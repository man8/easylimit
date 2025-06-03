"""
A simple and reliable rate limiter implementation with context manager support.

This module provides a token bucket rate limiter that can be used to limit
the rate of operations (e.g., API calls) to a specified number per second.
"""

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CallStats:
    """Statistics about rate limiter usage."""

    total_calls: int
    total_delay_seconds: float
    average_delay_seconds: float
    max_delay_seconds: float
    calls_per_second_average: float
    efficiency_percentage: float
    tracking_start_time: datetime
    last_call_time: Optional[datetime]


class RateLimiter:
    """
    A token bucket rate limiter with context manager support.

    This rate limiter uses a token bucket algorithm to control the rate
    of operations. It's thread-safe and can be used as a context manager.

    Args:
        max_calls_per_second: Maximum number of calls allowed per second

    Example:
        >>> limiter = RateLimiter(max_calls_per_second=2)
        >>> with limiter:
        ...     # This call will be rate limited
        ...     make_api_call()
    """

    def __init__(
        self, max_calls_per_second: float = 1.0, track_calls: bool = False, history_window_seconds: int = 3600
    ) -> None:
        """
        Initialise the rate limiter.

        Args:
            max_calls_per_second: Maximum number of calls allowed per second
            track_calls: Enable call tracking (default: False)
            history_window_seconds: How long to keep call history for windowed queries

        Raises:
            ValueError: If max_calls_per_second is not positive
        """
        if max_calls_per_second <= 0:
            raise ValueError("max_calls_per_second must be positive")

        self.max_calls_per_second = max_calls_per_second
        self.tokens = max_calls_per_second
        self.last_refill = time.time()

        self._track_calls = track_calls
        self._history_window = history_window_seconds
        self._call_count = 0
        self._timestamps = []
        self._delays = []
        self._start_time = datetime.now() if track_calls else None
        self._last_call_time = None
        self.lock = threading.RLock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        if elapsed > 0:
            tokens_to_add = elapsed * self.max_calls_per_second
            self.tokens = min(self.max_calls_per_second, self.tokens + tokens_to_add)
            self.last_refill = now

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token, blocking if necessary.

        Args:
            timeout: Maximum time to wait for a token (None for no timeout)

        Returns:
            True if token was acquired, False if timeout occurred
        """
        start_time = time.time()

        with self.lock:
            while True:
                self._refill_tokens()

                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False

                time_to_wait = (1 - self.tokens) / self.max_calls_per_second
                sleep_time = min(time_to_wait, 0.1)

                self.lock.release()
                try:
                    time.sleep(sleep_time)
                finally:
                    self.lock.acquire()

    def try_acquire(self) -> bool:
        """
        Try to acquire a token without blocking.

        Returns:
            True if token was acquired, False otherwise
        """
        with self.lock:
            self._refill_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def available_tokens(self) -> float:
        """
        Get the current number of available tokens.

        Returns:
            Number of tokens currently available
        """
        with self.lock:
            self._refill_tokens()
            return self.tokens

    def __enter__(self) -> "RateLimiter":
        """Context manager entry - acquire a token."""
        start_time = time.time()
        self.acquire()

        if self._track_calls:
            with self.lock:
                delay = time.time() - start_time
                self._call_count += 1
                self._timestamps.append(time.time())
                self._delays.append(delay)
                self._last_call_time = datetime.now()

                cutoff_time = time.time() - self._history_window
                self._timestamps = [ts for ts in self._timestamps if ts >= cutoff_time]

        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """Context manager exit - nothing to do."""
        pass

    @property
    def call_count(self) -> int:
        """Total number of calls made through this rate limiter."""
        if not self._track_calls:
            raise ValueError("Call tracking is not enabled")
        with self.lock:
            return self._call_count

    @property
    def stats(self) -> CallStats:
        """Detailed statistics about calls and timing."""
        if not self._track_calls:
            raise ValueError("Call tracking is not enabled")

        with self.lock:
            if self._call_count == 0:
                return CallStats(
                    total_calls=0,
                    total_delay_seconds=0.0,
                    average_delay_seconds=0.0,
                    max_delay_seconds=0.0,
                    calls_per_second_average=0.0,
                    efficiency_percentage=0.0,
                    tracking_start_time=self._start_time or datetime.now(),
                    last_call_time=None,
                )

            total_delay = sum(self._delays)
            avg_delay = total_delay / len(self._delays) if self._delays else 0.0
            max_delay = max(self._delays) if self._delays else 0.0

            elapsed_time = (datetime.now() - (self._start_time or datetime.now())).total_seconds()
            calls_per_second = self._call_count / elapsed_time if elapsed_time > 0 else 0.0
            efficiency = (
                (calls_per_second / self.max_calls_per_second) * 100.0 if self.max_calls_per_second > 0 else 0.0
            )

            return CallStats(
                total_calls=self._call_count,
                total_delay_seconds=total_delay,
                average_delay_seconds=avg_delay,
                max_delay_seconds=max_delay,
                calls_per_second_average=calls_per_second,
                efficiency_percentage=min(efficiency, 100.0),
                tracking_start_time=self._start_time or datetime.now(),
                last_call_time=self._last_call_time,
            )

    def reset_call_count(self) -> None:
        """Reset the call counter to zero."""
        if not self._track_calls:
            raise ValueError("Call tracking is not enabled")

        with self.lock:
            self._call_count = 0
            self._timestamps.clear()
            self._delays.clear()
            self._start_time = datetime.now()
            self._last_call_time = None

    def calls_in_window(self, window_seconds: int) -> int:
        """Return number of calls made in the last N seconds."""
        if not self._track_calls:
            raise ValueError("Call tracking is not enabled")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        with self.lock:
            now = time.time()
            cutoff_time = now - window_seconds
            return sum(1 for timestamp in self._timestamps if timestamp >= cutoff_time)

    def get_efficiency(self, window_seconds: int = 60) -> float:
        """Calculate rate limit efficiency as percentage (0.0 to 100.0)."""
        if not self._track_calls:
            raise ValueError("Call tracking is not enabled")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        with self.lock:
            calls_in_period = self.calls_in_window(window_seconds)
            max_possible_calls = self.max_calls_per_second * window_seconds
            return (calls_in_period / max_possible_calls) * 100.0 if max_possible_calls > 0 else 0.0

    def __repr__(self) -> str:
        """Return string representation of the rate limiter."""
        return f"RateLimiter(max_calls_per_second={self.max_calls_per_second})"
