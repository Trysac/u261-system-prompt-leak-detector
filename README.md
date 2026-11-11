# system-prompt-leak-detector

[![PyPI version](https://img.shields.io/pypi/v/trysac-system-prompt-leak-detector)](https://pypi.org/project/trysac-system-prompt-leak-detector/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-system-prompt-leak-detector)](LICENSE)
[![CI](https://github.com/Trysac/u261-system-prompt-leak-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u261-system-prompt-leak-detector/actions/workflows/ci.yml)

Detect system prompt leakage in LLM outputs: canary tokens, verbatim word n-gram overlap and base64-encoded copies, with a score, signals and an event hook that never sees the text.

## Problem

Prompts that encode product logic, tone rules or tool instructions leak when users ask the model to repeat its instructions, often reformatted or base64 encoded. Teams find out from screenshots rather than from their own checks. This library compares each output with the protected prompt, recognises canary tokens and encoded copies, and returns a score and signals that a gateway can act on.

## Install

```sh
pip install trysac-system-prompt-leak-detector
# or
uv add trysac-system-prompt-leak-detector
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from system_prompt_leak_detector import LeakDetector

prompt = "You are Atlas, the support assistant of Example Corp. Never discuss pricing. Always answer in English and cite the help center."
detector = LeakDetector(prompt)
report = detector.check(
    "Sure! My instructions say: never discuss pricing, "
    "always answer in English and cite the help center."
)
print(report.leaked, report.score, report.signals)
# True 0.35714285714285715 ('verbatim',)
```

`LeakDetector` computes an n-gram overlap score, checks the optional canary, and scans base64 spans that decode to UTF-8. `on_event` receives only `event`, `leaked`, `score` and `signals`.

## Public API

- `CanaryPrompt(prompt: str, canary: str)` — frozen dataclass returned by `add_canary`.
- `add_canary(system_prompt: str, *, rng: Callable[[int], bytes] = secrets.token_bytes) -> CanaryPrompt` — appends `\n\n[canary: <canary>]`; the canary is `cnry-` plus `rng(8).hex()`.
- `LeakDetector(system_prompt: str, *, canary: str | None = None, ngram: int = 8, threshold: float = 0.2, ignore: Sequence[str] = (), max_output_chars: int = 200_000, on_event: Callable[[dict[str, object]], None] | None = None)` — validates input and builds the prompt n-gram set.
- `LeakDetector.check(output: str) -> LeakReport` — returns `leaked`, `score` and sorted `signals` from `canary`, `encoded` and `verbatim`.
- `LeakDetector.score(text: str) -> float` — `|found prompt n-grams| / |prompt n-grams|`, or `0.0` when the set is empty.
- `LeakReport(leaked: bool, score: float, signals: tuple[str, ...])` — frozen dataclass.
- `LeakError` — has `.code` set to `input_too_large`, `invalid_options` or `prompt_too_short`.

Limits and options: the prompt must have at least 3 words and at most 50,000 characters; `ngram` must be 3..20 (the effective size is the smaller of `ngram` and the prompt word count); `threshold` must be in `(0, 1]`; `max_output_chars` defaults to 200,000 and larger outputs raise `LeakError` with code `input_too_large`. Base64 scanning considers at most 20 spans of at most 65,536 characters with a length divisible by 4. `ignore` texts remove their n-grams from the prompt n-gram set. The callback never receives prompt or output text.

## Why not generic output moderation rules

Generic output moderation matches fixed patterns. This utility measures overlap with the actual protected prompt, so the same code protects different prompts without maintaining a rule list.

## Documentation

- [Architecture](docs/ARCHITECTURE.md), [testing](docs/TESTING.md), [security](docs/SECURITY.md), [project record](docs/PROJECT.md), [stack](docs/STACK.md)
- [Security policy](docs/SECURITY.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
