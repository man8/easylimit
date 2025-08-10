#!/usr/bin/env python3
"""
Example using manual acquire/try_acquire with the period-based API.
"""

import time
from datetime import timedelta

from easylimit import RateLimiter


def main() -> None:
    limiter = RateLimiter(limit=2, period=timedelta(seconds=1))
    acquired = []

    if limiter.try_acquire():
        acquired.append("A")
    if limiter.try_acquire():
        acquired.append("B")
    # Next should fail immediately
    acquired.append("C" if limiter.try_acquire() else "-")

    # Wait a moment, then acquire with timeout
    start = time.time()
    ok = limiter.acquire(timeout=0.2)
    elapsed = time.time() - start
    print("acquired=", ",".join(acquired))
    print("acquire_with_timeout=", ok, "elapsed=", round(elapsed, 2))


if __name__ == "__main__":
    main()
