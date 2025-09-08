"""
Basic example demonstrating the initial_tokens parameter.

This example shows how to control the initial burst behaviour of a rate limiter
by setting the number of tokens available at startup.
"""

import time
from datetime import timedelta

from easylimit import RateLimiter


def demonstrate_initial_tokens():
    """Demonstrate different initial_tokens configurations."""

    print("=== Initial Tokens Example ===\n")

    print("1. Default behaviour (full bucket):")
    limiter_default = RateLimiter(limit=3, period=timedelta(seconds=1))
    print(f"   Available tokens: {limiter_default.available_tokens()}")
    print("   Can make 3 immediate calls, then rate limited\n")

    print("2. Empty bucket (no initial burst):")
    limiter_empty = RateLimiter(limit=3, period=timedelta(seconds=1), initial_tokens=0)
    print(f"   Available tokens: {limiter_empty.available_tokens()}")
    print("   Must wait for tokens to accumulate before making calls\n")

    print("3. Partial bucket (controlled burst):")
    limiter_partial = RateLimiter(limit=5, period=timedelta(seconds=1), initial_tokens=2)
    print(f"   Available tokens: {limiter_partial.available_tokens()}")
    print("   Can make 2 immediate calls, then rate limited\n")

    print("4. Behaviour comparison:")

    limiter_full = RateLimiter(limit=3, period=timedelta(seconds=1), initial_tokens=3)

    limiter_empty = RateLimiter(limit=3, period=timedelta(seconds=1), initial_tokens=0)

    print("   Full bucket limiter:")
    for i in range(4):
        if limiter_full.try_acquire():
            print(f"     Call {i + 1}: Success")
        else:
            print(f"     Call {i + 1}: Rate limited")

    print("\n   Empty bucket limiter:")
    for i in range(4):
        if limiter_empty.try_acquire():
            print(f"     Call {i + 1}: Success")
        else:
            print(f"     Call {i + 1}: Rate limited")

    print("\n   After waiting 1 second...")
    time.sleep(1.1)

    print("   Empty bucket limiter now has tokens:")
    for i in range(2):
        if limiter_empty.try_acquire():
            print(f"     Call {i + 1}: Success")
        else:
            print(f"     Call {i + 1}: Rate limited")


def api_client_example():
    """Example of using initial_tokens for API client rate limiting."""

    print("\n=== API Client Example ===\n")

    api_limiter = RateLimiter(limit=100, period=timedelta(minutes=1), initial_tokens=10)

    print(f"API rate limiter initialised with {api_limiter.available_tokens()} tokens")
    print("This allows 10 immediate API calls, then sustained rate of 100/minute\n")

    successful_calls = 0
    for i in range(15):
        if api_limiter.try_acquire():
            successful_calls += 1
            print(f"API call {i + 1}: Success (tokens remaining: {api_limiter.available_tokens():.1f})")
        else:
            print(f"API call {i + 1}: Rate limited")

    print(f"\nMade {successful_calls} successful calls out of 15 attempts")
    print("The remaining calls would need to wait for tokens to refill")


if __name__ == "__main__":
    demonstrate_initial_tokens()
    api_client_example()
