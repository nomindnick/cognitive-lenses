"""The model-call seam.

One protocol: complete(prompt, *, model, system, schema, label) -> Completion.
Implementations:
  - ClaudeCLIBackend: each call is a fresh `claude -p` process. Fresh process =
    fresh context = structural independence between lenses/panelists, and it
    runs off a Claude subscription with no API key.
  - OllamaBackend: local models via the Ollama HTTP API. Stateless calls give
    the same structural independence; `format` does grammar-constrained JSON at
    decode time (stronger schema enforcement than prompting, though the Delphi
    sanity gate still catches semantically degenerate output). No web tools —
    calls that need search (cite-check) must route to a Claude model.
  - MockBackend: deterministic canned outputs so the whole pipeline can be
    exercised offline (`python3 -m lenses selftest`).

Model strings route per call: "ollama:<tag>" goes to Ollama, anything else to
the Claude CLI, so one config can mix local workers with Claude judges. When a
call fails and its fallback_model routes to a different backend, the router
retries there (a local judge can fall back to Claude).

Every real call is appended to an audit log (one JSON file per call) with the
full prompt, response, usage, and cost; both backends share one sequence so a
mixed run interleaves into a single calls/ dir.
"""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

OLLAMA_PREFIX = "ollama:"


class BackendError(RuntimeError):
    pass


@dataclass
class Completion:
    text: str
    model: str
    label: str
    duration_s: float = 0.0
    cost_usd: float = 0.0
    usage: dict = field(default_factory=dict)
    data: object = None  # parsed structured output when a schema was supplied
    raw: dict = field(default_factory=dict)


def _extract_structured(raw: dict, text: str):
    so = raw.get("structured_output")
    if isinstance(so, (dict, list)):
        return so
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except (json.JSONDecodeError, ValueError):
        pass
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


class AuditLog:
    """One JSON file per call. Shared across backends so a mixed run gets one
    collision-free sequence in its calls/ dir."""

    def __init__(self, log_dir: Path | None):
        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq = 0

    def record(self, comp: Completion, prompt, system, schema, attempt) -> None:
        if not self.log_dir:
            return
        with self._lock:
            self._seq += 1
            seq = self._seq
        safe = re.sub(r"[^\w.-]+", "_", comp.label)[:80]
        rec = {
            "seq": seq, "label": comp.label, "model": comp.model, "attempt": attempt,
            "duration_s": comp.duration_s, "cost_usd": comp.cost_usd, "usage": comp.usage,
            "system": system, "prompt": prompt, "schema": schema,
            "text": comp.text, "data": comp.data,
        }
        path = self.log_dir / f"{seq:04d}-{safe}.json"
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")


class ClaudeCLIBackend:
    def __init__(self, audit: AuditLog | None = None, max_parallel: int = 4,
                 timeout_s: int = 900, retries: int = 2):
        self.audit = audit or AuditLog(None)
        self._sem = threading.Semaphore(max_parallel)
        self.timeout_s = timeout_s
        self.retries = retries

    def complete(self, prompt: str, *, model: str, system: str | None = None,
                 schema: dict | None = None, label: str = "call",
                 fallback_model: str | None = None,
                 timeout_s: int | None = None, tools: str | None = None) -> Completion:
        last = None
        for attempt in range(self.retries + 1):
            try:
                return self._once(prompt, model=model, system=system, schema=schema,
                                  label=label, fallback_model=fallback_model,
                                  timeout_s=timeout_s or self.timeout_s, attempt=attempt,
                                  tools=tools)
            except BackendError as e:
                last = e
                time.sleep(min(45, 8 * (attempt + 1)))
        raise BackendError(f"{label}: failed after {self.retries + 1} attempts: {last}")

    def _once(self, prompt, *, model, system, schema, label, fallback_model,
              timeout_s, attempt, tools=None) -> Completion:
        cmd = ["claude", "-p", "--model", model, "--output-format", "json",
               "--tools", tools or "", "--no-session-persistence",
               "--strict-mcp-config", "--disable-slash-commands"]
        if tools:
            cmd += ["--allowedTools", tools]
        if system:
            cmd += ["--system-prompt", system]
        if schema:
            cmd += ["--json-schema", json.dumps(schema)]
        if fallback_model:
            cmd += ["--fallback-model", fallback_model]
        t0 = time.time()
        with self._sem:
            try:
                proc = subprocess.run(cmd, input=prompt, text=True,
                                      capture_output=True, timeout=timeout_s)
            except subprocess.TimeoutExpired:
                raise BackendError(f"{label}: timed out after {timeout_s}s")
        dt = time.time() - t0
        if proc.returncode != 0:
            raise BackendError(
                f"{label}: claude exited {proc.returncode}: {(proc.stderr or proc.stdout)[-2000:]}")
        try:
            raw = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise BackendError(f"{label}: non-JSON stdout: {proc.stdout[:400]!r}")
        if raw.get("is_error"):
            raise BackendError(f"{label}: API error: {str(raw.get('result'))[:400]}")
        text = raw.get("result") or ""
        data = _extract_structured(raw, text) if schema else None
        if schema and data is None:
            raise BackendError(f"{label}: structured output not parseable: {text[:300]!r}")
        comp = Completion(text=text, model=model, label=label, duration_s=round(dt, 1),
                          cost_usd=float(raw.get("total_cost_usd") or 0.0),
                          usage=raw.get("usage") or {}, data=data, raw=raw)
        self.audit.record(comp, prompt, system, schema, attempt)
        return comp


