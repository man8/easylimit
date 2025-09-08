#!/usr/bin/env python3
"""
Demonstration script for async usage of easylimit.
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from easylimit import RateLimiter


async def fetch(i: int) -> None:
    """Simulate an async IO operation."""
    await asyncio.sleep(0.01)
    print(f"Fetched item {i}")


async def main() -> None:
    """Run the async rate limiter demonstration."""
    print("Async Rate Limiter Demo - 2 calls per second")
    print("=" * 50)

    limiter = RateLimiter(limit=2)
    t0 = time.time()

    for i in range(1, 7):
        async with limiter:
            await fetch(i)
            elapsed = time.time() - t0
            print(f"[{elapsed:.2f}s] completed {i}")

    total_time = time.time() - t0
    average_rate = 6 / total_time

    print("=" * 50)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average rate: {average_rate:.2f} calls per second")
    print("✅ Async rate limiting demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
