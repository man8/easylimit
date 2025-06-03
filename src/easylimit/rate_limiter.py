"""
A simple and reliable rate limiter implementation with context manager support.

This module provides a token bucket rate limiter that can be used to limit
the rate of operations (e.g., API calls) to a specified number per second.
"""

import threading
import time
from typing import Optional


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

    def __init__(self, max_calls_per_second: float = 1.0) -> None:
        """
        Initialise the rate limiter.

        Args:
            max_calls_per_second: Maximum number of calls allowed per second

        Raises:
            ValueError: If max_calls_per_second is not positive
        """
        if max_calls_per_second <= 0:
            raise ValueError("max_calls_per_second must be positive")

        self.max_calls_per_second = max_calls_per_second
        self.tokens = max_calls_per_second
        self.last_refill = time.time()
        self.lock = threading.Lock()

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
        self.acquire()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """Context manager exit - nothing to do."""
        pass

    def __repr__(self) -> str:
        """Return string representation of the rate limiter."""
        return f"RateLimiter(max_calls_per_second={self.max_calls_per_second})"
