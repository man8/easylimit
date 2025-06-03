"""
Comprehensive pytest test suite for the RateLimiter class.
"""

import threading
import time

import pytest

from easylimit import RateLimiter


class TestRateLimiterBasic:
    """Test basic functionality of RateLimiter."""

    def test_initialisation(self) -> None:
        """Test RateLimiter initialisation."""
        limiter = RateLimiter(max_calls_per_second=2.0)
        assert limiter.max_calls_per_second == 2.0
        assert limiter.tokens == 2.0
        assert limiter.available_tokens() == 2.0

    def test_initialisation_invalid_rate(self) -> None:
        """Test RateLimiter initialisation with invalid rate."""
        with pytest.raises(ValueError, match="max_calls_per_second must be positive"):
            RateLimiter(max_calls_per_second=0)

        with pytest.raises(ValueError, match="max_calls_per_second must be positive"):
            RateLimiter(max_calls_per_second=-1)

    def test_repr(self) -> None:
        """Test string representation."""
        limiter = RateLimiter(max_calls_per_second=2.5)
        assert repr(limiter) == "RateLimiter(max_calls_per_second=2.5)"


class TestRateLimiterAcquisition:
    """Test token acquisition methods."""

    def test_acquire_immediate(self) -> None:
        """Test immediate token acquisition when tokens are available."""
        limiter = RateLimiter(max_calls_per_second=2)

        start_time = time.time()
        result = limiter.acquire()
        elapsed = time.time() - start_time

        assert result is True
        assert elapsed < 0.1
        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_try_acquire_success(self) -> None:
        """Test non-blocking acquisition when tokens are available."""
        limiter = RateLimiter(max_calls_per_second=2)

        assert limiter.try_acquire() is True
        assert abs(limiter.available_tokens() - 1.0) < 0.01

        assert limiter.try_acquire() is True
        assert abs(limiter.available_tokens() - 0.0) < 0.01

    def test_try_acquire_failure(self) -> None:
        """Test non-blocking acquisition when no tokens are available."""
        limiter = RateLimiter(max_calls_per_second=1)

        assert limiter.try_acquire() is True

        start_time = time.time()
        result = limiter.try_acquire()
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.1

    def test_acquire_with_timeout_success(self) -> None:
        """Test acquisition with timeout that succeeds."""
        limiter = RateLimiter(max_calls_per_second=2)

        result = limiter.acquire(timeout=1.0)
        assert result is True

    def test_acquire_with_timeout_failure(self) -> None:
        """Test acquisition with timeout that fails."""
        limiter = RateLimiter(max_calls_per_second=1)

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
        limiter = RateLimiter(max_calls_per_second=2)

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
        limiter = RateLimiter(max_calls_per_second=2)

        limiter.acquire()
        limiter.acquire()
        assert abs(limiter.available_tokens() - 0.0) < 0.01

        time.sleep(0.6)

        tokens = limiter.available_tokens()
        assert 1.0 <= tokens <= 1.5

    def test_precise_two_calls_per_second(self) -> None:
        """Test the specific requirement: 2 calls per second."""
        limiter = RateLimiter(max_calls_per_second=2)

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
        limiter = RateLimiter(max_calls_per_second=2)

        with limiter:
            assert abs(limiter.available_tokens() - 1.0) < 0.01

        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_context_manager_exception(self) -> None:
        """Test context manager with exception."""
        limiter = RateLimiter(max_calls_per_second=2)

        try:
            with limiter:
                assert abs(limiter.available_tokens() - 1.0) < 0.01
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert abs(limiter.available_tokens() - 1.0) < 0.01

    def test_context_manager_multiple_calls(self) -> None:
        """Test multiple calls using context manager."""
        limiter = RateLimiter(max_calls_per_second=2)

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
        limiter = RateLimiter(max_calls_per_second=4)
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
        limiter = RateLimiter(max_calls_per_second=10)
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
        limiter = RateLimiter(max_calls_per_second=100)

        start_time = time.time()
        for _ in range(50):
            limiter.acquire()

        elapsed = time.time() - start_time
        assert elapsed < 1.0

    def test_fractional_rate(self) -> None:
        """Test with fractional rate."""
        limiter = RateLimiter(max_calls_per_second=1.5)

        start_time = time.time()

        for _ in range(3):
            limiter.acquire()

        total_time = time.time() - start_time

        assert 1.0 <= total_time <= 1.8
