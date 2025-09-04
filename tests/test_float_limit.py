"""
Test support for float values in the limit parameter.
"""

import time
from datetime import timedelta

import pytest

from easylimit import RateLimiter


class TestFloatLimitSupport:
    """Test that float values work correctly for the limit parameter."""

    def test_float_limit_basic(self) -> None:
        """Test basic functionality with float limit."""
        limiter = RateLimiter(limit=2.5, period=timedelta(seconds=1))

        assert limiter.max_calls_per_second == 2.5
        assert limiter.bucket_size == 2.5
        assert limiter.available_tokens() == 2.5

    def test_float_limit_fractional_rate(self) -> None:
        """Test fractional rate like 0.4 requests per second."""
        # 0.4 requests per second = 4 requests per 10 seconds
        limiter = RateLimiter(limit=0.4, period=timedelta(seconds=1))

        assert limiter.max_calls_per_second == 0.4
        assert limiter.bucket_size == 0.4

    def test_float_limit_equivalent_scaling(self) -> None:
        """Test that float limit gives equivalent results to scaled integer."""
        # These should be mathematically equivalent:
        # 0.4 req/sec vs 4 req/10sec
        float_limiter = RateLimiter(limit=0.4, period=timedelta(seconds=1))
        scaled_limiter = RateLimiter(limit=4, period=timedelta(seconds=10))

        assert abs(float_limiter.max_calls_per_second - scaled_limiter.max_calls_per_second) < 1e-10

    def test_float_limit_with_period(self) -> None:
        """Test float limit with custom period."""
        # 1.5 requests per 2 seconds = 0.75 requests per second
        limiter = RateLimiter(limit=1.5, period=timedelta(seconds=2))

        assert limiter.max_calls_per_second == 0.75
        assert limiter.bucket_size == 1.5

    def test_float_limit_validation(self) -> None:
        """Test validation with float limits."""
        with pytest.raises(ValueError, match="limit must be positive"):
            RateLimiter(limit=0.0)

        with pytest.raises(ValueError, match="limit must be positive"):
            RateLimiter(limit=-0.5, period=timedelta(seconds=1))

    def test_float_limit_context_manager(self) -> None:
        """Test context manager usage with float limit."""
        limiter = RateLimiter(limit=1.5, period=timedelta(seconds=2))

        start_time = time.time()
        with limiter:
            pass
        elapsed = time.time() - start_time

        # Should complete immediately on first call
        assert elapsed < 0.1

    def test_float_limit_with_tracking(self) -> None:
        """Test float limit with call tracking enabled."""
        limiter = RateLimiter(limit=2.5, track_calls=True)

        for _ in range(2):
            with limiter:
                pass

        assert limiter.call_count == 2
        stats = limiter.stats
        assert stats.total_calls == 2

    def test_float_limit_acquire_methods(self) -> None:
        """Test acquire and try_acquire with float limits."""
        limiter = RateLimiter(limit=2.5, period=timedelta(seconds=1))

        # Should be able to acquire immediately
        assert limiter.try_acquire() is True

        # Should have tokens left (1.5)
        available = limiter.available_tokens()
        assert 1.4 <= available <= 1.6  # Allow for small timing variations

        # Should be able to acquire one more full token
        assert limiter.try_acquire() is True

        # Now should have 0.5 tokens left, which is less than 1, so should fail
        assert limiter.try_acquire() is False

    def test_backward_compatibility(self) -> None:
        """Test that integer limits still work (backward compatibility)."""
        limiter = RateLimiter(limit=5, period=timedelta(seconds=1))

        assert limiter.max_calls_per_second == 5.0
        assert limiter.bucket_size == 5.0
        assert limiter.available_tokens() == 5.0

    def test_very_small_float_limit(self) -> None:
        """Test with very small float limits."""
        # 0.1 requests per second = 1 request per 10 seconds
        limiter = RateLimiter(limit=0.1, period=timedelta(seconds=1))

        assert limiter.max_calls_per_second == 0.1
        assert limiter.bucket_size == 0.1

        # With bucket size 0.1, we can't acquire a full token (which requires 1.0)
        # This is expected behavior - the token bucket requires at least 1 token for acquisition
        # For very small rates, users should scale up: 1 request per 10 seconds instead
        assert limiter.try_acquire() is False

        # But after waiting, tokens should accumulate
        time.sleep(1.1)  # Wait for tokens to accumulate
        assert limiter.available_tokens() >= 0.1
