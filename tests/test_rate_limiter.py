"""
Comprehensive pytest test suite for the RateLimiter class.
"""

import threading
import time
from datetime import timedelta

import pytest
from easylimit import RateLimiter


class TestRateLimiterBasic:
    """Test basic functionality of RateLimiter."""

    def test_initialisation(self) -> None:
        """Test RateLimiter initialisation."""
        limiter = RateLimiter(limit=2)
        assert limiter.max_calls_per_second == 2.0
        assert limiter.tokens == 2.0
        assert limiter.available_tokens() == 2.0

    def test_initialisation_invalid_rate(self) -> None:
        """Test RateLimiter initialisation with invalid rate."""
        with pytest.raises(ValueError, match="limit must be positive"):
            RateLimiter(limit=0)

        with pytest.raises(ValueError, match="limit must be positive"):
            RateLimiter(limit=-1, period=timedelta(seconds=1))

    def test_repr(self) -> None:
        """Test string representation."""
        limiter = RateLimiter(limit=100)
        repr_str = repr(limiter)
        assert "max_calls_per_second=" in repr_str
        assert "bucket_size=100.0" in repr_str


class TestRateLimiterAcquisition:
    """Test token acquisition methods."""

    def test_acquire_immediate(self) -> None:
        """Test immediate token acquisition when tokens are available."""
        limiter = RateLimiter(limit=2)

        start_time = time.time()
        result = limiter.acquire()
        elapsed = time.time() - start_time

        assert result is True
        assert elapsed < 0.1
        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_try_acquire_success(self) -> None:
        """Test non-blocking acquisition when tokens are available."""
        limiter = RateLimiter(limit=2)

        assert limiter.try_acquire() is True
        assert abs(limiter.available_tokens() - 1.0) < 0.01

        assert limiter.try_acquire() is True
        assert abs(limiter.available_tokens() - 0.0) < 0.01

    def test_try_acquire_failure(self) -> None:
        """Test non-blocking acquisition when no tokens are available."""
        limiter = RateLimiter(limit=1)

        assert limiter.try_acquire() is True

        start_time = time.time()
        result = limiter.try_acquire()
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.1

    def test_acquire_with_timeout_success(self) -> None:
        """Test acquisition with timeout that succeeds."""
        limiter = RateLimiter(limit=2)

        result = limiter.acquire(timeout=1.0)
        assert result is True

    def test_acquire_with_timeout_failure(self) -> None:
        """Test acquisition with timeout that fails."""
        limiter = RateLimiter(limit=1)

        limiter.acquire()

        start_time = time.time()
        result = limiter.acquire(timeout=0.1)
        elapsed = time.time() - start_time

        assert result is False
        assert 0.08 <= elapsed <= 0.15


class TestRateLimiterTiming:
    """Test rate limiting timing behaviour."""

    def test_rate_limiting_behaviour(self) -> None:
        """Test that rate limiting actually limits the rate."""
        limiter = RateLimiter(limit=2)

        call_times = []

        for _i in range(4):
            limiter.acquire()
            call_times.append(time.time())

        total_time = call_times[-1] - call_times[0]

        assert total_time >= 0.9
        assert total_time <= 1.6

        gaps = [call_times[i] - call_times[i - 1] for i in range(1, len(call_times))]

        assert gaps[0] < 0.1

        for gap in gaps[1:]:
            assert 0.4 <= gap <= 0.6

    def test_token_refill(self) -> None:
        """Test that tokens are refilled over time."""
        limiter = RateLimiter(limit=2)

        limiter.acquire()
        limiter.acquire()
        assert abs(limiter.available_tokens() - 0.0) < 0.01

        time.sleep(0.6)

        tokens = limiter.available_tokens()
        assert 1.0 <= tokens <= 1.5

    def test_precise_two_calls_per_second(self) -> None:
        """Test the specific requirement: 2 calls per second."""
        limiter = RateLimiter(limit=2)

        start_time = time.time()
        call_times = []

        for _i in range(6):
            with limiter:
                call_times.append(time.time() - start_time)

        total_time = call_times[-1]

        assert 2.0 <= total_time <= 3.0

        assert call_times[0] < 0.1
        assert call_times[1] < 0.1

        for i in range(2, 6):
            expected_time = (i - 2) * 0.5
            assert abs(call_times[i] - expected_time) < 0.6


