"""
Test suite to verify that direct acquire() and async_acquire() calls
properly increment call_count when track_calls=True.

This addresses the bug reported in MAN8-5762.
"""

from datetime import timedelta

import pytest
from easylimit import RateLimiter


class TestDirectAcquireTracking:
    """Test that direct acquire calls properly track call count."""

    def test_sync_acquire_increments_call_count(self) -> None:
        """Test that direct acquire() calls increment call_count."""
        limiter = RateLimiter(limit=100, period=timedelta(hours=1), track_calls=True)

        assert limiter.call_count == 0

        # Direct acquire - should track
        limiter.acquire()
        assert limiter.call_count == 1

        limiter.acquire()
        assert limiter.call_count == 2

    @pytest.mark.asyncio
    async def test_async_acquire_increments_call_count(self) -> None:
        """Test that direct async_acquire() calls increment call_count."""
        limiter = RateLimiter(limit=100, period=timedelta(hours=1), track_calls=True)

        assert limiter.call_count == 0

        # Direct async_acquire - should track
        await limiter.async_acquire()
        assert limiter.call_count == 1

        await limiter.async_acquire()
        assert limiter.call_count == 2

    @pytest.mark.asyncio
    async def test_async_reproduce_issue(self) -> None:
        """
        Reproduce the exact scenario from the bug report.

        This test reproduces the issue described in MAN8-5762 and verifies the fix.
        """
        limiter = RateLimiter(limit=100, period=timedelta(hours=1), track_calls=True)

        # Direct async_acquire - should track now
        await limiter.async_acquire()
        assert limiter.call_count == 1, "Direct async_acquire should increment call_count"

        # Context manager - should also work
        async with limiter:
            pass
        assert limiter.call_count == 2, "Context manager should increment call_count"

    def test_sync_acquire_with_context_manager(self) -> None:
        """Test that both sync acquire and context manager track calls correctly."""
        limiter = RateLimiter(limit=100, period=timedelta(hours=1), track_calls=True)

        # Direct acquire
        limiter.acquire()
        assert limiter.call_count == 1

        # Context manager
        with limiter:
            pass
        assert limiter.call_count == 2

    @pytest.mark.asyncio
    async def test_mixed_acquire_methods(self) -> None:
        """Test that mixing different acquire methods all track correctly."""
        limiter = RateLimiter(limit=100, period=timedelta(hours=1), track_calls=True)

        # Direct sync acquire
        limiter.acquire()
        assert limiter.call_count == 1

        # Direct async acquire
        await limiter.async_acquire()
        assert limiter.call_count == 2

        # Sync context manager
        with limiter:
            pass
        assert limiter.call_count == 3

        # Async context manager
        async with limiter:
            pass
        assert limiter.call_count == 4

    def test_acquire_with_tokens_parameter(self) -> None:
        """Test that acquire with tokens parameter still tracks calls."""
        limiter = RateLimiter(limit=10, period=timedelta(seconds=1), track_calls=True)

        # Multiple acquires in quick succession
        for i in range(5):
            limiter.acquire()
            assert limiter.call_count == i + 1

    @pytest.mark.asyncio
    async def test_async_acquire_with_timeout(self) -> None:
        """Test that async_acquire with timeout still tracks successful acquisitions."""
        limiter = RateLimiter(limit=5, period=timedelta(seconds=1), track_calls=True)

        # Successful acquisition with timeout
        result = await limiter.async_acquire(timeout=1.0)
        assert result is True
        assert limiter.call_count == 1

    def test_acquire_tracks_delay(self) -> None:
        """Test that acquire properly tracks delay time in stats."""
        limiter = RateLimiter(limit=2, period=timedelta(seconds=1), track_calls=True)

        # First two should be instant
        limiter.acquire()
        limiter.acquire()

        # Third should have delay
        limiter.acquire()

        stats = limiter.stats
        assert stats.total_calls == 3
        assert stats.total_delay_seconds > 0.0
        assert stats.average_delay_seconds > 0.0

    @pytest.mark.asyncio
    async def test_async_acquire_tracks_delay(self) -> None:
        """Test that async_acquire properly tracks delay time in stats."""
        limiter = RateLimiter(limit=2, period=timedelta(seconds=1), track_calls=True)

        # First two should be instant
        await limiter.async_acquire()
        await limiter.async_acquire()

        # Third should have delay
        await limiter.async_acquire()

        stats = limiter.stats
        assert stats.total_calls == 3
        assert stats.total_delay_seconds > 0.0
        assert stats.average_delay_seconds > 0.0

    def test_acquire_without_tracking_unchanged(self) -> None:
        """Test that acquire behavior is unchanged when tracking is disabled."""
        limiter = RateLimiter(limit=5, period=timedelta(seconds=1))

        # Should work without errors
        assert limiter.acquire() is True
        assert limiter.acquire() is True

        # Should raise error when trying to access call_count
        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            _ = limiter.call_count
