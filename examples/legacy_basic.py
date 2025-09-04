#!/usr/bin/env python3
"""
Legacy API example (deprecated): max_calls_per_second.
"""

import warnings

from easylimit import RateLimiter


def main() -> None:
    with warnings.catch_warnings(record=True) as _w:
        warnings.simplefilter("ignore", DeprecationWarning)
        limiter = RateLimiter(max_calls_per_second=2)
    # Execute a few calls just to show it runs
    for _ in range(2):
        with limiter:
            pass
    print("legacy_ok=True")


if __name__ == "__main__":
    main()
