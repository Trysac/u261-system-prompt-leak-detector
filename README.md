# system-prompt-leak-detector

[![PyPI version](https://img.shields.io/pypi/v/trysac-system-prompt-leak-detector)](https://pypi.org/project/trysac-system-prompt-leak-detector/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-system-prompt-leak-detector)](LICENSE)
[![CI](https://github.com/Trysac/u261-system-prompt-leak-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u261-system-prompt-leak-detector/actions/workflows/ci.yml)

Detect system prompt leakage in LLM outputs: canary tokens, verbatim word n-gram overlap and base64-encoded copies, with a score, signals and an event hook that never sees the text

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-system-prompt-leak-detector
# or
uv add trysac-system-prompt-leak-detector
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import system_prompt_leak_detector

# normalize() trims surrounding whitespace and lower-cases the text.
print(system_prompt_leak_detector.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    system_prompt_leak_detector.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
