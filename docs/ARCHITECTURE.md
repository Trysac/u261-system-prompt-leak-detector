# Architecture

## Purpose

`trysac-system-prompt-leak-detector` is a small, dependency-free Python library that detects system prompt leakage in LLM outputs.

## Shape

```text
caller code --> system_prompt_leak_detector (public API in __init__.py)
                    |
                    +-- stdlib-only detection: NFKC tokenisation, n-gram sets, base64 scan
```

- **Public API**: `CanaryPrompt`, `add_canary`, `LeakDetector`, `LeakReport`, `LeakError` from `src/system_prompt_leak_detector/__init__.py`.
- **Errors**: invalid input or options raise `LeakError` with `.code` set to `input_too_large`, `invalid_options` or `prompt_too_short`.
- **Side effects**: no network or file I/O. The module attaches a `NullHandler` to its logger; the optional `on_event` callback receives only `event`, `leaked`, `score` and `signals`.
- **State**: `LeakDetector` stores the prompt n-gram set, optional canary, threshold, ignore texts and output limit; there is no global mutable state.

## Quality contract

The package ships `py.typed`. Tests in `tests/test_system_prompt_leak_detector.py` assert exact reports, signals and error codes; see [TESTING.md](TESTING.md).

## Decisions

No separate architecture decision records are present in the provided source snapshot. The public API and limits above are the implemented decisions.
