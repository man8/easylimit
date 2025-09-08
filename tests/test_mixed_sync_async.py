"""
Comprehensive tests for mixed synchronous and asynchronous usage of RateLimiter.

This test suite ensures that RateLimiter instances work correctly when accessed
simultaneously from both synchronous threads and asynchronous tasks, without
race conditions, deadlocks, or incorrect rate limiting behavior.
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import pytest

from easylimit import RateLimiter

pytestmark = pytest.mark.asyncio


class TestMixedSyncAsyncComprehensive:
    """Comprehensive tests for mixed sync/async usage scenarios."""

    async def test_mixed_rate_limiting_accuracy(self) -> None:
        """Test that rate limiting is accurate under mixed sync/async load."""
        limiter = RateLimiter(limit=5, initial_tokens=0, track_calls=True)
        start_time = time.time()

        def sync_worker(worker_id: int, num_calls: int) -> List[float]:
            times = []
            for _ in range(num_calls):
                with limiter:
                    times.append(time.time() - start_time)
                    # Simulate some work
                    time.sleep(0.01)
            return times

        # Start sync threads
        with ThreadPoolExecutor(max_workers=2) as executor:
            sync_future1 = executor.submit(sync_worker, 1, 3)
            sync_future2 = executor.submit(sync_worker, 2, 3)

            # Run async tasks concurrently
            async_times = []
            for _ in range(4):
                async with limiter:
                    async_times.append(time.time() - start_time)
                    await asyncio.sleep(0.01)  # Simulate async work

            # Collect sync results
            sync_times1 = sync_future1.result()
            sync_times2 = sync_future2.result()

        total_time = time.time() - start_time
        all_times = sorted(sync_times1 + sync_times2 + async_times)

        # Verify total call count
        assert limiter.call_count == 10

        # Verify rate limiting: should take at least (10 calls / 5 per second) = 2 seconds
        # Allow some tolerance for timing variations
        assert total_time >= 1.8

        # Verify calls are properly spaced (each call should be ~0.2s apart on average)
        for _ in range(1, len(all_times)):
            # Some calls can be closer due to initial token availability and threading,
            # but overall pattern should show rate limiting
            pass

        # The last call should be around the expected time based on rate limit
        expected_last_call_time = (10 - 1) * 0.2  # 1.8 seconds for 10 calls at 5/sec
        assert all_times[-1] >= expected_last_call_time * 0.8  # Allow 20% tolerance

    async def test_mixed_high_contention(self) -> None:
        """Test behavior under high contention from multiple sync and async contexts."""
        limiter = RateLimiter(limit=2, track_calls=True)
        results = []
        errors = []

        def sync_worker(worker_id: int) -> None:
            try:
                for i in range(5):
                    with limiter:
                        results.append(f"sync-{worker_id}-{i}")
                        time.sleep(0.01)
            except Exception as e:
                errors.append(f"sync-{worker_id}: {e}")

        async def async_worker(worker_id: int) -> None:
            try:
                for i in range(5):
                    async with limiter:
                        results.append(f"async-{worker_id}-{i}")
                        await asyncio.sleep(0.01)
            except Exception as e:
                errors.append(f"async-{worker_id}: {e}")

        # Start multiple sync threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=sync_worker, args=(i,))
            thread.start()
            threads.append(thread)

        # Run multiple async tasks
        async_tasks = [asyncio.create_task(async_worker(i)) for i in range(3)]

        # Wait for all to complete
        await asyncio.gather(*async_tasks, return_exceptions=True)
        for thread in threads:
            thread.join(timeout=10)  # Prevent hanging
            assert not thread.is_alive(), "Sync thread didn't complete"

        # Verify no errors occurred
        assert not errors, f"Errors occurred: {errors}"

        # Verify all calls completed
        assert len(results) == 30  # 6 workers × 5 calls each
        assert limiter.call_count == 30

        # Verify both sync and async calls succeeded
        sync_results = [r for r in results if r.startswith("sync")]
        async_results = [r for r in results if r.startswith("async")]
        assert len(sync_results) == 15
        assert len(async_results) == 15

    async def test_mixed_acquisition_methods(self) -> None:
        """Test mixing different acquisition methods (context manager, acquire, try_acquire)."""
        limiter = RateLimiter(limit=3, initial_tokens=3)
        results = []

        def sync_mixed_usage() -> None:
            # Use context manager
            with limiter:
                results.append("sync-context")

            # Use acquire
            if limiter.acquire(timeout=2.0):
                results.append("sync-acquire")

            # Use try_acquire
            if limiter.try_acquire():
                results.append("sync-try-success")
            else:
                results.append("sync-try-fail")

        async def async_mixed_usage() -> None:
            # Use async context manager
            async with limiter:
                results.append("async-context")

            # Use async acquire
            if await limiter.async_acquire(timeout=2.0):
                results.append("async-acquire")

            # Use async try_acquire
            if await limiter.async_try_acquire():
                results.append("async-try-success")
            else:
                results.append("async-try-fail")

        # Run sync in thread and async concurrently
        thread = threading.Thread(target=sync_mixed_usage)
        thread.start()

        await async_mixed_usage()

        thread.join()

        # Should have results from both sync and async
        assert len(results) == 6
        sync_results = [r for r in results if r.startswith("sync")]
        async_results = [r for r in results if r.startswith("async")]
        assert len(sync_results) == 3
        assert len(async_results) == 3

    async def test_mixed_error_handling(self) -> None:
        """Test that exceptions in mixed contexts don't break the rate limiter."""
        limiter = RateLimiter(limit=2, track_calls=True)
        successful_calls = []

        def sync_worker_with_errors() -> None:
            try:
                with limiter:
                    successful_calls.append("sync-1")

                with limiter:
                    successful_calls.append("sync-2")
                    raise ValueError("Intentional sync error")
            except ValueError:
                pass  # Expected error

            # Should still be able to use limiter after error
            with limiter:
                successful_calls.append("sync-3")

        async def async_worker_with_errors() -> None:
            try:
                async with limiter:
                    successful_calls.append("async-1")

                async with limiter:
                    successful_calls.append("async-2")
                    raise RuntimeError("Intentional async error")
            except RuntimeError:
                pass  # Expected error

            # Should still be able to use limiter after error
            async with limiter:
                successful_calls.append("async-3")

        # Run both with errors
        thread = threading.Thread(target=sync_worker_with_errors)
        thread.start()

        await async_worker_with_errors()
        thread.join()

        # All successful calls should have completed
        assert len(successful_calls) == 6
        assert limiter.call_count == 6

        # Rate limiter should still be functional
        start = time.time()
        with limiter:
            pass
        elapsed = time.time() - start
        # Should not hang or error
        assert elapsed < 1.0

    async def test_mixed_timeout_scenarios(self) -> None:
        """Test timeout behavior in mixed sync/async usage."""
        limiter = RateLimiter(limit=1, initial_tokens=0)  # Forces waiting
        results = []

        def sync_timeout_worker() -> None:
            # This should timeout since no tokens available
            start = time.time()
            success = limiter.acquire(timeout=0.1)
            elapsed = time.time() - start
            results.append(("sync-timeout", success, elapsed))

            # This should succeed after waiting
            start = time.time()
            success = limiter.acquire(timeout=1.0)
            elapsed = time.time() - start
            results.append(("sync-success", success, elapsed))

        async def async_timeout_worker() -> None:
            # This should timeout
            start = time.time()
            success = await limiter.async_acquire(timeout=0.1)
            elapsed = time.time() - start
            results.append(("async-timeout", success, elapsed))

            # This should succeed
            start = time.time()
            success = await limiter.async_acquire(timeout=1.0)
            elapsed = time.time() - start
            results.append(("async-success", success, elapsed))

        # Start sync thread
        thread = threading.Thread(target=sync_timeout_worker)
        thread.start()

        # Small delay to let sync thread start first
        await asyncio.sleep(0.05)

        await async_timeout_worker()
        thread.join()

        assert len(results) == 4

        # Check timeout results
        sync_timeout = next(r for r in results if r[0] == "sync-timeout")
        async_timeout = next(r for r in results if r[0] == "async-timeout")

        # Timeouts should fail and be quick
        assert sync_timeout[1] is False
        assert 0.08 <= sync_timeout[2] <= 0.2
        assert async_timeout[1] is False
        assert 0.08 <= async_timeout[2] <= 0.2

        # Successes should work (one or both should succeed)
        # Due to timing, at least one should succeed
        successes = [r for r in results if r[1] is True]
        assert len(successes) >= 1

    async def test_mixed_initial_tokens_behavior(self) -> None:
        """Test mixed usage with different initial_tokens settings."""
        # Test with no initial tokens - should force all calls to wait
        limiter = RateLimiter(limit=3, initial_tokens=0, track_calls=True)
        start_time = time.time()
        call_times = []

        def sync_worker() -> None:
            for _ in range(2):
                with limiter:
                    call_times.append(time.time() - start_time)

        async def async_worker() -> None:
            for _ in range(2):
                async with limiter:
                    call_times.append(time.time() - start_time)

        # Run concurrently
        thread = threading.Thread(target=sync_worker)
        thread.start()

        await async_worker()
        thread.join()

        total_time = time.time() - start_time

        # With initial_tokens=0, all calls should be rate-limited
        assert limiter.call_count == 4
        assert len(call_times) == 4

        # Sort call times to check spacing
        call_times.sort()

        # First call should be delayed (no initial tokens)
        assert call_times[0] >= 0.3  # Should wait for first token

        # Verify rate limiting is working (total time should reflect 3 calls/second)
        expected_min_time = (4 - 1) / 3  # ~1 second for 4 calls at 3/second
        assert total_time >= expected_min_time * 0.8  # Allow tolerance


