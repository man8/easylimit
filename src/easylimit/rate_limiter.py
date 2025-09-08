"""
A simple and reliable rate limiter implementation with context manager support.

This module provides a token bucket rate limiter that can be used to limit
the rate of operations (e.g., API calls) to a specified number of calls in a
given period.
"""

import asyncio
import os
import threading
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, overload


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

    Preferred usage (period-based):
        >>> from datetime import timedelta
        >>> limiter = RateLimiter(limit=120, period=timedelta(minutes=1))
        >>> with limiter:
        ...     # This call will be rate limited
        ...     make_api_call()
    """

    @overload
    def __init__(
        self,
        *,
        max_calls_per_second: float,
        track_calls: bool = False,
        history_window_seconds: int = 3600,
    ) -> None:
        """Deprecated: Use limit and period instead."""
        ...

    @overload
    def __init__(
        self,
        *,
        limit: float,
        period: timedelta,
        track_calls: bool = False,
        history_window_seconds: int = 3600,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        limit: float,
        track_calls: bool = False,
        history_window_seconds: int = 3600,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        track_calls: bool = False,
        history_window_seconds: int = 3600,
    ) -> None: ...

    def __init__(
        self,
        *,
        max_calls_per_second: Optional[float] = None,
        limit: Optional[float] = None,
        period: Optional[timedelta] = None,
        track_calls: bool = False,
        history_window_seconds: int = 3600,
    ) -> None:
        """
        Initialise the rate limiter.

        Args:
            max_calls_per_second: Maximum number of calls allowed per second (deprecated)
            limit: Number of calls allowed in the specified period (recommended)
            period: Time period for the rate limit using timedelta (defaults to 1 second if omitted and limit is provided)
            track_calls: Enable call tracking (default: False)
            history_window_seconds: How long to keep call history for windowed queries

        Raises:
            ValueError: If parameters are invalid or conflicting

        Note:
            Use either max_calls_per_second OR both limit and period.
            The period-based approach is recommended for clarity and precision.
        """
        if max_calls_per_second is not None:
            if limit is not None or period is not None:
                raise ValueError("Cannot specify both max_calls_per_second and limit/period")
            if max_calls_per_second <= 0:
                raise ValueError("max_calls_per_second must be positive")

            if os.getenv("EASYLIMIT_SUPPRESS_DEPRECATIONS", "").lower() not in {"1", "true", "yes"}:
                warnings.warn(
                    "The 'max_calls_per_second' parameter is deprecated. "
                    "Use 'limit' and 'period' instead for better clarity and precision.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            self.max_calls_per_second = max_calls_per_second
            self.bucket_size = max_calls_per_second
        elif limit is not None:
            # Default period to 1 second if not provided. Do not treat zero-duration as falsy here.
            effective_period = period if period is not None else timedelta(seconds=1)
            if limit <= 0:
                raise ValueError("limit must be positive")
            if effective_period.total_seconds() <= 0:
                raise ValueError("period must be positive")

            self.max_calls_per_second = limit / effective_period.total_seconds()
            self.bucket_size = float(limit)
        elif max_calls_per_second is None and limit is None and period is None:
            self.max_calls_per_second = 1.0
            self.bucket_size = 1.0
        else:
            # period provided without limit
            raise ValueError("Must specify limit when providing period, or use max_calls_per_second")

        self.tokens = self.bucket_size
        self.last_refill = time.time()

        self._track_calls = track_calls
        self._history_window = history_window_seconds
        self._call_count = 0
        self._timestamps: List[float] = []
        self._delays: List[float] = []
        self._start_time = datetime.now() if track_calls else None
        self._last_call_time: Optional[datetime] = None
        self.lock = threading.RLock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        if elapsed > 0:
            tokens_to_add = elapsed * self.max_calls_per_second
            new_tokens = self.tokens + tokens_to_add

            # For fractional bucket sizes (< 1.0), allow tokens to accumulate beyond bucket_size
            # to enable token acquisition (which requires at least 1.0 tokens).
            # However, we still respect the rate limit by capping at a reasonable maximum.
            if self.bucket_size < 1.0:
                # Allow accumulation up to at least 1.0, but cap at 2.0 to prevent excessive buildup
                max_tokens = max(1.0, min(2.0, self.bucket_size * 2))
                self.tokens = min(max_tokens, new_tokens)
            else:
                # For bucket sizes >= 1.0, use the original behavior
                self.tokens = min(self.bucket_size, new_tokens)

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
            self._record_call(time.time() - start_time)
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

    @staticmethod
    def unlimited(track_calls: bool = False) -> "RateLimiter":
        """
        Create an unlimited rate limiter that performs no rate limiting.

        This method returns a RateLimiter instance configured to allow unlimited
        calls per second whilst maintaining the same API surface as a regular
        RateLimiter, including context manager support and optional statistics tracking.

        Args:
            track_calls: Enable call tracking (default: False for optimal performance)

        Returns:
            RateLimiter: An unlimited rate limiter instance

        Example:
            >>> unlimited_limiter = RateLimiter.unlimited()
            >>> with unlimited_limiter:
            ...     # This call will not be rate limited
            ...     make_api_call()

            >>> tracked_limiter = RateLimiter.unlimited(track_calls=True)
            >>> with tracked_limiter:
            ...     make_api_call()
            >>> print(f"Calls made: {tracked_limiter.call_count}")
        """
        # Create a valid limiter, then override internals to unlimited
        limiter = RateLimiter(limit=1, period=timedelta(seconds=1), track_calls=track_calls)
        limiter.max_calls_per_second = float("inf")
        limiter.bucket_size = float("inf")
        limiter.tokens = float("inf")
        return limiter

    def _try_consume_one_token_sync(self, start_time: float, timeout: Optional[float]) -> tuple[bool, float, bool]:
        """Try to consume a token under the sync lock; return (acquired, sleep_time, timed_out)."""
        with self.lock:
            self._refill_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True, 0.0, False
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False, 0.0, True
            time_to_wait = (1 - self.tokens) / self.max_calls_per_second
            return False, min(time_to_wait, 0.1), False

    def _try_acquire_sync(self) -> bool:
        """Non-blocking try_acquire under sync lock."""
        with self.lock:
            self._refill_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def _record_call(self, delay: float) -> None:
        """Record tracking info under sync lock."""
        with self.lock:
            self._call_count += 1
            now_ts = time.time()
            self._timestamps.append(now_ts)
            self._delays.append(delay)
            self._last_call_time = datetime.now()
            cutoff_time = now_ts - self._history_window
            self._timestamps = [ts for ts in self._timestamps if ts >= cutoff_time]

    async def async_acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Async version of acquire that doesn't block the event loop.

        Args:
            timeout: Maximum time to wait for a token (None for no timeout)

        Returns:
            True if token was acquired, False if timeout occurred
        """
        start_time = time.time()
        while True:
            acquired, sleep_time, timed_out = await asyncio.to_thread(
                self._try_consume_one_token_sync, start_time, timeout
            )
            if acquired:
                return True
            if timed_out:
                return False
            await asyncio.sleep(sleep_time)

    async def async_try_acquire(self) -> bool:
        """
        Async version of try_acquire.

        Returns:
            True if token was acquired, False otherwise
        """
        return await asyncio.to_thread(self._try_acquire_sync)

    async def __aenter__(self) -> "RateLimiter":
        """Async context manager entry - acquire a token without blocking event loop."""
        start_time = time.time()
        await self.async_acquire()
        if self._track_calls:
            delay = time.time() - start_time
            await asyncio.to_thread(self._record_call, delay)
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]
    ) -> None:
        """Async context manager exit - nothing to do."""
        pass

    def __repr__(self) -> str:
        """Return string representation of the rate limiter."""
        return f"RateLimiter(max_calls_per_second={self.max_calls_per_second}, bucket_size={self.bucket_size})"
