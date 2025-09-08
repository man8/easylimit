# easylimit

[![Test](https://github.com/man8/easylimit/actions/workflows/test.yml/badge.svg)](https://github.com/man8/easylimit/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/easylimit.svg)](https://badge.fury.io/py/easylimit)
[![Python versions](https://img.shields.io/pypi/pyversions/easylimit.svg)](https://pypi.org/project/easylimit/)

A simple, precise Python rate limiter with built-in context manager support for hassle-free API throttling.

## Features

- **Simple and Intuitive**: Easy-to-use context manager interface
- **Precise Rate Limiting**: Token bucket algorithm ensures accurate timing
- **Burst Control**: Configure initial tokens to control startup burst behaviour
- **Call Tracking**: Optional tracking of calls, delays, and efficiency metrics
- **Thread-Safe**: Safe for use in multi-threaded applications
- **Zero Dependencies**: No runtime dependencies, lightweight and fast
- **Flexible Configuration**: Support for any positive rate (calls per second)
- **Comprehensive Testing**: Extensive test suite with 100% coverage

## Installation

```bash
pip install easylimit
```

## Quick Start

```python
# Simplest: 2 calls per second (defaults to a 1-second period)
from easylimit import RateLimiter

limiter = RateLimiter(limit=2)
with limiter:
    make_api_call()
```

```python
from datetime import timedelta
from easylimit import RateLimiter

# Minimal period-based usage (recommended)
limiter = RateLimiter(limit=120, period=timedelta(minutes=1))
with limiter:
    make_api_call()

# Control initial burst behaviour
controlled_burst = RateLimiter(limit=10, initial_tokens=3)  # Start with 3 tokens instead of 10

# Minimal legacy usage (deprecated)
legacy = RateLimiter(max_calls_per_second=2)

# Unlimited variant
unlimited = RateLimiter.unlimited()
```

## Usage Examples

### Period-Based Rate Limiting (Recommended)

See runnable examples under `examples/`, including:
- `period_based_basic.py`: context manager usage
- `period_based_manual_acquire.py`: manual `try_acquire`/`acquire`
- `unlimited_basic.py`: unlimited limiter, with and without tracking
- `initial_tokens_basic.py`: controlling initial burst behaviour
- `initial_tokens_advanced.py`: advanced initial tokens scenarios
- `legacy_basic.py`: legacy API

### Legacy API Rate Limiting

See `examples/legacy_basic.py`.

### Handling Multiple APIs with Different Limits

See `examples/period_based_basic.py` and `examples/period_based_manual_acquire.py` for similar usage.

### Non-blocking Token Acquisition

See `examples/period_based_manual_acquire.py`.

### Timeout-based Acquisition

See `examples/period_based_manual_acquire.py`.

### Unlimited Rate Limiting

For scenarios where rate limiting is optional or needs to be disabled:

See `examples/unlimited_basic.py`.

### Asynchronous Usage

The rate limiter supports async context managers and async acquisition methods for use in asyncio applications.

See `examples/async_demo.py` for a complete demonstration of async usage patterns.
### Call Tracking and Monitoring

See examples for tracked usage patterns.

See examples for tracking and efficiency calculations.

## API Reference

### RateLimiter

#### Constructor Parameters

- **`limit`**: Maximum number of calls per period (float, required unless using legacy API)
- **`period`**: Time period for the rate limit using timedelta (defaults to 1 second)
- **`initial_tokens`**: Initial number of tokens in the bucket (defaults to `limit` for full bucket)
- **`track_calls`**: Enable call tracking (default: False)
- **`history_window_seconds`**: How long to keep call history for windowed queries (default: 3600)

The `initial_tokens` parameter allows you to control the initial burst behaviour:
- `None` (default): Start with a full bucket (backward compatible)
- `0`: Start with an empty bucket (no initial burst)
- Any value between 0 and `limit`: Start with a specific number of tokens

See `src/easylimit/rate_limiter.py` for full API reference.

#### Static Methods

- **`unlimited(track_calls: bool = False) -> RateLimiter`**

  Create an unlimited rate limiter that performs no rate limiting.

  - `track_calls`: Enable call tracking (default: False for optimal performance)
  - Returns: RateLimiter instance configured for unlimited calls

  This method returns a RateLimiter instance that maintains the same API surface whilst allowing unlimited calls per second. Ideal for conditional rate limiting scenarios.

#### Methods

- **`acquire(timeout: Optional[float] = None) -> bool`**

  Acquire a token, blocking if necessary.

  - `timeout`: Maximum time to wait for a token (None for no timeout)
  - Returns: `True` if token was acquired, `False` if timeout occurred

- **`try_acquire() -> bool`**

  Try to acquire a token without blocking.

  - Returns: `True` if token was acquired, `False` otherwise

- **`async_acquire(timeout: Optional[float] = None) -> bool`**

  Async version of acquire that doesn't block the event loop.

  - `timeout`: Maximum time to wait for a token (None for no timeout)
  - Returns: `True` if token was acquired, `False` if timeout occurred

- **`async_try_acquire() -> bool`**

  Async version of try_acquire.

  - Returns: `True` if token was acquired, `False` otherwise

- **`available_tokens() -> float`**

  Get the current number of available tokens.

  - Returns: Number of tokens currently available

#### Call Tracking Properties (when `track_calls=True`)

- **`call_count -> int`**

  Total number of calls made through this rate limiter.

  - Returns: Total call count
  - Raises: `ValueError` if call tracking is not enabled

- **`stats -> CallStats`**

  Detailed statistics about calls and timing.

  - Returns: `CallStats` object with comprehensive metrics
  - Raises: `ValueError` if call tracking is not enabled

#### Call Tracking Methods (when `track_calls=True`)

- **`reset_call_count() -> None`**

  Reset the call counter and all tracking data to zero.

  - Raises: `ValueError` if call tracking is not enabled

- **`calls_in_window(window_seconds: int) -> int`**

  Return number of calls made in the last N seconds.

  - `window_seconds`: Time window in seconds (must be positive)
  - Returns: Number of calls in the specified window
  - Raises: `ValueError` if call tracking is not enabled or window_seconds is not positive

- **`get_efficiency(window_seconds: int = 60) -> float`**

  Calculate rate limit efficiency as percentage (0.0 to 100.0).

  - `window_seconds`: Time window for efficiency calculation (default: 60)
  - Returns: Efficiency percentage (0.0 = no calls, 100.0 = maximum rate utilisation)
  - Raises: `ValueError` if call tracking is not enabled or window_seconds is not positive

#### Context Manager Support

The `RateLimiter` can be used as both sync and async context manager:

**Synchronous:**
```python
with limiter:
    # This block will only execute after acquiring a token
    make_api_call()
```

**Asynchronous:**
```python
async with limiter:
    # This block will only execute after acquiring a token
    await make_async_api_call()
```

### CallStats

When call tracking is enabled, the `stats` property returns a `CallStats` object:

```python
from easylimit import CallStats

@dataclass
class CallStats:
    """Statistics about rate limiter usage."""
    total_calls: int                    # Total number of calls made
    total_delay_seconds: float          # Cumulative delay time
    average_delay_seconds: float        # Average delay per call
    max_delay_seconds: float            # Maximum delay encountered
    calls_per_second_average: float     # Average call rate
    efficiency_percentage: float        # Rate limit efficiency (0-100%)
    tracking_start_time: datetime       # When tracking began
    last_call_time: Optional[datetime]  # Timestamp of most recent call
```

## How It Works

### Rate Limiting Algorithm

`easylimit` uses a **token bucket algorithm** to provide precise rate limiting:

1. **Token Bucket**: A bucket holds tokens, with a maximum capacity equal to `max_calls_per_second`
2. **Token Refill**: Tokens are added to the bucket at a constant rate over time
3. **Token Consumption**: Each operation consumes one token from the bucket
4. **Rate Limiting**: When the bucket is empty, operations must wait for new tokens

This approach allows for:
- **Burst Handling**: Initial burst of calls up to the bucket capacity
- **Sustained Rate**: Steady rate limiting after the initial burst
- **Precise Timing**: Accurate rate control based on elapsed time

### Call Tracking System

When `track_calls=True`, the rate limiter maintains detailed statistics:

1. **Call Counting**: Each successful token acquisition increments the call counter
2. **Delay Tracking**: Records the time spent waiting for tokens
3. **Timestamp History**: Maintains a sliding window of call timestamps for windowed queries
4. **Memory Management**: Automatically cleans up old timestamps beyond the history window
5. **Thread Safety**: All tracking operations are protected by the same lock as rate limiting

**Efficiency Calculation**: Efficiency is calculated as `(actual_calls / max_possible_calls) * 100%` for a given time window, helping you understand how well you're utilising your rate limit.

## Thread Safety

`easylimit` is fully thread-safe and can be used safely in multi-threaded applications. All operations, including call tracking, are protected by internal locking mechanisms using `threading.RLock()`.

### Thread Safety with asyncio

The rate limiter supports mixed sync and async usage safely. Internal state is protected by a single lock (`threading.RLock`), with async paths delegating state mutations to a background thread via `asyncio.to_thread` to avoid blocking the event loop. This ensures that mixed sync/async usage is safe and consistent.

```python
import threading
from easylimit import RateLimiter

# Thread-safe rate limiting with tracking
limiter = RateLimiter(limit=5, track_calls=True)

def worker(worker_id):
    for i in range(10):
        with limiter:
            # Thread-safe API call with automatic tracking
            make_api_call(f"worker_{worker_id}_call_{i}")

# Create multiple threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

# All tracking data is consistent across threads
print(f"Total calls from all threads: {limiter.call_count}")
print(f"Thread-safe efficiency: {limiter.get_efficiency():.1f}%")
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/man8/easylimit.git
cd easylimit

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create an in-project virtualenv (.venv)
uv venv --python 3.13

# (Optional) activate it; uv run does not require activation
source .venv/bin/activate

# Install dependencies
uv sync --all-extras --dev
```

### Running Tests

```bash
# Run all tests (default)
uv run pytest

# Run only unit tests (skip integration and legacy)
uv run pytest -m 'not integration and not legacy'

# Run only integration tests
uv run pytest -m integration

# Run only legacy tests
uv run pytest -m legacy

# Run with coverage
uv run pytest --cov=easylimit --cov-report=html
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.3.1 (2025-09-08)

- **Feature**: `limit` parameter now supports float values for precise fractional rates
  - Enables direct usage like `RateLimiter(limit=0.4)` for 0.4 requests/second
  - Eliminates need for scaling workarounds (e.g., `limit=4, period=timedelta(seconds=10)`)
  - Maintains full backward compatibility with integer limits
  - All existing functionality and API surface unchanged
- **Feature**: `initial_tokens` parameter for controlling initial burst behaviour
  - Allows setting the number of tokens available at startup (defaults to full bucket)
  - Enables scenarios like gradual startup, controlled bursts, and empty bucket initialisation
  - Supports float values and maintains full backward compatibility
  - Includes comprehensive examples and test coverage
- **Feature**: Added async context manager support
  - Added `async_acquire()` and `async_try_acquire()` methods
  - Added `__aenter__()` and `__aexit__()` for async context manager protocol
  - Thread-safe mixed sync/async usage with unified locking

### 0.3.0 (2025-08-10)

- Adopt period-based API using `limit` and `period` (default period = 1 second when omitted)
- Deprecate `max_calls_per_second` (still supported with warning)
- Add `EASYLIMIT_SUPPRESS_DEPRECATIONS` env var to silence deprecation warnings in tests/scripts
- Remove transitional `per_second` classmethod
- Move runnable examples to `examples/` and reference them from README
- Update and expand test suite, including example smoke tests
### 0.2.0 (2025-06-03)

- Initial release
- Token bucket rate limiting algorithm
- Context manager support
- Thread-safe implementation
- **Call tracking capabilities**
  - Optional call counting and statistics
  - Time-windowed call history tracking
  - Efficiency metrics and delay analysis
  - Thread-safe tracking with bounded memory usage
- **Unlimited rate limiting**
  - `RateLimiter.unlimited()` static method for non-limiting instances
  - Maintains full API compatibility for conditional rate limiting
  - Optional call tracking with performance-optimised defaults
- Comprehensive test suite with 26 tests
- Zero runtime dependencies
For development: run linting and type checks locally using uv as follows: `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy src/`.
