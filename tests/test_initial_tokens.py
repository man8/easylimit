"""Tests for the initial_tokens parameter functionality."""

import time
from datetime import timedelta

import pytest
from easylimit import RateLimiter


class TestInitialTokensBasic:
    """Test basic initial_tokens functionality."""

    def test_initial_tokens_none_defaults_to_bucket_size(self):
        """Test that initial_tokens=None uses bucket_size (backward compatibility)."""
        limiter = RateLimiter(limit=5, initial_tokens=None)
        assert limiter.available_tokens() == 5.0

    def test_initial_tokens_zero(self):
        """Test that initial_tokens=0 starts with empty bucket."""
        limiter = RateLimiter(limit=5, initial_tokens=0)
        assert limiter.available_tokens() < 0.1

    def test_initial_tokens_partial(self):
        """Test that initial_tokens can be set to partial bucket."""
        limiter = RateLimiter(limit=10, initial_tokens=3)
        assert abs(limiter.available_tokens() - 3.0) < 0.1

    def test_initial_tokens_full_bucket(self):
        """Test that initial_tokens can be set to full bucket size."""
        limiter = RateLimiter(limit=7, initial_tokens=7)
        assert limiter.available_tokens() == 7.0

    def test_initial_tokens_float_values(self):
        """Test that initial_tokens supports float values."""
        limiter = RateLimiter(limit=5.5, initial_tokens=2.3)
        assert abs(limiter.available_tokens() - 2.3) < 0.1

    def test_initial_tokens_with_period_based_api(self):
        """Test initial_tokens with period-based constructor."""
        limiter = RateLimiter(limit=120, period=timedelta(minutes=1), initial_tokens=50)
        assert abs(limiter.available_tokens() - 50.0) < 0.1

    def test_initial_tokens_with_legacy_api(self):
        """Test initial_tokens with deprecated max_calls_per_second."""
        import os

        os.environ["EASYLIMIT_SUPPRESS_DEPRECATIONS"] = "1"
        try:
            limiter = RateLimiter(max_calls_per_second=3.0, initial_tokens=1.5)
            assert abs(limiter.available_tokens() - 1.5) < 0.1
        finally:
            os.environ.pop("EASYLIMIT_SUPPRESS_DEPRECATIONS", None)


class TestInitialTokensValidation:
    """Test validation of initial_tokens parameter."""

    def test_initial_tokens_negative_raises_error(self):
        """Test that negative initial_tokens raises ValueError."""
        with pytest.raises(ValueError, match="initial_tokens must be non-negative"):
            RateLimiter(limit=5, initial_tokens=-1)

    def test_initial_tokens_exceeds_bucket_size_raises_error(self):
        """Test that initial_tokens > bucket_size raises ValueError."""
        with pytest.raises(ValueError, match="initial_tokens \\(10\\) cannot exceed bucket_size \\(5.0\\)"):
            RateLimiter(limit=5, initial_tokens=10)

    def test_initial_tokens_non_numeric_raises_error(self):
        """Test that non-numeric initial_tokens raises ValueError."""
        with pytest.raises(ValueError, match="initial_tokens must be a number"):
            RateLimiter(limit=5, initial_tokens="invalid")

    def test_initial_tokens_equals_bucket_size_allowed(self):
        """Test that initial_tokens equal to bucket_size is allowed."""
        limiter = RateLimiter(limit=5, initial_tokens=5.0)
        assert limiter.available_tokens() == 5.0

    def test_initial_tokens_zero_allowed(self):
        """Test that initial_tokens=0 is explicitly allowed."""
        limiter = RateLimiter(limit=5, initial_tokens=0.0)
        assert limiter.available_tokens() < 0.1

    def test_initial_tokens_fractional_bucket_validation(self):
        """Test validation with fractional bucket sizes."""
        limiter = RateLimiter(limit=0.5, initial_tokens=0.3)
        assert abs(limiter.available_tokens() - 0.3) < 0.1

        with pytest.raises(ValueError, match="initial_tokens \\(0.8\\) cannot exceed bucket_size \\(0.5\\)"):
            RateLimiter(limit=0.5, initial_tokens=0.8)


