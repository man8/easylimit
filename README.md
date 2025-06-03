# easylimit

[![Test](https://github.com/man8/easylimit/actions/workflows/test.yml/badge.svg)](https://github.com/man8/easylimit/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/easylimit.svg)](https://badge.fury.io/py/easylimit)
[![Python versions](https://img.shields.io/pypi/pyversions/easylimit.svg)](https://pypi.org/project/easylimit/)

A simple, precise Python rate limiter with built-in context manager support for hassle-free API throttling.

## Features

- **Simple and Intuitive**: Easy-to-use context manager interface
- **Precise Rate Limiting**: Token bucket algorithm ensures accurate timing
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
from easylimit import RateLimiter

# Create a rate limiter for 2 calls per second
limiter = RateLimiter(max_calls_per_second=2)

# Use with context manager (recommended)
with limiter:
    make_api_call()

# Or acquire tokens manually
if limiter.try_acquire():
    make_api_call()
```

## Usage Examples

### Basic API Rate Limiting

```python
import requests
from easylimit import RateLimiter

# Limit API calls to 2 per second
api_limiter = RateLimiter(max_calls_per_second=2)

def fetch_user_data(user_id):
    with api_limiter:
        response = requests.get(f"https://api.example.com/users/{user_id}")
        return response.json()

# Make multiple API calls - automatically rate limited
for user_id in range(1, 11):
    user_data = fetch_user_data(user_id)
    print(f"User {user_id}: {user_data['name']}")
```

### Handling Multiple APIs with Different Limits

```python
from easylimit import RateLimiter

# Different rate limits for different APIs
github_limiter = RateLimiter(max_calls_per_second=1)    # 1 call/sec
twitter_limiter = RateLimiter(max_calls_per_second=0.5)  # 1 call every 2 seconds

def fetch_github_data():
    with github_limiter:
        # GitHub API call
        pass

def fetch_twitter_data():
    with twitter_limiter:
        # Twitter API call
        pass
```

### Non-blocking Token Acquisition

```python
from easylimit import RateLimiter

limiter = RateLimiter(max_calls_per_second=1)

# Try to acquire a token without blocking
if limiter.try_acquire():
    print("Token acquired, making API call")
    make_api_call()
else:
    print("Rate limit reached, skipping call")
```

### Timeout-based Acquisition

```python
from easylimit import RateLimiter

limiter = RateLimiter(max_calls_per_second=1)

# Wait up to 5 seconds for a token
if limiter.acquire(timeout=5.0):
    print("Token acquired within timeout")
    make_api_call()
else:
    print("Timeout reached, no token available")
```

## API Reference

### RateLimiter

```python
class RateLimiter:
    def __init__(self, max_calls_per_second: float = 1.0) -> None:
        """
        Initialise the rate limiter.
        
        Args:
            max_calls_per_second: Maximum number of calls allowed per second
            
        Raises:
            ValueError: If max_calls_per_second is not positive
        """
```

#### Methods

- **`acquire(timeout: Optional[float] = None) -> bool`**
  
  Acquire a token, blocking if necessary.
  
  - `timeout`: Maximum time to wait for a token (None for no timeout)
  - Returns: `True` if token was acquired, `False` if timeout occurred

- **`try_acquire() -> bool`**
  
  Try to acquire a token without blocking.
  
  - Returns: `True` if token was acquired, `False` otherwise

- **`available_tokens() -> float`**
  
  Get the current number of available tokens.
  
  - Returns: Number of tokens currently available

#### Context Manager Support

The `RateLimiter` can be used as a context manager:

```python
with limiter:
    # This block will only execute after acquiring a token
    make_api_call()
```

## How It Works

`easylimit` uses a **token bucket algorithm** to provide precise rate limiting:

1. **Token Bucket**: A bucket holds tokens, with a maximum capacity equal to `max_calls_per_second`
2. **Token Refill**: Tokens are added to the bucket at a constant rate over time
3. **Token Consumption**: Each operation consumes one token from the bucket
4. **Rate Limiting**: When the bucket is empty, operations must wait for new tokens

This approach allows for:
- **Burst Handling**: Initial burst of calls up to the bucket capacity
- **Sustained Rate**: Steady rate limiting after the initial burst
- **Precise Timing**: Accurate rate control based on elapsed time

## Thread Safety

`easylimit` is fully thread-safe and can be used safely in multi-threaded applications. All operations are protected by internal locking mechanisms.

```python
import threading
from easylimit import RateLimiter

limiter = RateLimiter(max_calls_per_second=5)

def worker():
    for _ in range(10):
        with limiter:
            # Thread-safe API call
            make_api_call()

# Create multiple threads
threads = [threading.Thread(target=worker) for _ in range(3)]
for thread in threads:
    thread.start()
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/man8/easylimit.git
cd easylimit

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras --dev
```

### Running Tests

```bash
# Run unit tests only (default)
uv run pytest

# Run all tests including integration tests
uv run pytest -m ""

# Run only integration tests
uv run pytest -m integration

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

### 0.1.0 (2025-06-03)

- Initial release
- Token bucket rate limiting algorithm
- Context manager support
- Thread-safe implementation
- Comprehensive test suite
- Zero runtime dependencies
