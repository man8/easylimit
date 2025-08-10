"""
Test suite for the new period-based API parameters.
"""

import time
from datetime import timedelta

import pytest

from easylimit import RateLimiter


class TestPeriodBasedAPI:
    """Test the new period-based API parameters."""

    def test_period_based_constructor(self) -> None:
        """Test constructor with rate_limit_calls and rate_limit_period."""
        limiter = RateLimiter(rate_limit_calls=1200, rate_limit_period=timedelta(hours=1))

        assert limiter.max_calls_per_second == 1200 / 3600
        assert limiter.bucket_size == 1200.0
        assert limiter.available_tokens() == 1200.0

    def test_period_based_burst_behavior(self) -> None:
        """Test that period-based limits allow proper bursting."""
        limiter = RateLimiter(rate_limit_calls=10, rate_limit_period=timedelta(seconds=10))

        start_time = time.time()
        call_times = []

        for _ in range(10):
            with limiter:
                call_times.append(time.time() - start_time)

        for call_time in call_times:
            assert call_time < 0.1

    def test_period_based_validation(self) -> None:
        """Test validation of period-based parameters."""
        with pytest.raises(ValueError, match="rate_limit_calls must be positive"):
            RateLimiter(rate_limit_calls=0, rate_limit_period=timedelta(seconds=1))

        with pytest.raises(ValueError, match="rate_limit_calls must be positive"):
            RateLimiter(rate_limit_calls=-1, rate_limit_period=timedelta(seconds=1))

        with pytest.raises(ValueError, match="rate_limit_period must be positive"):
            RateLimiter(rate_limit_calls=1, rate_limit_period=timedelta(seconds=0))

        with pytest.raises(ValueError, match="rate_limit_period must be positive"):
            RateLimiter(rate_limit_calls=1, rate_limit_period=timedelta(seconds=-1))

    def test_conflicting_parameters(self) -> None:
        """Test that conflicting parameters raise an error."""
        with pytest.raises(
            ValueError, match="Cannot specify both max_calls_per_second and rate_limit_calls/rate_limit_period"
        ):
            RateLimiter(max_calls_per_second=1.0, rate_limit_calls=10, rate_limit_period=timedelta(seconds=10))

    def test_incomplete_period_parameters(self) -> None:
        """Test that incomplete period parameters raise an error."""
        with pytest.raises(
            ValueError, match="Must specify either max_calls_per_second or both rate_limit_calls and rate_limit_period"
        ):
            RateLimiter(rate_limit_calls=10)

        with pytest.raises(
            ValueError, match="Must specify either max_calls_per_second or both rate_limit_calls and rate_limit_period"
        ):
            RateLimiter(rate_limit_period=timedelta(seconds=10))

    def test_backward_compatibility(self) -> None:
        """Test that existing max_calls_per_second API still works."""
        limiter = RateLimiter(max_calls_per_second=2.0)

        assert limiter.max_calls_per_second == 2.0
        assert limiter.bucket_size == 2.0
        assert limiter.available_tokens() == 2.0

    def test_default_parameters(self) -> None:
        """Test that default parameters work when no rate is specified."""
        limiter = RateLimiter()

        assert limiter.max_calls_per_second == 1.0
        assert limiter.bucket_size == 1.0
        assert limiter.available_tokens() == 1.0

    def test_fractional_rates_performance(self) -> None:
        """Test that fractional rates like 1200 calls/hour work without performance issues."""
        limiter = RateLimiter(rate_limit_calls=1200, rate_limit_period=timedelta(hours=1))

        start_time = time.time()

        for _ in range(5):
            with limiter:
                pass

        elapsed = time.time() - start_time
        assert elapsed < 0.1

    def test_period_based_repr(self) -> None:
        """Test string representation with period-based parameters."""
        limiter = RateLimiter(rate_limit_calls=100, rate_limit_period=timedelta(minutes=1))

        repr_str = repr(limiter)
        assert "max_calls_per_second=" in repr_str
        assert "bucket_size=100.0" in repr_str

    def test_timedelta_various_units(self) -> None:
        """Test timedelta with various time units."""
        limiter_seconds = RateLimiter(rate_limit_calls=10, rate_limit_period=timedelta(seconds=5))
        assert limiter_seconds.max_calls_per_second == 2.0

        limiter_minutes = RateLimiter(rate_limit_calls=60, rate_limit_period=timedelta(minutes=1))
        assert limiter_minutes.max_calls_per_second == 1.0

        limiter_hours = RateLimiter(rate_limit_calls=3600, rate_limit_period=timedelta(hours=1))
        assert limiter_hours.max_calls_per_second == 1.0

        limiter_days = RateLimiter(rate_limit_calls=86400, rate_limit_period=timedelta(days=1))
        assert limiter_days.max_calls_per_second == 1.0

    def test_period_based_with_tracking(self) -> None:
        """Test period-based API with call tracking enabled."""
        limiter = RateLimiter(rate_limit_calls=5, rate_limit_period=timedelta(seconds=1), track_calls=True)

        for _ in range(3):
            with limiter:
                pass

        assert limiter.call_count == 3
        stats = limiter.stats
        assert stats.total_calls == 3
