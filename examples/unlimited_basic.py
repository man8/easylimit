#!/usr/bin/env python3
"""
Demonstrate RateLimiter.unlimited() with and without tracking.
"""

from easylimit import RateLimiter


def main() -> None:
    # No throttling
    unlimited = RateLimiter.unlimited()
    for _ in range(3):
        with unlimited:
            pass
    print("unlimited_ok=True")

    # With tracking
    tracked = RateLimiter.unlimited(track_calls=True)
    for _ in range(5):
        with tracked:
            pass
    print("tracked_calls=", tracked.call_count)


if __name__ == "__main__":
    main()
