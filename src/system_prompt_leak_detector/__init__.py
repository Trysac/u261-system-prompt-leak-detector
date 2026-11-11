"""Detect system prompt leakage in LLM outputs.

This module compares LLM outputs against a protected system prompt using three
detection strategies:

* **Canary token** - a unique string appended to the prompt and searched for
  case-insensitively.
* **Verbatim n-gram overlap** - word n-grams from the prompt that appear in the
  output, normalized with NFKC and casefold.
* **Encoded copies** - base64 spans that decode to valid UTF-8 whose score meets
  the threshold or which contain the canary.

The detector returns a :class:`LeakReport` with a score, a set of signals, and a
boolean ``leaked`` flag. An optional ``on_event`` callback receives only the
report metadata (event, leaked, score, signals) and never the prompt or output
text, preventing accidental logging of sensitive content.

Threat model
------------

**Defended against**

* Verbatim copies of the system prompt.
* Case and punctuation changes (via NFKC normalization and casefold).
* Echoes of the canary token.
* Base64-encoded copies of the prompt or canary.

**Not defended against**

* Paraphrases or translations of the prompt.
* Leaks shorter than ``ngram`` words.
* Leaks split across several responses.
* Other encodings (hex, rot13, etc.).
* A model that reveals the canary token itself while dropping its surrounding
  ``[canary: ...]`` context.

Out of scope: blocking or rewriting outputs, streaming, and input-side injection
detection.
"""

from __future__ import annotations

import base64
import binascii
import logging
import re
import secrets
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "CanaryPrompt",
    "LeakDetector",
    "LeakError",
    "LeakReport",
    "add_canary",
]

__version__ = "0.1.0"

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

LeakErrorCode = Literal["input_too_large", "invalid_options", "prompt_too_short"]


@dataclass(frozen=True)
class CanaryPrompt:
    """A system prompt with an embedded canary token."""

    prompt: str
    canary: str


def add_canary(
    system_prompt: str,
    *,
    rng: Callable[[int], bytes] = secrets.token_bytes,
) -> CanaryPrompt:
    """Append a canary token to *system_prompt* and return the result.

    The canary is generated as ``"cnry-" + rng(8).hex()`` and appended as
    ``\\n\\n[canary: <canary>]``.

    Args:
        system_prompt: The original system prompt.
        rng: A callable that returns ``n`` random bytes. Defaults to
            :func:`secrets.token_bytes`.

    Returns:
        A :class:`CanaryPrompt` containing the modified prompt and the canary.
    """
    canary = "cnry-" + rng(8).hex()
    prompt = system_prompt + "\n\n[canary: " + canary + "]"
    return CanaryPrompt(prompt=prompt, canary=canary)


@dataclass(frozen=True)
class LeakReport:
    """Result of a leak check."""

    leaked: bool
    score: float
    signals: tuple[str, ...]


class LeakError(Exception):
    """Raised when invalid input or options are provided."""

    def __init__(self, code: LeakErrorCode) -> None:
        self.code = code
        super().__init__(code)