class OllamaBackend:
    """Local models over the Ollama HTTP API (stateless /api/chat calls).

    num_ctx is set explicitly on every request and prompts are size-checked
    first: Ollama otherwise truncates over-long prompts SILENTLY, which would
    poison the experiment (a lens that never saw half the facts still returns
    a confident answer). Usage carries measured prompt/decode tok/s so runs
    double as throughput data.
    """

    def __init__(self, audit: AuditLog | None = None, host: str = "http://localhost:11434",
                 max_parallel: int = 2, timeout_s: int = 3600, retries: int = 2,
                 num_ctx: int = 32768, options: dict | None = None,
                 think: object = None, keep_alive: object = None):
        self.audit = audit or AuditLog(None)
        self.host = host.rstrip("/")
        self._sem = threading.Semaphore(max_parallel)
        self.timeout_s = timeout_s
        self.retries = retries
        self.num_ctx = num_ctx
        self.options = options or {}
        self.think = think
        self.keep_alive = keep_alive

    def complete(self, prompt: str, *, model: str, system: str | None = None,
                 schema: dict | None = None, label: str = "call",
                 fallback_model: str | None = None,
                 timeout_s: int | None = None, tools: str | None = None) -> Completion:
        del fallback_model  # cross-backend fallback is the router's job
        if tools:
            raise BackendError(
                f"{label}: ollama backend has no web tools (needed: {tools}); "
                "set verify_model to a Claude model for search-enabled stages")
        # ~3.6 chars/token is conservative for legal English; 4k headroom for output.
        est_tokens = (len(prompt) + len(system or "")) / 3.6
        if est_tokens + 4096 > self.num_ctx:
            raise BackendError(
                f"{label}: prompt ≈{est_tokens:,.0f} tokens won't fit num_ctx="
                f"{self.num_ctx} (Ollama would truncate silently) — raise ollama_num_ctx")
        last = None
        for attempt in range(self.retries + 1):
            try:
                return self._once(prompt, model=model, system=system, schema=schema,
                                  label=label, timeout_s=timeout_s or self.timeout_s,
                                  attempt=attempt)
            except BackendError as e:
                last = e
                time.sleep(min(20, 4 * (attempt + 1)))
        raise BackendError(f"{label}: failed after {self.retries + 1} attempts: {last}")

    def _once(self, prompt, *, model, system, schema, label, timeout_s, attempt) -> Completion:
        messages = ([{"role": "system", "content": system}] if system else []) \
            + [{"role": "user", "content": prompt}]
        body = {"model": model, "messages": messages, "stream": False,
                "options": {"num_ctx": self.num_ctx, **self.options}}
        if schema:
            body["format"] = schema
        if self.think is not None:
            body["think"] = self.think
        if self.keep_alive is not None:
            body["keep_alive"] = self.keep_alive
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        t0 = time.time()
        with self._sem:
            try:
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:400]
                raise BackendError(f"{label}: ollama HTTP {e.code}: {detail}")
            except urllib.error.URLError as e:
                if isinstance(getattr(e, "reason", None), TimeoutError):
                    raise BackendError(f"{label}: ollama timed out after {timeout_s}s")
                raise BackendError(
                    f"{label}: cannot reach ollama at {self.host} ({e.reason}) — "
                    "is `ollama serve` running?")
            except TimeoutError:
                raise BackendError(f"{label}: ollama timed out after {timeout_s}s")
        dt = time.time() - t0
        msg = raw.get("message") or {}
        text = msg.get("content") or ""
        data = _extract_structured({}, text) if schema else None
        if schema and data is None:
            raise BackendError(
                f"{label}: structured output not parseable "
                f"(done_reason={raw.get('done_reason')!r}): {text[:300]!r}")
        p_n, p_ns = raw.get("prompt_eval_count", 0), raw.get("prompt_eval_duration", 0)
        e_n, e_ns = raw.get("eval_count", 0), raw.get("eval_duration", 0)
        usage = {
            "input_tokens": p_n, "output_tokens": e_n,
            "prompt_tps": round(p_n / (p_ns / 1e9), 1) if p_ns else None,
            "decode_tps": round(e_n / (e_ns / 1e9), 1) if e_ns else None,
            "load_s": round(raw.get("load_duration", 0) / 1e9, 1),
            "thinking_chars": len(msg.get("thinking") or ""),
            "done_reason": raw.get("done_reason"),
        }
        comp = Completion(text=text, model=model, label=label, duration_s=round(dt, 1),
                          cost_usd=0.0, usage=usage, data=data, raw=raw)
        self.audit.record(comp, prompt, system, schema, attempt)
        return comp


