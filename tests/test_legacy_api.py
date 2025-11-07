"""
Legacy API tests for the deprecated max_calls_per_second signature.
Run these selectively with: uv run pytest -m legacy
"""

import time
from datetime import timedelta

import pytest
from easylimit import RateLimiter

# Mark all tests in this module as legacy
pytestmark = pytest.mark.legacy


def test_basic_initialisation_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EASYLIMIT_SUPPRESS_DEPRECATIONS", "1")
    limiter = RateLimiter(max_calls_per_second=2.0)
    assert limiter.max_calls_per_second == 2.0
    assert limiter.available_tokens() == 2.0


def test_acquire_and_try_acquire_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EASYLIMIT_SUPPRESS_DEPRECATIONS", "1")
    limiter = RateLimiter(max_calls_per_second=2)
    assert limiter.try_acquire() is True
    assert limiter.acquire() is True


def test_fractional_legacy_with_suppression(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EASYLIMIT_SUPPRESS_DEPRECATIONS", "1")
    limiter = RateLimiter(max_calls_per_second=1.5)
    start = time.time()
    for _ in range(3):
        limiter.acquire()
    elapsed = time.time() - start
    assert 1.0 <= elapsed <= 1.8


def test_legacy_deprecation_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    # Explicitly assert a warning for legacy usage
    monkeypatch.delenv("EASYLIMIT_SUPPRESS_DEPRECATIONS", raising=False)
    with pytest.warns(DeprecationWarning, match="max_calls_per_second"):
        limiter = RateLimiter(max_calls_per_second=2.0)
        assert limiter.max_calls_per_second == 2.0


def test_conflicting_params_still_error() -> None:
    with pytest.raises(ValueError, match="Cannot specify both max_calls_per_second and limit/period"):
        RateLimiter(max_calls_per_second=1.0, limit=10, period=timedelta(seconds=10))


def test_invalid_max_calls_per_second_raises_value_error() -> None:
    # Lines 114-115: validate legacy max_calls_per_second > 0
    with pytest.raises(ValueError, match="max_calls_per_second must be positive"):
        RateLimiter(max_calls_per_second=0)

    with pytest.raises(ValueError, match="max_calls_per_second must be positive"):
        RateLimiter(max_calls_per_second=-1)
