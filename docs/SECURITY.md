# Security

This document describes the threat model for the `system_prompt_leak_detector` library.

## Threat Model

The library compares LLM outputs against a protected system prompt to detect leakage. It does **not** modify, block, or rewrite outputs and does not detect input-side injection attacks. It performs no network I/O and makes no LLM calls.

### Defended Against

- **Verbatim copies** of the system prompt.
- **Case and punctuation changes** via NFKC normalization and casefold; tokenisation uses `re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold())`.
- **Echoes of the canary token** case-insensitively.
- **Base64-encoded copies** of the prompt or canary: spans matching `[A-Za-z0-9+/]{24,}={0,2}` with length divisible by 4, at most 20 spans of at most 65,536 characters, that decode to valid UTF-8 and meet the threshold or contain the canary.

### Not Defended Against

- **Paraphrases or translations** of the prompt.
- **Leaks shorter than `ngram` words**.
- **Leaks split across several responses**.
- **Other encodings** such as hex or rot13.
- **A model that reveals the canary token** while dropping the surrounding `[canary: ...]` context.

### Limits

- System prompt: at most 50,000 characters and at least 3 words.
- Output: at most `max_output_chars` (default 200,000); larger outputs raise `LeakError` with code `input_too_large`.
- `ngram`: 3..20; the effective size is `min(ngram, prompt word count)`.
- `threshold`: in `(0, 1]`.
- `on_event` receives only `event`, `leaked`, `score` and `signals` and never the prompt or output text.

### Out of Scope

- Blocking or rewriting outputs.
- Streaming responses.
- Input-side injection detection.

## Reporting a Vulnerability

If you discover a security issue, please report it responsibly. Do not open a public issue. Contact the maintainers privately with details.