class RoutingBackend:
    """Dispatch per call on the model string: "ollama:<tag>" -> OllamaBackend,
    anything else -> ClaudeCLIBackend. Claude-to-Claude fallback stays inside
    the CLI (--fallback-model handles transient overload best there); any
    fallback that crosses backends — or falls back within Ollama — is retried
    here after the primary exhausts its own retries."""

    def __init__(self, claude: ClaudeCLIBackend, ollama: OllamaBackend):
        self.claude = claude
        self.ollama = ollama

    def _route(self, model: str):
        if model.startswith(OLLAMA_PREFIX):
            return self.ollama, model[len(OLLAMA_PREFIX):]
        return self.claude, model

    def complete(self, prompt: str, *, model: str, fallback_model: str | None = None,
                 **kw) -> Completion:
        be, m = self._route(model)
        fb_be, fb_m = self._route(fallback_model) if fallback_model else (None, None)
        inner_fb = fb_m if (fb_be is be is self.claude) else None
        try:
            return be.complete(prompt, model=m, fallback_model=inner_fb, **kw)
        except BackendError:
            if fb_be is None or inner_fb:
                raise  # no fallback, or the CLI already tried it
            print(f"[backend] {kw.get('label', 'call')}: {m} failed, "
                  f"falling back to {fb_m}", flush=True)
            return fb_be.complete(prompt, model=fb_m, fallback_model=None, **kw)


def _mock_instance(schema: dict, seed: str = ""):
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if t == "object":
        return {k: _mock_instance(v, seed) for k, v in (schema.get("properties") or {}).items()}
    if t == "array":
        n = max(1, int(schema.get("minItems", 2)))
        return [_mock_instance(schema.get("items", {"type": "string"}), f"{seed}.{i}")
                for i in range(n)]
    if t in ("number", "integer"):
        return 55
    if t == "boolean":
        return False
    return (f"mock-{seed or 'text'}: plausible synthetic content standing in for a real "
            "model answer so the offline pipeline (including sanity gates) can be exercised.")


class MockBackend:
    """Offline stand-in: valid-shaped outputs, zero tokens."""

    def __init__(self, **_kw):
        self.log_dir = None

    def complete(self, prompt: str, *, model: str, system: str | None = None,
                 schema: dict | None = None, label: str = "call", **_kw) -> Completion:
        if schema:
            data = _mock_instance(schema, label)
            return Completion(text=json.dumps(data), model="mock", label=label, data=data)
        text = (
            f"### mock output ({label})\n\n"
            "A mock analysis citing Gov. Code § 54952.2(b)(1) and "
            "*Wolfe v. City of Fremont* (2006) 144 Cal.App.4th 533, plus Prop 218 "
            "and FPPC Advice Letter No. A-15-071 for citation-extractor exercise.\n"
        )
        return Completion(text=text, model="mock", label=label)


def make_backend(cfg: dict, log_dir: Path | None, mock: bool = False):
    if mock:
        return MockBackend()
    audit = AuditLog(log_dir)
    claude = ClaudeCLIBackend(
        audit=audit,
        max_parallel=int(cfg.get("max_parallel_calls", 4)),
        timeout_s=int(cfg.get("call_timeout_s", 900)),
        retries=int(cfg.get("retries", 2)),
    )
    ollama = OllamaBackend(
        audit=audit,
        host=cfg.get("ollama_host", "http://localhost:11434"),
        max_parallel=int(cfg.get("ollama_max_parallel", 2)),
        timeout_s=int(cfg.get("ollama_timeout_s", 3600)),
        retries=int(cfg.get("retries", 2)),
        num_ctx=int(cfg.get("ollama_num_ctx", 32768)),
        options=cfg.get("ollama_options"),
        think=cfg.get("ollama_think"),
        keep_alive=cfg.get("ollama_keep_alive"),
    )
    return RoutingBackend(claude, ollama)
