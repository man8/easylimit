"""
Test suite for the opt-in refund_on_error context manager behaviour.
"""

from datetime import timedelta

import pytest

from easylimit import RateLimiter


class TestDefaultNoRefund:
    """Tokens are consumed even when the context manager body raises."""

    def test_token_not_refunded_by_default(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100))

        with pytest.raises(ValueError):
            with limiter:
                raise ValueError("boom")

        assert limiter.available_tokens() < 9.5

    @pytest.mark.asyncio
    async def test_token_not_refunded_by_default_async(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100))

        with pytest.raises(ValueError):
            async with limiter:
                raise ValueError("boom")

        assert limiter.available_tokens() < 9.5


class TestRefundOnError:
    """Tokens are returned to the bucket when refund_on_error is enabled."""

    def test_token_refunded_on_exception(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100), refund_on_error=True)

        with pytest.raises(ValueError):
            with limiter:
                raise ValueError("boom")

        assert limiter.available_tokens() == pytest.approx(10.0)

    def test_token_not_refunded_on_success(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100), refund_on_error=True)

        with limiter:
            pass

        assert limiter.available_tokens() < 9.5

    def test_refund_does_not_exceed_bucket_size(self) -> None:
        """A refund cannot inflate the bucket beyond its capacity."""
        limiter = RateLimiter(limit=1, period=timedelta(seconds=100), refund_on_error=True)

        for _ in range(3):
            with pytest.raises(ValueError):
                with limiter:
                    raise ValueError("boom")

        assert limiter.available_tokens() == pytest.approx(1.0)

    def test_refund_restores_capacity_for_next_call(self) -> None:
        """A refunded token can be acquired again immediately."""
        limiter = RateLimiter(limit=1, period=timedelta(seconds=100), refund_on_error=True)

        with pytest.raises(ValueError):
            with limiter:
                raise ValueError("boom")

        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False

    def test_refund_with_fractional_limit(self) -> None:
        """Fractional buckets are capped by the same accumulation limit as refills."""
        limiter = RateLimiter(limit=0.4, period=timedelta(seconds=1), refund_on_error=True)

        for _ in range(3):
            with pytest.raises(ValueError):
                with limiter:
                    raise ValueError("boom")

        assert limiter.available_tokens() <= 1.0

    def test_call_tracking_still_records_failed_attempt(self) -> None:
        """Refunding a token does not undo call tracking of the attempt."""
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100), track_calls=True, refund_on_error=True)

        with pytest.raises(ValueError):
            with limiter:
                raise ValueError("boom")

        assert limiter.call_count == 1

    @pytest.mark.asyncio
    async def test_token_refunded_on_exception_async(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100), refund_on_error=True)

        with pytest.raises(ValueError):
            async with limiter:
                raise ValueError("boom")

        assert limiter.available_tokens() == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_token_not_refunded_on_success_async(self) -> None:
        limiter = RateLimiter(limit=10, period=timedelta(seconds=100), refund_on_error=True)

        async with limiter:
            pass

        assert limiter.available_tokens() < 9.5
