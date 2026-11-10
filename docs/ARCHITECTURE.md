# Architecture

## Purpose

`trysac-system-prompt-leak-detector` is a small, dependency-free Python library: Detect system prompt leakage in LLM outputs: canary tokens, verbatim word n-gram overlap and base64-encoded copies, with a score, signals and an event hook that never sees the text

## Shape

```text
caller code --> system_prompt_leak_detector (public API in __init__.py)
                    |
                    +-- pure functions, no I/O, no global state
```

- **Public API**: the names listed in `__all__` of `src/system_prompt_leak_detector/__init__.py`. Anything else is
  internal and may change without a major version.
- **Errors**: invalid input raises built-in exceptions (`ValueError`, `TypeError`) with a clear
  message; the library never prints or exits.
- **Side effects**: none. If a feature needs I/O, isolate it in its own module behind a small
  interface and record the choice in an ADR.

## Quality contract

`scripts/check.py` is the single definition of the gates; `fabrica.json` tells the factory and CI
how to run it. See [TESTING.md](TESTING.md).

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
