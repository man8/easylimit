# Changelog

All notable changes to easylimit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.4] - 2025-11-07

### Fixed
- Fixed call tracking bug where `try_acquire()` and `async_try_acquire()` did not increment `call_count` when `track_calls=True`
- Fixed call tracking bug where `acquire()` did not increment `call_count` when called directly (outside context manager) with `track_calls=True`
- All acquisition methods now consistently track calls when tracking is enabled

### Changed
- Refactored call tracking to be implemented at the internal method level (`_try_consume_one_token_sync`, `_try_acquire_sync`) for cleaner architecture
- Context managers (`__enter__`, `__aenter__`) now delegate tracking to underlying acquisition methods

## [0.3.3] - 2025-11-07

### Added
- Comprehensive community health documentation
  - CONTRIBUTING.md with development guidelines and Conventional Commits spec
  - CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
  - SECURITY.md with vulnerability reporting process
  - GitHub issue templates (bug report, feature request)
  - GitHub pull request template
- Development infrastructure
  - Pre-commit hooks for secret scanning, linting, and formatting
  - Conventional Commits validation
  - SECURITY_SETUP.md guide for GitHub security features
- Repository discoverability improvements
  - Added 8 topics for better GitHub search visibility
  - License and Downloads badges in README

### Changed
- CI/CD workflow optimized: removed redundant integration job
- Branch protection configured with standard rules for open source projects
- Test markers simplified: removed misleading "integration" markers
- Documentation improvements across README, CONTRIBUTING, and CLAUDE.md

### Fixed
- GitHub Actions workflow permissions set explicitly (CodeQL compliance)

### Infrastructure
- First release to PyPI using automated GitHub Actions with Trusted Publishing
- Python 3.13 classifier added to package metadata
- Dynamic versioning configured (single source in __init__.py)

## [0.3.2] - 2025-10-14

### Fixed
- Fixed call tracking bug in `async_acquire()` method where the call count was not being incremented when `track_calls=True`
- Direct `async_acquire()` calls are now properly tracked (context manager usage was already working correctly)

## [0.3.1] - 2025-09-08

### Added
- `limit` parameter now supports float values for precise fractional rates (e.g., `RateLimiter(limit=0.4)` for 0.4 requests/second)
- `initial_tokens` parameter for controlling initial burst behavior
  - Allows setting the number of tokens available at startup (defaults to full bucket)
  - Enables scenarios like gradual startup, controlled bursts, and empty bucket initialization
  - Supports float values for fractional token counts
- Async context manager support with `__aenter__()` and `__aexit__()`
- `async_acquire()` method for non-blocking async token acquisition
- `async_try_acquire()` method for async non-blocking token checks
- Comprehensive examples for new features in `examples/` directory

### Changed
- Thread-safe mixed sync/async usage with unified locking
- Async methods delegate state mutations to background threads via `_to_thread()` helper

## [0.3.0] - 2025-08-10

### Added
- Period-based API using `limit` and `period` parameters (recommended approach)
- Default period of 1 second when omitted for simple usage
- `EASYLIMIT_SUPPRESS_DEPRECATIONS` environment variable to silence deprecation warnings
- Runnable examples in `examples/` directory
- Example smoke tests in test suite

### Changed
- Adopted period-based API as the recommended approach
- Expanded and reorganized test suite
- Updated documentation to reference examples

### Deprecated
- `max_calls_per_second` parameter (still supported with deprecation warning)

### Removed
- Transitional `per_second` classmethod

## [0.2.0] - 2025-06-03

### Added
- Initial public release
- Token bucket rate limiting algorithm
- Context manager support (`with` statement)
- Thread-safe implementation using `threading.RLock()`
- Call tracking capabilities
  - Optional call counting and statistics via `track_calls` parameter
  - Time-windowed call history tracking with `calls_in_window()` method
  - Efficiency metrics via `get_efficiency()` method
  - Delay analysis with `CallStats` dataclass
  - Thread-safe tracking with bounded memory usage
- `RateLimiter.unlimited()` static method for non-limiting instances
  - Maintains full API compatibility for conditional rate limiting
  - Optional call tracking with performance-optimized defaults
- Comprehensive test suite with 26 tests
- Zero runtime dependencies (only Python standard library)
- Support for Python 3.8-3.13
- MIT License
- PyPI distribution

[Unreleased]: https://github.com/man8/easylimit/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/man8/easylimit/releases/tag/v0.3.2
[0.3.1]: https://github.com/man8/easylimit/releases/tag/v0.3.1
[0.3.0]: https://github.com/man8/easylimit/releases/tag/v0.3.0
[0.2.0]: https://github.com/man8/easylimit/releases/tag/v0.2.0
