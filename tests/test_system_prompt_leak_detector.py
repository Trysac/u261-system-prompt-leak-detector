import base64
import re

import pytest

from system_prompt_leak_detector import (
    CanaryPrompt,
    LeakDetector,
    LeakError,
    LeakReport,
    add_canary,
)

PROMPT = (
    "You are Atlas, the support assistant of Example Corp. Never discuss pricing. "
    "Always answer in English and cite the help center."
)
OUTPUT_LEAK = "Sure! My instructions say: never discuss pricing, always answer in English and cite the help center."
OUTPUT_UPPER = OUTPUT_LEAK.upper()
OUTPUT_NO_LEAK = "Our help center is open. Always answer in English, please."
BASE64_LEAK = "Here: bmV2ZXIgZGlzY3VzcyBwcmljaW5nLiBBbHdheXMgYW5zd2VyIGluIEVuZ2xpc2ggYW5kIGNpdGUgdGhlIGhlbHAgY2VudGVy"
CANARY = "cnry-0001020304050607"


def test_add_canary_equality() -> None:
    result = add_canary("Be brief.", rng=lambda n: bytes(range(n)))
    expected = CanaryPrompt(
        prompt="Be brief.\n\n[canary: cnry-0001020304050607]",
        canary="cnry-0001020304050607",
    )
    assert result == expected


def test_verbatim_leak_score_and_signal() -> None:
    detector = LeakDetector(PROMPT)
    report = detector.check(OUTPUT_LEAK)
    assert report == LeakReport(
        leaked=True,
        score=5 / 14,
        signals=("verbatim",),
    )


def test_no_leak_and_uppercase_leak() -> None:
    detector = LeakDetector(PROMPT)
    assert detector.check(OUTPUT_NO_LEAK) == LeakReport(leaked=False, score=0.0, signals=())
    report_upper = detector.check(OUTPUT_UPPER)
    assert report_upper.score == 5 / 14
    assert report_upper.signals == ("verbatim",)
    assert report_upper.leaked is True


def test_canary_signal_without_ngram_match() -> None:
    detector = LeakDetector(PROMPT, canary=CANARY)
    report = detector.check("ref CNRY-0001020304050607")
    assert report.leaked is True
    assert report.signals == ("canary",)
    assert report.score == 0.0


def test_base64_encoded_leak() -> None:
    detector = LeakDetector(PROMPT)
    report = detector.check(BASE64_LEAK)
    assert report.leaked is True
    assert report.score == 5 / 14
    assert report.signals == ("encoded",)


def test_ignore_removes_ngrams_and_lowers_score() -> None:
    ignore = ["Always answer in English and cite the help center."]
    detector = LeakDetector(PROMPT, ignore=ignore)
    report = detector.check(OUTPUT_LEAK)
    assert report.score == pytest.approx(3 / 12)
    assert report.leaked is True
    assert report.signals == ("verbatim",)


def test_output_too_large_raises_input_too_large() -> None:
    detector = LeakDetector(PROMPT)
    with pytest.raises(LeakError) as exc_info:
        detector.check("a" * 200_001)
    assert exc_info.value.code == "input_too_large"
    # Exactly max_output_chars is allowed.
    detector.check("a" * 200_000)


def test_invalid_options_raise() -> None:
    with pytest.raises(LeakError) as exc_info:
        LeakDetector(PROMPT, ngram=2)
    assert exc_info.value.code == "invalid_options"
    with pytest.raises(LeakError) as exc_info:
        LeakDetector(PROMPT, threshold=0)
    assert exc_info.value.code == "invalid_options"
    with pytest.raises(LeakError) as exc_info:
        LeakDetector(PROMPT, max_output_chars=0)
    assert exc_info.value.code == "invalid_options"


def test_prompt_too_short_raises() -> None:
    with pytest.raises(LeakError) as exc_info:
        LeakDetector("Hello world.")
    assert exc_info.value.code == "prompt_too_short"


def test_on_event_receives_metadata_only() -> None:
    events: list[dict[str, object]] = []
    detector = LeakDetector(PROMPT, on_event=events.append)
    detector.check(OUTPUT_LEAK)
    assert len(events) == 1
    payload = events[0]
    assert set(payload.keys()) == {"event", "leaked", "score", "signals"}
    assert payload["event"] == "check"
    assert payload["leaked"] is True
    assert payload["score"] == 5 / 14
    assert payload["signals"] == ["verbatim"]


def test_no_sensitive_data_in_payload_repr_or_error() -> None:
    prompt = "Secret alpha beta gamma delta epsilon zeta eta theta"
    output = "Secret alpha beta gamma delta epsilon zeta eta theta"
    events: list[dict[str, object]] = []
    detector = LeakDetector(prompt, on_event=events.append)
    report = detector.check(output)
    payload = events[0]
    sensitive_words = set(
        re.findall(r"\w+", prompt.casefold()) + re.findall(r"\w+", output.casefold())
    )
    for word in sensitive_words:
        assert word not in str(payload)
        assert word not in repr(report)
    with pytest.raises(LeakError) as exc_info:
        LeakDetector(prompt, ngram=2)
    assert exc_info.value.code == "invalid_options"
    # Ensure error message does not contain prompt words.
    for word in sensitive_words:
        assert word not in str(exc_info.value)


def test_prompt_exactly_three_words() -> None:
    prompt = "Alpha beta gamma"
    detector = LeakDetector(prompt)
    report = detector.check("Alpha beta gamma")
    assert report.leaked is True
    assert report.score == 1.0
    assert report.signals == ("verbatim",)


def test_ignore_covers_whole_prompt_canary_still_works() -> None:
    detector = LeakDetector(PROMPT, canary=CANARY, ignore=[PROMPT])
    report = detector.check(CANARY)
    assert report.leaked is True
    assert report.score == 0.0
    assert report.signals == ("canary",)


def test_invalid_base64_padding_is_skipped() -> None:
    detector = LeakDetector(PROMPT)
    # 25 'A' characters: length not multiple of 4, ignored by the detector.
    output = "A" * 25
    report = detector.check(output)
    assert "encoded" not in report.signals


def test_base64_span_decoding_to_binary_is_skipped() -> None:
    detector = LeakDetector(PROMPT)
    binary_bytes = b"\xff\xfe\x00" * 10  # invalid UTF-8
    encoded = base64.b64encode(binary_bytes).decode("ascii")
    report = detector.check(encoded)
    assert "encoded" not in report.signals


def test_empty_or_whitespace_canary_is_rejected() -> None:
    for bad_canary in ("", "   ", "\t\n"):
        with pytest.raises(LeakError) as exc_info:
            LeakDetector(PROMPT, canary=bad_canary)
        assert exc_info.value.code == "invalid_options"


def test_canary_detection_with_adjacent_characters() -> None:
    detector = LeakDetector(PROMPT, canary=CANARY)
    report = detector.check(f"xx{CANARY}123")
    assert "canary" in report.signals
