# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

easylimit is a lightweight Python rate limiter library using a token bucket algorithm with context manager support. It has zero runtime dependencies and supports both synchronous and asynchronous usage patterns. Python 3.8-3.13 compatible.

## Development Environment

### Setup
```bash
# Tool versions (see .tool-versions)
python 3.13.2
uv 0.7.9

# Install dependencies
uv sync --all-extras --dev
```

## Common Commands

### Testing
```bash
# Run all tests
uv run pytest

# Non-legacy tests only
uv run pytest -m 'not legacy'

# Run with coverage
uv run pytest --cov=easylimit --cov-report=html

# Run specific test markers
uv run pytest -m legacy
uv run pytest -m asyncio

# Run single test file
uv run pytest tests/test_rate_limiter.py

# Run single test
uv run pytest tests/test_rate_limiter.py::TestRateLimiter::test_basic_rate_limiting
```

### Code Quality
```bash
# Lint (check)
uv run ruff check .

# Format code
uv run ruff format .

# Check formatting without modifying
uv run ruff format --check .

# Type check
uv run mypy src/

# Run all quality checks (what CI runs)
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest
```

### Building
```bash
# Build package
uv build

# Clean build artifacts
rm -rf dist/ build/ src/*.egg-info
```

## Architecture

### Token Bucket Algorithm

The core rate limiter uses a token bucket algorithm implemented in `src/easylimit/rate_limiter.py`:

1. **Bucket holds tokens** with max capacity = `bucket_size` (equals `limit` parameter)
2. **Tokens refill continuously** at rate = `limit / period.total_seconds()`
3. **Each operation consumes 1 token** from the bucket
4. **Operations block/wait** when bucket is empty until tokens refill

Key implementation details:
- `_refill_tokens()`: Calculates elapsed time and adds tokens proportionally
- For fractional buckets (< 1.0), allows accumulation up to 2.0 to enable acquisition
- Uses `threading.RLock()` for thread-safe state management

### Synchronous vs Asynchronous Support

**Sync API:**
- `acquire(timeout)`: Blocking acquisition with optional timeout
- `try_acquire()`: Non-blocking check-only
- `with limiter:` context manager

**Async API:**
- `async_acquire(timeout)`: Non-blocking async acquisition
- `async_try_acquire()`: Non-blocking async check
- `async with limiter:` context manager

**Threading Model:**
- Uses `threading.RLock()` to protect all state access
- Async methods delegate state mutations to background threads via `_to_thread()` helper
- `_to_thread()` uses `asyncio.to_thread()` on Python 3.9+, falls back to `run_in_executor()` on 3.8
- Lock is released during sleeps to prevent thread starvation
- Fully thread-safe for mixed sync/async usage in same program

### Constructor API Variants

Multiple constructor signatures for backwards compatibility:

1. **Period-based (recommended):** `RateLimiter(limit=120, period=timedelta(minutes=1))`
2. **Simple (defaults to 1 second):** `RateLimiter(limit=2)`
3. **Legacy (deprecated):** `RateLimiter(max_calls_per_second=2)`
4. **Unlimited:** `RateLimiter.unlimited()`

**Special parameters:**
- `initial_tokens`: Control startup burst behavior (0 to limit, defaults to full bucket)
- `track_calls`: Enable call tracking (default: False for performance)
- `history_window_seconds`: Sliding window for call history (default: 3600)

### Call Tracking System

When `track_calls=True`, the limiter maintains:
- `_timestamps`: Sliding window of call timestamps (auto-trimmed)
- `_delays`: Wait times for each call
- `_call_count`: Total calls made
- `_last_call_time`: Most recent acquisition

Access via: `call_count`, `stats`, `calls_in_window(seconds)`, `get_efficiency(window_seconds)`

## Code Standards