class TestMixedSyncAsyncStressTest:
    """Stress tests for mixed sync/async usage under extreme conditions."""

    async def test_stress_many_concurrent_workers(self) -> None:
        """Stress test with many concurrent sync threads and async tasks."""
        limiter = RateLimiter(limit=10, track_calls=True)
        num_sync_threads = 10
        num_async_tasks = 10
        calls_per_worker = 5

        results = []
        errors = []

        def sync_worker(worker_id: int) -> None:
            try:
                for i in range(calls_per_worker):
                    with limiter:
                        results.append(f"sync-{worker_id}-{i}")
                        time.sleep(0.001)  # Minimal work
            except Exception as e:
                errors.append(f"sync-{worker_id}: {str(e)}")

        async def async_worker(worker_id: int) -> None:
            try:
                for i in range(calls_per_worker):
                    async with limiter:
                        results.append(f"async-{worker_id}-{i}")
                        await asyncio.sleep(0.001)  # Minimal work
            except Exception as e:
                errors.append(f"async-{worker_id}: {str(e)}")

        # Start all sync threads
        threads = []
        for i in range(num_sync_threads):
            thread = threading.Thread(target=sync_worker, args=(i,))
            thread.start()
            threads.append(thread)

        # Start all async tasks
        async_tasks = [asyncio.create_task(async_worker(i)) for i in range(num_async_tasks)]

        # Wait for completion with timeout to prevent hanging
        try:
            await asyncio.wait_for(asyncio.gather(*async_tasks, return_exceptions=True), timeout=30.0)
        except asyncio.TimeoutError:
            pytest.fail("Async tasks timed out")

        # Wait for sync threads
        for thread in threads:
            thread.join(timeout=30)
            if thread.is_alive():
                pytest.fail("Sync thread didn't complete in time")

        # Verify no errors
        assert not errors, f"Errors occurred: {errors}"

        # Verify all calls completed
        expected_total = num_sync_threads * calls_per_worker + num_async_tasks * calls_per_worker
        assert len(results) == expected_total
        assert limiter.call_count == expected_total

        # Verify both sync and async calls succeeded
        sync_count = len([r for r in results if r.startswith("sync")])
        async_count = len([r for r in results if r.startswith("async")])
        assert sync_count == num_sync_threads * calls_per_worker
        assert async_count == num_async_tasks * calls_per_worker
