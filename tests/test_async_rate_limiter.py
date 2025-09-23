"""
Async test suite for RateLimiter async API and context manager.
"""

import threading
import time

import pytest

from easylimit import RateLimiter

pytestmark = pytest.mark.asyncio


class TestAsyncAcquisition:
    """Test async token acquisition methods."""

    async def test_async_acquire_immediate(self) -> None:
        """Test immediate async token acquisition."""
        limiter = RateLimiter(limit=2)
        start = time.time()
        got = await limiter.async_acquire()
        assert got is True
        assert (time.time() - start) < 0.1
        assert abs(limiter.available_tokens() - 1.0) < 0.01

    async def test_async_try_acquire_success_and_failure(self) -> None:
        """Test async try_acquire success and failure cases."""
        limiter = RateLimiter(limit=1)
        assert await limiter.async_try_acquire() is True
        start = time.time()
        got = await limiter.async_try_acquire()
        elapsed = time.time() - start
        assert got is False
        assert elapsed < 0.1

    async def test_async_acquire_with_timeout_success(self) -> None:
        """Test async acquire with timeout that succeeds."""
        limiter = RateLimiter(limit=1)
        assert await limiter.async_acquire(timeout=0.5) is True

    async def test_async_acquire_with_timeout_failure(self) -> None:
        """Test async acquire with timeout that fails."""
        limiter = RateLimiter(limit=1)
        assert await limiter.async_acquire() is True
        start = time.time()
        got = await limiter.async_acquire(timeout=0.1)
        elapsed = time.time() - start
        assert got is False
        assert 0.08 <= elapsed <= 0.2


class TestAsyncContextManager:
    """Test async context manager behaviour and timing."""

    async def test_async_with_basic_timing(self) -> None:
        """Test async context manager timing behaviour."""
        limiter = RateLimiter(limit=2)
        t0 = time.time()
        stamps = []
        for _ in range(4):
            async with limiter:
                stamps.append(time.time() - t0)
        assert stamps[0] < 0.1
        assert stamps[1] < 0.1
        assert 0.4 <= stamps[2] <= 0.7
        assert 0.9 <= stamps[3] <= 1.2

    async def test_async_call_tracking(self) -> None:
        """Test call tracking with async context manager."""
        limiter = RateLimiter(limit=2, track_calls=True)
        for _ in range(3):
            async with limiter:
                pass
        assert limiter.call_count == 3
        stats = limiter.stats
        assert stats.total_calls == 3
        assert stats.average_delay_seconds >= 0.0

    async def test_async_acquire_records_tracking(self) -> None:
        """Direct async_acquire() should increment the tracked call count."""
        limiter = RateLimiter(limit=2, track_calls=True)

        assert limiter.call_count == 0
        assert await limiter.async_acquire() is True
        assert limiter.call_count == 1

    async def test_async_try_acquire_records_tracking(self) -> None:
        """async_try_acquire() should only count successful acquisitions."""
        limiter = RateLimiter(limit=1, track_calls=True)

        assert await limiter.async_try_acquire() is True
        assert limiter.call_count == 1

        # Subsequent call has no tokens available yet
        assert await limiter.async_try_acquire() is False
        assert limiter.call_count == 1


class TestMixedSyncAsync:
    """Test mixed sync and async usage to ensure unified locking works."""

    async def test_mixed_concurrent_usage(self) -> None:
        """Test concurrent sync and async usage."""
        limiter = RateLimiter(limit=3, track_calls=True)
        results = []

        def sync_worker(n: int) -> None:
            for _ in range(n):
                with limiter:
                    results.append("sync")

        thread = threading.Thread(target=sync_worker, args=(3,))
        thread.start()

        for _ in range(3):
            async with limiter:
                results.append("async")

        thread.join()

        assert limiter.call_count == 6
        assert len(results) == 6
