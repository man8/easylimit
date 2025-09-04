#!/usr/bin/env python3
"""
Basic example using the period-based API with context manager.
"""

import time
from datetime import timedelta

from easylimit import RateLimiter


def main() -> None:
    limiter = RateLimiter(limit=120, period=timedelta(minutes=1))
    start = time.time()
    outputs = []
    for i in range(3):
        with limiter:
            outputs.append(f"call-{i}")
    elapsed = time.time() - start
    print("elapsed=", round(elapsed, 3))
    print("outputs=", ",".join(outputs))


if __name__ == "__main__":
    main()