class TestRateLimiterContextManager:
    """Test context manager functionality."""

    def test_context_manager_basic(self) -> None:
        """Test basic context manager usage."""
        limiter = RateLimiter(limit=2)

        with limiter:
            assert abs(limiter.available_tokens() - 1.0) < 0.01

        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_context_manager_exception(self) -> None:
        """Test context manager with exception."""
        limiter = RateLimiter(limit=2)

        try:
            with limiter:
                assert abs(limiter.available_tokens() - 1.0) < 0.01
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_context_manager_multiple_calls(self) -> None:
        """Test multiple calls using context manager."""
        limiter = RateLimiter(limit=2)

        results = []
        start_time = time.time()

        for _i in range(4):
            with limiter:
                elapsed = time.time() - start_time
                results.append(elapsed)

        assert results[0] < 0.1
        assert results[1] < 0.1
        assert 0.4 <= results[2] <= 0.6
        assert 0.9 <= results[3] <= 1.1


class TestRateLimiterThreadSafety:
    """Test thread safety of RateLimiter."""

    def test_concurrent_access(self) -> None:
        """Test concurrent access from multiple threads."""
        limiter = RateLimiter(limit=4)
        results = []

        def worker() -> None:
            for _ in range(3):
                start_time = time.time()
                with limiter:
                    end_time = time.time()
                    results.append(end_time - start_time)

        threads = [threading.Thread(target=worker) for _ in range(3)]

        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        assert total_time >= 1.2
        assert len(results) == 9

    def test_thread_safety_token_count(self) -> None:
        """Test that token counting is thread-safe."""
        limiter = RateLimiter(limit=10)
        successful_acquisitions = []

        def worker() -> None:
            for _ in range(5):
                if limiter.try_acquire():
                    successful_acquisitions.append(1)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(successful_acquisitions) <= 10


class TestRateLimiterEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_high_rate(self) -> None:
        """Test with very high rate."""
        limiter = RateLimiter(limit=100)

        start_time = time.time()
        for _ in range(50):
            limiter.acquire()

        elapsed = time.time() - start_time
        assert elapsed < 1.0

    def test_fractional_rate(self) -> None:
        """Test with fractional rate."""
        # Fractional-like rate using period-based API: 3 calls per 2 seconds
        limiter = RateLimiter(limit=3, period=timedelta(seconds=2))

        start_time = time.time()

        for _ in range(3):
            limiter.acquire()

        total_time = time.time() - start_time

        # All three should be available immediately as an initial burst
        assert total_time < 0.5


class TestRateLimiterUnlimited:
    """Test unlimited rate limiter functionality."""

    def test_unlimited_creation(self) -> None:
        """Test that unlimited() creates a proper RateLimiter instance."""
        limiter = RateLimiter.unlimited()
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_calls_per_second == float("inf")
        assert limiter._track_calls is False

    def test_unlimited_no_rate_limiting(self) -> None:
        """Test that unlimited limiter performs no rate limiting."""
        limiter = RateLimiter.unlimited()

        start_time = time.time()

        for _ in range(100):
            with limiter:
                pass

        elapsed = time.time() - start_time
        assert elapsed < 0.5

    def test_unlimited_context_manager(self) -> None:
        """Test unlimited limiter as context manager."""
        limiter = RateLimiter.unlimited()

        with limiter:
            pass

        for _ in range(10):
            with limiter:
                pass

    def test_unlimited_acquire_methods(self) -> None:
        """Test unlimited limiter acquire methods."""
        limiter = RateLimiter.unlimited()

        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire(timeout=0.1) is True

    def test_unlimited_call_tracking(self) -> None:
        """Test that unlimited limiter maintains call tracking when enabled."""
        limiter = RateLimiter.unlimited(track_calls=True)

        for _ in range(5):
            with limiter:
                pass

        assert limiter.call_count == 5
        stats = limiter.stats
        assert stats.total_calls == 5
        assert stats.average_delay_seconds >= 0

        limiter.reset_call_count()
        assert limiter.call_count == 0

    def test_unlimited_windowed_queries(self) -> None:
        """Test windowed query methods work with unlimited limiter when tracking enabled."""
        limiter = RateLimiter.unlimited(track_calls=True)

        for _ in range(3):
            with limiter:
                pass

        assert limiter.calls_in_window(60) == 3
        efficiency = limiter.get_efficiency(60)
        assert efficiency >= 0

    def test_unlimited_thread_safety(self) -> None:
        """Test unlimited limiter is thread-safe with tracking enabled."""
        limiter = RateLimiter.unlimited(track_calls=True)
        results = []

        def worker() -> None:
            for _ in range(10):
                with limiter:
                    results.append(1)

        threads = [threading.Thread(target=worker) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 30
        assert limiter.call_count == 30

    def test_unlimited_available_tokens(self) -> None:
        """Test unlimited limiter always has maximum tokens available."""
        limiter = RateLimiter.unlimited()

        assert limiter.available_tokens() == float("inf")

        limiter.acquire()
        limiter.acquire()
        assert limiter.available_tokens() == float("inf")
