"""Behavior tests for the public API of system_prompt_leak_detector."""

from __future__ import annotations

import pytest

import system_prompt_leak_detector


def test_normalize_trims_and_lowercases() -> None:
    assert system_prompt_leak_detector.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        system_prompt_leak_detector.normalize(value)


def test_version_is_semver() -> None:
    parts = system_prompt_leak_detector.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
