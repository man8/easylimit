"""
Advanced example demonstrating initial_tokens with different scenarios.

This example shows more sophisticated use cases for the initial_tokens parameter,
including gradual startup, burst control, and integration with call tracking.
"""

import time
from datetime import timedelta

from easylimit import RateLimiter


def gradual_startup_example():
    """Demonstrate gradual startup pattern using initial_tokens."""

    print("=== Gradual Startup Example ===\n")

    print("Simulating a service with gradual startup:")
    print("- Full capacity: 10 requests/second")
    print("- Startup capacity: 2 requests initially\n")

    service_limiter = RateLimiter(limit=10, period=timedelta(seconds=1), initial_tokens=2, track_calls=True)

    print(f"Initial tokens: {service_limiter.available_tokens()}")

    startup_requests = 5
    successful = 0

    for i in range(startup_requests):
        if service_limiter.try_acquire():
            successful += 1
            print(f"Startup request {i + 1}: Success")
        else:
            print(f"Startup request {i + 1}: Rejected (protecting service)")

    print(f"\nStartup phase: {successful}/{startup_requests} requests accepted")
    print("Service protected from overload during startup\n")

    print("Waiting for service to reach full capacity...")
    time.sleep(1.2)

    print(f"Tokens after warmup: {service_limiter.available_tokens():.1f}")
    print("Service now at full capacity")


def burst_control_example():
    """Demonstrate burst control with different initial_tokens values."""

    print("\n=== Burst Control Example ===\n")

    scenarios = [
        ("No burst allowed", 0),
        ("Small burst allowed", 2),
        ("Medium burst allowed", 5),
        ("Full burst allowed", 10),
    ]

    for description, initial_tokens in scenarios:
        print(f"{description} (initial_tokens={initial_tokens}):")

        limiter = RateLimiter(limit=10, period=timedelta(seconds=1), initial_tokens=initial_tokens)

        successful = 0
        for _ in range(12):
            if limiter.try_acquire():
                successful += 1

        print(f"  Immediate requests successful: {successful}/12")
        print(f"  Remaining tokens: {limiter.available_tokens():.1f}\n")


def tracking_with_initial_tokens():
    """Demonstrate call tracking with initial_tokens."""

    print("=== Call Tracking with Initial Tokens ===\n")

    limiter = RateLimiter(limit=5, period=timedelta(seconds=1), initial_tokens=2, track_calls=True)

    print(f"Limiter created with {limiter.available_tokens()} initial tokens")
    print("Call tracking enabled\n")

    print("Making calls using context manager:")
    for i in range(4):
        try:
            if limiter.acquire(timeout=0.1):
                with limiter:
                    print(f"Call {i + 1}: Completed")
                    time.sleep(0.1)  # Simulate work
            else:
                print(f"Call {i + 1}: Timed out (rate limited)")
        except Exception:
            print(f"Call {i + 1}: Failed to acquire token")

    if limiter.call_count > 0:
        stats = limiter.stats
        print("\nCall Statistics:")
        print(f"  Total calls: {stats.total_calls}")
        print(f"  Average delay: {stats.average_delay_seconds:.3f}s")
        print(f"  Efficiency: {stats.efficiency_percentage:.1f}%")

    print(f"  Current tokens: {limiter.available_tokens():.1f}")


def fractional_tokens_example():
    """Demonstrate initial_tokens with fractional values."""

    print("\n=== Fractional Initial Tokens ===\n")

    limiter = RateLimiter(
        limit=1.5,  # 1.5 requests per second
        period=timedelta(seconds=1),
        initial_tokens=0.7,  # Start with 0.7 tokens
    )

    print("Fractional rate limiter: 1.5 requests/second")
    print(f"Initial tokens: {limiter.available_tokens()}")
    print("\nTrying to acquire tokens:")

    if limiter.try_acquire():
        print("First acquisition: Success")
    else:
        print("First acquisition: Failed (insufficient tokens)")

    print("Waiting for tokens to accumulate...")
    time.sleep(0.5)  # Should add ~0.75 tokens

    print(f"Tokens after wait: {limiter.available_tokens():.2f}")

    if limiter.try_acquire():
        print("Second acquisition: Success")
        print(f"Tokens after acquisition: {limiter.available_tokens():.2f}")
    else:
        print("Second acquisition: Failed")


if __name__ == "__main__":
    gradual_startup_example()
    burst_control_example()
    tracking_with_initial_tokens()
    fractional_tokens_example()
