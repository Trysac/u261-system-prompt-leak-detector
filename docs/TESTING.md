# Testing

## Running

```sh
pytest
pytest tests/test_system_prompt_leak_detector.py
```

The tests import the public package: `from system_prompt_leak_detector import CanaryPrompt, LeakDetector, LeakError, LeakReport, add_canary`.

## Policy

- Tests exercise the public API and assert exact `LeakReport` values, signal tuples, error codes and callback payloads.
- The test file uses fixed strings and a deterministic `rng` (`lambda n: bytes(range(n))`) where canary output is asserted.
- No network access, wall-clock dependence or test-order dependence is used in the test file.

## Tiers

All tests are in `tests/test_system_prompt_leak_detector.py`. There are no conformance-marked tests in the provided source tree.

## Layout

`tests/test_system_prompt_leak_detector.py` covers:

- `test_add_canary_equality` — exact `CanaryPrompt` from `add_canary`.
- `test_verbatim_leak_score_and_signal` — verbatim leak score `5 / 14` and signal `verbatim`.
- `test_no_leak_and_uppercase_leak` — no-leak output and uppercase leak score.
- `test_canary_signal_without_ngram_match` — canary signal with case-insensitive match.
- `test_base64_encoded_leak` — base64 leak with signal `encoded`.
- `test_ignore_removes_ngrams_and_lowers_score` — ignored n-grams and lowered score.
- `test_output_too_large_raises_input_too_large` — `LeakError.code == input_too_large`.
- `test_invalid_options_raise` — invalid `ngram`, `threshold` and `max_output_chars`.
- `test_prompt_too_short_raises` — `LeakError.code == prompt_too_short`.
- `test_on_event_receives_metadata_only` — callback payload keys.
- `test_no_sensitive_data_in_payload_repr_or_error` — no prompt/output words in payload, `repr` or error.
- `test_prompt_exactly_three_words` — prompt with exactly three words is accepted.
- `test_ignore_covers_whole_prompt_canary_still_works` — score `0.0`, canary still detected.
- `test_invalid_base64_padding_is_skipped` — invalid base64 span does not produce `encoded`.
- `test_base64_span_decoding_to_binary_is_skipped` — non-UTF-8 decoded span is skipped.
- `test_empty_or_whitespace_canary_is_rejected` — empty or whitespace canary raises `invalid_options`.
- `test_canary_detection_with_adjacent_characters` — canary found next to adjacent characters.