def _tokenize(text: str) -> list[str]:
    """Normalize *text* (NFKC + casefold) and return word tokens."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"\w+", normalized)


_BASE64_RE = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


class LeakDetector:
    """Detect leakage of a protected system prompt in LLM outputs.

    Args:
        system_prompt: The prompt to protect. Must have at least 3 words and at
            most 50,000 characters.
        canary: Optional canary token to search for. If provided, its presence
            in the output (case-insensitively) raises the ``canary`` signal.
        ngram: Size of the word n-grams to compare. Must be 3..20.
        threshold: Score threshold for the ``verbatim`` signal. Must be in
            ``(0, 1]``.
        ignore: Texts whose n-grams are removed from the prompt n-gram set.
        max_output_chars: Maximum allowed output length. Larger outputs raise
            :class:`LeakError` with code ``"input_too_large"``.
        on_event: Optional callback receiving a dict with keys ``"event"``,
            ``"leaked"``, ``"score"``, ``"signals"``. Never receives prompt or
            output text.

    Raises:
        LeakError: If validation fails.
    """

    def __init__(
        self,
        system_prompt: str,
        *,
        canary: str | None = None,
        ngram: int = 8,
        threshold: float = 0.2,
        ignore: Sequence[str] = (),
        max_output_chars: int = 200_000,
        on_event: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        if not isinstance(system_prompt, str):
            raise LeakError("invalid_options")
        if len(system_prompt) > 50_000:
            raise LeakError("input_too_large")
        if canary is not None and (not isinstance(canary, str) or not canary.strip()):
            raise LeakError("invalid_options")
        words = _tokenize(system_prompt)
        if len(words) < 3:
            raise LeakError("prompt_too_short")
        if not 3 <= ngram <= 20:
            raise LeakError("invalid_options")
        if not 0.0 < threshold <= 1.0:
            raise LeakError("invalid_options")
        if max_output_chars <= 0:
            raise LeakError("invalid_options")

        self._system_prompt = system_prompt
        self._canary = None if canary is None else canary.strip().casefold()
        self._threshold = threshold
        self._ignore = tuple(ignore)
        self._max_output_chars = max_output_chars
        self._on_event = on_event
        self._effective_ngram = min(ngram, len(words))
        self._prompt_grams = self._build_prompt_grams(words, self._effective_ngram)

    def _build_prompt_grams(self, prompt_words: list[str], n: int) -> set[tuple[str, ...]]:
        """Build the set of prompt n-grams, minus n-grams from ignore texts."""
        grams: set[tuple[str, ...]] = set()
        for i in range(len(prompt_words) - n + 1):
            grams.add(tuple(prompt_words[i : i + n]))
        for ignore_text in self._ignore:
            ignore_words = _tokenize(ignore_text)
            for i in range(len(ignore_words) - n + 1):
                grams.discard(tuple(ignore_words[i : i + n]))
        return grams

    def score(self, text: str) -> float:
        """Return the n-gram overlap score between *text* and the prompt.

        The score is ``|found prompt grams| / |prompt grams|``, or 0.0 if the
        prompt gram set is empty.
        """
        if not self._prompt_grams:
            return 0.0
        words = _tokenize(text)
        n = self._effective_ngram
        found: set[tuple[str, ...]] = set()
        for i in range(len(words) - n + 1):
            gram = tuple(words[i : i + n])
            if gram in self._prompt_grams:
                found.add(gram)
        return len(found) / len(self._prompt_grams)

    def _canary_present(self, text: str) -> bool:
        """Return True if the canary appears in *text* case-insensitively."""
        if self._canary is None:
            return False
        normalized = unicodedata.normalize("NFKC", text).casefold()
        return self._canary in normalized

    def check(self, output: str) -> LeakReport:
        """Check *output* for leakage.

        Computes a verbatim n-gram score, detects the canary, scans for
        base64-encoded copies, and returns a :class:`LeakReport`. Calls the
        ``on_event`` callback if provided.

        Raises:
            LeakError: If ``len(output) > max_output_chars``.
        """
        if len(output) > self._max_output_chars:
            raise LeakError("input_too_large")

        output_score = self.score(output)
        canary_signal = self._canary_present(output)

        encoded_signal = False
        max_decoded_score = 0.0
        # Process at most 20 base64 spans of at most 65,536 characters.
        candidates: list[str] = []
        for match in _BASE64_RE.finditer(output):
            span = match.group(0)
            if len(span) <= 65_536 and len(span) % 4 == 0:
                candidates.append(span)
                if len(candidates) == 20:
                    break
        for span in candidates:
            try:
                decoded_bytes = base64.b64decode(span, validate=True)
            except binascii.Error:
                continue
            try:
                decoded_text = decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                continue
            decoded_score = self.score(decoded_text)
            max_decoded_score = max(max_decoded_score, decoded_score)
            if decoded_score >= self._threshold or self._canary_present(decoded_text):
                encoded_signal = True

        signals: set[str] = set()
        if output_score >= self._threshold:
            signals.add("verbatim")
        if canary_signal:
            signals.add("canary")
        if encoded_signal:
            signals.add("encoded")

        overall_score = max(output_score, max_decoded_score)
        leaked = bool(signals)
        sorted_signals = tuple(sorted(signals))
        report = LeakReport(leaked=leaked, score=overall_score, signals=sorted_signals)

        if self._on_event is not None:
            payload: dict[str, object] = {
                "event": "check",
                "leaked": report.leaked,
                "score": report.score,
                "signals": list(report.signals),
            }
            self._on_event(payload)

        return report
