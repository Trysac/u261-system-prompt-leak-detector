# Project record

## Objective

Detect system prompt leakage in LLM outputs: canary tokens, verbatim word n-gram overlap and base64-encoded copies, with a score, signals and an event hook that never sees the text.

## Scope

- In scope: `add_canary`, `LeakDetector` (`check`, `score`), `LeakReport`, `LeakError`, and the detection strategies implemented in `src/system_prompt_leak_detector/__init__.py`.
- In scope: NFKC and casefold tokenisation, prompt n-gram sets with `ignore`, optional canary matching, base64 span decoding, validation limits, and the metadata-only `on_event` callback.
- In scope: the public API documented in [README.md](../README.md), typed with `py.typed`, and tested.
- Out of scope: blocking or rewriting outputs, streaming, and input-side injection detection.
- Out of scope: LLM calls, network I/O and runtime dependencies.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 807746 / 53927 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0814 |

## Factory run u261 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1770 | 14922 | 0 | 3200 | 0.0308 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 8524 | 2079 | 0 | 55936 | 0.0027 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 5875 | 948 | 0 | 26752 | 0.0015 |
| 2026-11-10 | audit | deepseek-flash | no | 36915 | 21187 | 0 | 508288 | 0.0198 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 6565 | 2942 | 0 | 43008 | 0.0029 |
| 2026-11-10 | docs | deepseek-flash | no | 110657 | 11849 | 0 | 256 | 0.0237 |

Total: $0.0814. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
