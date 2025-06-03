"""
easylimit: A simple, precise Python rate limiter with built-in context manager support.

This package provides a token bucket rate limiter that can be used to limit
the rate of operations (e.g., API calls) to a specified number per second.
"""

from .rate_limiter import CallStats, RateLimiter

__version__ = "0.2.0"
__all__ = ["RateLimiter", "CallStats"]
