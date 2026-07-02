# Ollama candidate benchmark

Probes use the real q1 Delphi round-1 panelist prompt (entry point #1). `retries=0` for generation: failures are first-attempt failures, not exhausted retries. Cold load is measured by a warmup call that tolerates Ollama's 5-minute server load timeout (disk speed, not model quality); decode/prompt tok/s come from Ollama's own eval counters with the model resident. Schema probe is grammar-constrained (`format=PANELIST_SCHEMA`) and then gated by the lens's `_sane()`.

| model | size | cold load s | prompt tok/s | decode tok/s | schema out toks | schema wall s | valid | sane | prob | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-oss:120b | 65 GB | 2190.7 | — | — | — | — | — | — | — | FAILED: did not load within 3 server load-timeout windows |
| qwen3.5:122b | 81 GB | 25.7 | 271.6 | 22.8 | 467 | 181.3 | ✓ | ✓ | 82 | speed capped (expected); thought 15,644 chars |
| mistral-medium-3.5:128b | 80 GB | 1341.6 | — | — | — | — | — | — | — | FAILED: did not load within 3 server load-timeout windows |
| gemma4:31b | 19 GB | 9.2 | 303.4 | 9.4 | — | — | — | — | — | speed capped (expected); schema probe FAILED: bench-gemma4:31b-schema: failed after 1 attempts: bench-gemma4:31b-schema: structured output not parseable (done_reason='stop'): '{\n  "probability": 75,\n  "confidence": "high",\n  "position_summary": "The use of a shared-memory AI is more likely than not to bectors as a \'communication\' via an in |
| qwen3.6:27b | 17 GB | 8.3 | 237.9 | 11.8 | 309 | 348.3 | ✓ | ✓ | 75 | speed capped (expected); thought 16,186 chars |
| gemma4:12b | 7.6 GB | 6.4 | 781.2 | 21.9 | 408 | 82.2 | ✓ | ✓ | 90 | speed capped (expected); thought 5,793 chars |

Feasibility yardstick: a full-protocol question burned ~450k output tokens on the Claude runs. tok/s above sets the overnight-run math; `sane ✗` or a schema failure disqualifies a model as a Delphi panelist regardless of speed.

## Verdict (2026-07-02, Ollama 0.30.7, ROCm on Ryzen AI Max+ 395 / 126GB)

- **qwen3.5:122b is the local engine.** Only big model that serves; 22.8 tok/s
  decode ≈ 5.5 h per full-protocol question — overnight-viable. Passed schema +
  sanity with real authorities cited.
- **gpt-oss:120b and mistral-medium-3.5:128b cannot currently serve on this
  box**: tensors reach VRAM quickly, but llama-server startup (ROCm kernel
  compile for their quant formats, apparently) exceeds the server's 5-minute
  load window on every attempt — 3 windows each, while qwen3.5:122b (a *bigger*
  file) loaded in 25.7 s. Remedy to try later: `OLLAMA_LOAD_TIMEOUT=30m` in the
  ollama systemd unit; if the compile result is cached the cost may be one-time.
- **gemma4:31b is out**: 9.4 tok/s AND a first-attempt schema failure with
  visible token corruption ("to bectors as a") under grammar constraint. Slow
  and unreliable is the losing combination.
- **qwen3.6:27b technically qualifies** (valid, sane) but cited ZERO authorities
  and needed 348 s per panelist answer — thin substance at dense-model speed.
- **gemma4:12b is the surprise**: 21.9 tok/s (matches the 122B MoE), passed
  cleanly, cited 2 authorities. Cheapest credible panelist; candidate for the
  below-Haiku-floor probe.
- **Early overconfidence signal**: local panelist probabilities on q1 ran
  82 / 75 / 90 where the Claude panels clustered 62–68. One sample each, but
  worth watching in the real runs — if local panels systematically run hot,
  the Delphi spread statistics mean something different.
- Bookkeeping note: on thinking models, the schema probe's `input_tokens`
  (~4.5k vs a ~900-token prompt) includes the thinking pass re-fed through the
  grammar-constrained decode; that inflation will recur in real runs.

Next: config C (`config/ollama-hybrid.json`, qwen3.5:122b workers + Fable
judge) on q1, judged blind by the round-1–3 harness; then config D
(`config/ollama-local.json`, all-qwen3.5:122b) on the same question.
