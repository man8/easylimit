"""
Comprehensive pytest test suite for the RateLimiter call tracking functionality.
"""

import threading
import time
from datetime import timedelta

import pytest

from easylimit import RateLimiter
from easylimit.rate_limiter import CallStats


class TestCallTrackingBasic:
    """Test basic call tracking functionality."""

    def test_tracking_disabled_by_default(self) -> None:
        """Test that call tracking is disabled by default."""
        limiter = RateLimiter(limit=2)

        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            _ = limiter.call_count

        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            _ = limiter.stats

        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            limiter.reset_call_count()

        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            limiter.calls_in_window(60)

        with pytest.raises(ValueError, match="Call tracking is not enabled"):
            limiter.get_efficiency()

    def test_tracking_enabled_constructor(self) -> None:
        """Test enabling call tracking via constructor."""
        limiter = RateLimiter(limit=2, track_calls=True)

        assert limiter.call_count == 0
        assert isinstance(limiter.stats, CallStats)
        assert limiter.stats.total_calls == 0

    def test_history_window_parameter(self) -> None:
        """Test custom history window parameter."""
        limiter = RateLimiter(limit=2, track_calls=True, history_window_seconds=1800)

        assert limiter._history_window == 1800


class TestCallCounting:
    """Test call counting functionality."""

    def test_call_count_increments(self) -> None:
        """Test that call count increments with each call."""
        limiter = RateLimiter(limit=5, track_calls=True)

        assert limiter.call_count == 0

        with limiter:
            pass
        assert limiter.call_count == 1

        with limiter:
            pass
        assert limiter.call_count == 2

    def test_call_count_thread_safe(self) -> None:
        """Test that call counting is thread-safe."""
        limiter = RateLimiter(limit=10, track_calls=True)

        def worker() -> None:
            for _ in range(5):
                with limiter:
                    pass

        threads = [threading.Thread(target=worker) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert limiter.call_count == 15

    def test_call_count_increments_for_acquire(self) -> None:
        """Call tracking should include direct acquire() usage."""
        limiter = RateLimiter(limit=5, track_calls=True)

        assert limiter.call_count == 0
        assert limiter.acquire() is True
        assert limiter.call_count == 1

    def test_call_count_increments_for_try_acquire(self) -> None:
        """Call tracking should include try_acquire() successes only."""
        limiter = RateLimiter(limit=2, track_calls=True)

        assert limiter.try_acquire() is True
        assert limiter.call_count == 1

        assert limiter.try_acquire() is True
        assert limiter.call_count == 2

        # Bucket is empty now; failure should not increment the counter
        assert limiter.try_acquire() is False
        assert limiter.call_count == 2

    def test_reset_call_count(self) -> None:
        """Test resetting call count."""
        limiter = RateLimiter(limit=5, track_calls=True)

        with limiter:
            pass
        with limiter:
            pass

        assert limiter.call_count == 2

        limiter.reset_call_count()

        assert limiter.call_count == 0
        assert limiter.stats.total_calls == 0


class TestCallStats:
    """Test CallStats functionality."""

    def test_stats_empty_state(self) -> None:
        """Test stats when no calls have been made."""
        limiter = RateLimiter(limit=2, track_calls=True)

        stats = limiter.stats

        assert stats.total_calls == 0
        assert stats.total_delay_seconds == 0.0
        assert stats.average_delay_seconds == 0.0
        assert stats.max_delay_seconds == 0.0
        assert stats.calls_per_second_average == 0.0
        assert stats.efficiency_percentage == 0.0
        assert stats.tracking_start_time is not None
        assert stats.last_call_time is None

    def test_stats_with_calls(self) -> None:
        """Test stats after making calls."""
        limiter = RateLimiter(limit=5, track_calls=True)

        with limiter:
            pass
        with limiter:
            pass

        stats = limiter.stats

        assert stats.total_calls == 2
        assert stats.total_delay_seconds >= 0.0
        assert stats.average_delay_seconds >= 0.0
        assert stats.max_delay_seconds >= 0.0
        assert stats.calls_per_second_average > 0.0
        assert 0.0 <= stats.efficiency_percentage <= 100.0
        assert stats.last_call_time is not None

    def test_stats_delay_tracking(self) -> None:
        """Test that delays are properly tracked."""
        limiter = RateLimiter(limit=1, track_calls=True)

        with limiter:
            pass
        with limiter:
            pass
        with limiter:
            pass

        stats = limiter.stats

        assert stats.total_calls == 3
        assert stats.total_delay_seconds > 1.0
        assert stats.average_delay_seconds > 0.0
        assert stats.max_delay_seconds > 0.0


class TestWindowedQueries:
    """Test windowed query functionality."""

    def test_calls_in_window_validation(self) -> None:
        """Test validation of window_seconds parameter."""
        limiter = RateLimiter(limit=2, track_calls=True)

        with pytest.raises(ValueError, match="window_seconds must be positive"):
            limiter.calls_in_window(0)

        with pytest.raises(ValueError, match="window_seconds must be positive"):
            limiter.calls_in_window(-1)

    def test_calls_in_window_basic(self) -> None:
        """Test basic windowed call counting."""
        limiter = RateLimiter(limit=5, track_calls=True)

        with limiter:
            pass
        with limiter:
            pass

        assert limiter.calls_in_window(60) == 2
        assert limiter.calls_in_window(1) == 2

    def test_calls_in_window_time_filtering(self) -> None:
        """Test that old calls are filtered out of window."""
        limiter = RateLimiter(limit=10, period=timedelta(seconds=1), track_calls=True, history_window_seconds=5)

        with limiter:
            pass

        time.sleep(0.1)

        with limiter:
            pass

        assert limiter.calls_in_window(1) == 2
        assert limiter.calls_in_window(60) == 2

    def test_get_efficiency_validation(self) -> None:
        """Test validation of efficiency calculation parameters."""
        limiter = RateLimiter(limit=2, period=timedelta(seconds=1), track_calls=True)

        with pytest.raises(ValueError, match="window_seconds must be positive"):
            limiter.get_efficiency(0)

        with pytest.raises(ValueError, match="window_seconds must be positive"):
            limiter.get_efficiency(-1)

    def test_get_efficiency_calculation(self) -> None:
        """Test efficiency calculation."""
        limiter = RateLimiter(limit=2, period=timedelta(seconds=1), track_calls=True)

        assert limiter.get_efficiency(60) == 0.0

        with limiter:
            pass
        with limiter:
            pass

        efficiency = limiter.get_efficiency(60)
        assert 0.0 <= efficiency <= 100.0

        efficiency_short = limiter.get_efficiency(1)
        assert efficiency_short >= efficiency


class TestMemoryManagement:
    """Test memory management of historical data."""

    def test_timestamp_cleanup(self) -> None:
        """Test that old timestamps are cleaned up."""
        limiter = RateLimiter(limit=10, track_calls=True, history_window_seconds=1)

        with limiter:
            pass

        initial_timestamps = len(limiter._timestamps)
        assert initial_timestamps == 1

        time.sleep(1.1)

        with limiter:
            pass

        assert len(limiter._timestamps) == 1


class TestBackwardCompatibility:
    """Test that existing functionality remains unchanged."""

    def test_existing_api_unchanged(self) -> None:
        """Test that existing API works without tracking."""
        limiter = RateLimiter(limit=2)

        assert limiter.max_calls_per_second == 2.0
        assert limiter.available_tokens() == 2.0

        assert limiter.try_acquire() is True
        assert limiter.acquire() is True

        with limiter:
            pass

        repr_str = repr(limiter)
        assert "max_calls_per_second=" in repr_str
        assert "bucket_size=2.0" in repr_str

    def test_context_manager_unchanged(self) -> None:
        """Test that context manager behaviour is unchanged when tracking disabled."""
        limiter = RateLimiter(limit=2)

        start_time = time.time()

        with limiter:
            pass
        with limiter:
            pass
        with limiter:
            pass

        elapsed = time.time() - start_time

        assert elapsed >= 0.4
        assert elapsed <= 1.0


class TestThreadSafety:
    """Test thread safety of tracking features."""

    def test_concurrent_tracking(self) -> None:
        """Test concurrent access to tracking features."""
        limiter = RateLimiter(limit=10, track_calls=True)

        def worker() -> None:
            for _ in range(5):
                with limiter:
                    pass
                _ = limiter.call_count
                _ = limiter.stats

        threads = [threading.Thread(target=worker) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert limiter.call_count == 15
        assert limiter.stats.total_calls == 15

    def test_concurrent_windowed_queries(self) -> None:
        """Test concurrent windowed queries."""
        limiter = RateLimiter(limit=10, track_calls=True)

        results = []

        def worker() -> None:
            for _ in range(3):
                with limiter:
                    pass
                results.append(limiter.calls_in_window(60))
                results.append(limiter.get_efficiency(60))

        threads = [threading.Thread(target=worker) for _ in range(2)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert limiter.call_count == 6
        assert len(results) == 12
