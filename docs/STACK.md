# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | Uses `str | None`, built-in generic types and `from __future__ import annotations`. |
| Standard library only | Imports `base64`, `binascii`, `logging`, `re`, `secrets`, `unicodedata`, `dataclasses`, `collections.abc` and `typing`; no runtime dependencies. |
| pytest | Test runner for `tests/test_system_prompt_leak_detector.py`. |
| `py.typed` | Marks the package as typed for type checkers. |

## Discarded

| Tool | Why not |
|---|---|
| Third-party runtime libraries | The detector uses only the standard library. |
| LLM provider SDKs | The utility performs no LLM calls. |
| Network or I/O frameworks | The detector is a pure in-process check. |
| Non-base64 encodings | Hex, rot13 and similar encodings are outside the implementation. |
