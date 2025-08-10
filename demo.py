#!/usr/bin/env python3
"""
Demonstration script for easylimit rate limiter.

This script demonstrates both the new period-based API and legacy API.
"""

import time
from datetime import timedelta

from easylimit import RateLimiter


def mock_api_call(call_id: int) -> str:
    """Simulate an API call with some processing time."""
    time.sleep(0.01)
    return f"API response for call {call_id}"


def demo_new_api() -> None:
    """Demonstrate the new period-based API."""
    print("New Period-Based API Demo - 120 calls per minute")
    print("=" * 60)

    limiter = RateLimiter(rate_limit_calls=120, rate_limit_period=timedelta(minutes=1))
    start_time = time.time()

    for i in range(1, 7):
        with limiter:
            result = mock_api_call(i)
            elapsed = time.time() - start_time
            print(f"[{elapsed:.2f}s] {result}")

    total_time = time.time() - start_time
    average_rate = 6 / total_time

    print("=" * 60)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average rate: {average_rate:.2f} calls per second")
    print("✅ New API demonstration complete!")


def demo_legacy_api() -> None:
    """Demonstrate the legacy API (with deprecation warning)."""
    print("\nLegacy API Demo - 2 calls per second (deprecated)")
    print("=" * 60)

    limiter = RateLimiter(max_calls_per_second=2)
    start_time = time.time()

    for i in range(1, 4):
        with limiter:
            result = mock_api_call(i)
            elapsed = time.time() - start_time
            print(f"[{elapsed:.2f}s] {result}")

    total_time = time.time() - start_time
    print("=" * 60)
    print(f"Total time: {total_time:.2f} seconds")
    print("⚠️  Legacy API demonstration complete (with deprecation warning)")


def main() -> None:
    """Run both API demonstrations."""
    demo_new_api()
    demo_legacy_api()


if __name__ == "__main__":
    main()