### Commit Messages
- **MUST follow [Conventional Commits](https://www.conventionalcommits.org/)** specification
- Format: `<type>[optional scope]: <description>`
- Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- Breaking changes: Add `!` after type or `BREAKING CHANGE:` in footer
- Examples:
  - `feat: add exponential backoff support`
  - `fix(async): resolve race condition in async_acquire`
  - `feat!: remove deprecated max_calls_per_second parameter`
- See CONTRIBUTING.md for full guidelines
- Pre-commit hook validates commit messages automatically

### Style
- **Line length:** 119 characters (enforced by ruff)
- **Quotes:** Double quotes (ruff format)
- **Indentation:** Spaces, no magic trailing comma

### Type Checking
- **Strict mypy mode** enforced (see pyproject.toml)
- All functions must have type annotations (`disallow_untyped_defs=true`)
- No implicit Optional allowed
- Use `@overload` for multiple constructor signatures

### Testing
- Tests live in `tests/` directory
- Use pytest markers: `@pytest.mark.legacy`, `@pytest.mark.asyncio`
- Class-based organization: `class Test*` groups related tests
- CI runs tests on Python 3.8-3.13

## Key Development Patterns

### Deprecation Management
- Legacy `max_calls_per_second` API still supported but shows `DeprecationWarning`
- Suppress warnings with `EASYLIMIT_SUPPRESS_DEPRECATIONS=1` environment variable
- Tests use this env var to avoid noise in test output

### Backwards Compatibility
- Use `@overload` decorators for type-safe API variants
- All new features must maintain compatibility with Python 3.8+
- CI runs full test suite on all supported Python versions

### Float Limit Support
- `limit` parameter accepts both int and float (as of v0.3.1)
- Fractional rates like `limit=0.4` work correctly (0.4 requests/second)
- For buckets < 1.0, tokens accumulate beyond bucket_size (up to 2.0) to enable acquisition

### Thread Safety
- Always acquire lock before accessing/modifying state
- Release lock during sleeps to prevent deadlocks
- Async paths must use `_to_thread()` wrapper for state mutations

## Important Notes

### Recent Bug Fixes
- **v0.3.2:** Fixed `async_acquire()` not incrementing call count when `track_calls=True`
- The fix ensures `_record_call()` is called after successful async acquisition

### Version Numbers
- **Single source of truth:** `src/easylimit/__init__.py` - `__version__` variable
- `pyproject.toml` uses dynamic versioning (hatchling) to read from `__init__.py`
- When releasing: Update only `__init__.py`, build system reads it automatically

### Zero Dependencies
- No runtime dependencies - only uses Python standard library
- Dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff, mypy
- Keep it dependency-free to maintain simplicity and security

## Testing Strategy

### Test Organization
12 test modules covering:
- `test_rate_limiter.py`: Basic functionality
- `test_async_rate_limiter.py`: Async API
- `test_call_tracking.py`: Call tracking features
- `test_direct_acquire_tracking.py`: Direct acquire call tracking
- `test_initial_tokens.py`: Initial tokens parameter
- `test_float_limit.py`: Float limit support
- `test_period_based_api.py`: Period-based API
- `test_legacy_api.py`: Deprecated API
- `test_integration.py`: Real-world usage scenarios and performance tests
- `test_deprecation.py`: Deprecation warnings
- `test_mixed_sync_async.py`: Mixed sync/async usage
- `test_examples.py`: Smoke tests of example scripts

### CI/CD Pipeline
- **Test job:** Runs on Python 3.8-3.13 (lint, type check, all tests)

## Community & Contribution

### Pre-commit Hooks
Pre-commit hooks are configured for security and code quality:
```bash
# Install pre-commit tool
uv tool install pre-commit

# Install hooks into git (run once)
pre-commit install
pre-commit install --hook-type commit-msg

# Hooks will run automatically on git commit
# To run manually on all files:
pre-commit run --all-files
```

Hooks include:
- TruffleHog secret scanning
- Ruff linting and formatting
- Conventional Commits validation
- File quality checks (trailing whitespace, large files, etc.)

### Community Files
- **CONTRIBUTING.md** - Contribution guidelines and development setup
- **CODE_OF_CONDUCT.md** - Contributor Covenant v2.1
- **SECURITY.md** - Security vulnerability reporting
- **CHANGELOG.md** - Version history following Keep a Changelog format

### Contact Information
- **Package author:** Louis Mandelstam <louis@man8.com> (PyPI attribution)
- **Project contact:** opensource@man8.com (security reports, conduct violations, questions)
- See SECURITY.md for vulnerability reporting process
