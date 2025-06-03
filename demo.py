#!/usr/bin/env python3
"""
Demonstration script for easylimit rate limiter.

This script demonstrates the rate limiter limiting API calls to 2 per second.
"""

import time

from easylimit import RateLimiter


def mock_api_call(call_id: int) -> str:
    """Simulate an API call with some processing time."""
    time.sleep(0.01)
    return f"API response for call {call_id}"


def main() -> None:
    """Run the rate limiter demonstration."""
    print("Rate Limiter Demo - 2 calls per second")
    print("=" * 50)

    limiter = RateLimiter(max_calls_per_second=2)
    start_time = time.time()

    for i in range(1, 7):
        with limiter:
            result = mock_api_call(i)
            elapsed = time.time() - start_time
            print(f"[{elapsed:.2f}s] {result}")

    total_time = time.time() - start_time
    average_rate = 6 / total_time

    print("=" * 50)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average rate: {average_rate:.2f} calls per second")
    print("✅ Rate limiting demonstration complete!")


if __name__ == "__main__":
    main()
