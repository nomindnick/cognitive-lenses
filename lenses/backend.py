"""The model-call seam.

One protocol: complete(prompt, *, model, system, schema, label) -> Completion.
Two implementations:
  - ClaudeCLIBackend: each call is a fresh `claude -p` process. Fresh process =
    fresh context = structural independence between lenses/panelists, and it
    runs off a Claude subscription with no API key.
  - MockBackend: deterministic canned outputs so the whole pipeline can be
    exercised offline (`python3 -m lenses selftest`).

Every real call is appended to an audit log (one JSON file per call) with the
full prompt, response, usage, and cost.
"""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


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


class ClaudeCLIBackend:
    def __init__(self, log_dir: Path | None = None, max_parallel: int = 4,
                 timeout_s: int = 900, retries: int = 2):
        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        self._sem = threading.Semaphore(max_parallel)
        self._lock = threading.Lock()
        self._seq = 0
        self.timeout_s = timeout_s
        self.retries = retries

    def complete(self, prompt: str, *, model: str, system: str | None = None,
                 schema: dict | None = None, label: str = "call",
                 fallback_model: str | None = None,
                 timeout_s: int | None = None) -> Completion:
        last = None
        for attempt in range(self.retries + 1):
            try:
                return self._once(prompt, model=model, system=system, schema=schema,
                                  label=label, fallback_model=fallback_model,
                                  timeout_s=timeout_s or self.timeout_s, attempt=attempt)
            except BackendError as e:
                last = e
                time.sleep(min(45, 8 * (attempt + 1)))
        raise BackendError(f"{label}: failed after {self.retries + 1} attempts: {last}")

    def _once(self, prompt, *, model, system, schema, label, fallback_model,
              timeout_s, attempt) -> Completion:
        cmd = ["claude", "-p", "--model", model, "--output-format", "json",
               "--tools", "", "--no-session-persistence", "--strict-mcp-config",
               "--disable-slash-commands"]
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
        self._audit(comp, prompt, system, schema, attempt)
        return comp

    def _audit(self, comp: Completion, prompt, system, schema, attempt) -> None:
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
    return ClaudeCLIBackend(
        log_dir=log_dir,
        max_parallel=int(cfg.get("max_parallel_calls", 4)),
        timeout_s=int(cfg.get("call_timeout_s", 900)),
        retries=int(cfg.get("retries", 2)),
    )