class TestInitialTokensBehaviour:
    """Test behavioural aspects of initial_tokens."""

    def test_initial_tokens_affects_immediate_availability(self):
        """Test that initial_tokens affects immediate token availability."""
        limiter_empty = RateLimiter(limit=5, initial_tokens=0)
        limiter_partial = RateLimiter(limit=5, initial_tokens=2)
        limiter_full = RateLimiter(limit=5, initial_tokens=5)

        assert not limiter_empty.try_acquire()
        assert limiter_partial.try_acquire()
        assert limiter_partial.try_acquire()
        assert not limiter_partial.try_acquire()

        for _ in range(5):
            assert limiter_full.try_acquire()
        assert not limiter_full.try_acquire()

    def test_initial_tokens_with_context_manager(self):
        """Test initial_tokens behaviour with context manager."""
        limiter = RateLimiter(limit=3, initial_tokens=1)

        with limiter:
            pass

        assert limiter.available_tokens() < 0.1

    def test_initial_tokens_refill_behaviour(self):
        """Test that tokens refill normally after initial_tokens is consumed."""
        limiter = RateLimiter(limit=2, period=timedelta(seconds=1), initial_tokens=0)

        assert limiter.available_tokens() < 0.1

        time.sleep(0.6)
        tokens_after_wait = limiter.available_tokens()
        assert 1.0 <= tokens_after_wait <= 1.5

    def test_initial_tokens_with_tracking(self):
        """Test initial_tokens works correctly with call tracking enabled."""
        limiter = RateLimiter(limit=5, initial_tokens=2, track_calls=True)

        assert abs(limiter.available_tokens() - 2.0) < 0.1
        assert limiter.call_count == 0

        with limiter:
            pass

        assert limiter.call_count == 1
        assert abs(limiter.available_tokens() - 1.0) < 0.1


class TestInitialTokensAllConstructorOverloads:
    """Test initial_tokens parameter works with all constructor overloads."""

    def test_limit_only_overload(self):
        """Test initial_tokens with limit-only constructor."""
        limiter = RateLimiter(limit=5, initial_tokens=2)
        assert abs(limiter.available_tokens() - 2.0) < 0.1

    def test_limit_and_period_overload(self):
        """Test initial_tokens with limit and period constructor."""
        limiter = RateLimiter(limit=10, period=timedelta(seconds=2), initial_tokens=4)
        assert abs(limiter.available_tokens() - 4.0) < 0.1

    def test_tracking_only_overload(self):
        """Test initial_tokens with tracking-only constructor."""
        limiter = RateLimiter(track_calls=True, initial_tokens=0.5)
        assert abs(limiter.available_tokens() - 0.5) < 0.1

    def test_legacy_overload(self):
        """Test initial_tokens with legacy max_calls_per_second constructor."""
        import os

        os.environ["EASYLIMIT_SUPPRESS_DEPRECATIONS"] = "1"
        try:
            limiter = RateLimiter(max_calls_per_second=2.0, initial_tokens=1.0)
            assert abs(limiter.available_tokens() - 1.0) < 0.1
        finally:
            os.environ.pop("EASYLIMIT_SUPPRESS_DEPRECATIONS", None)


class TestInitialTokensEdgeCases:
    """Test edge cases for initial_tokens parameter."""

    def test_initial_tokens_with_unlimited_limiter(self):
        """Test that unlimited limiter ignores initial_tokens."""
        limiter = RateLimiter.unlimited()
        assert limiter.available_tokens() == float("inf")

    def test_initial_tokens_very_small_values(self):
        """Test initial_tokens with very small float values."""
        limiter = RateLimiter(limit=0.1, initial_tokens=0.05)
        assert abs(limiter.available_tokens() - 0.05) < 0.01

    def test_initial_tokens_precision(self):
        """Test initial_tokens maintains precision for float values."""
        limiter = RateLimiter(limit=1.0, initial_tokens=0.123456789)
        assert abs(limiter.available_tokens() - 0.123456789) < 0.01

    def test_initial_tokens_thread_safety(self):
        """Test initial_tokens is thread-safe during initialisation."""
        import threading

        results = []

        def create_limiter():
            limiter = RateLimiter(limit=5, initial_tokens=3)
            results.append(limiter.available_tokens())

        threads = [threading.Thread(target=create_limiter) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert all(abs(tokens - 3.0) < 0.1 for tokens in results)
        assert len(results) == 10


class TestInitialTokensBackwardCompatibility:
    """Test that initial_tokens maintains backward compatibility."""

    def test_default_behaviour_unchanged(self):
        """Test that not specifying initial_tokens maintains current behaviour."""
        limiter_old_style = RateLimiter(limit=5)
        limiter_explicit_none = RateLimiter(limit=5, initial_tokens=None)

        assert limiter_old_style.available_tokens() == limiter_explicit_none.available_tokens()
        assert limiter_old_style.available_tokens() == 5.0

    def test_existing_api_patterns_work(self):
        """Test that existing API usage patterns continue to work."""
        limiter1 = RateLimiter(limit=120, period=timedelta(minutes=1))
        assert limiter1.available_tokens() == 120.0

        limiter2 = RateLimiter(limit=10)
        assert limiter2.available_tokens() == 10.0

        limiter3 = RateLimiter()
        assert limiter3.available_tokens() == 1.0

    def test_repr_includes_initial_state(self):
        """Test that repr shows the current state correctly."""
        limiter = RateLimiter(limit=5, initial_tokens=2)
        repr_str = repr(limiter)
        assert "bucket_size=5.0" in repr_str
