# Contributing to easylimit

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to easylimit.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to opensource@man8.com.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check [existing issues](https://github.com/man8/easylimit/issues) to avoid duplicates.

When creating a bug report, include:
- Clear and descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- Environment details (Python version, OS, easylimit version)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
- Use a clear and descriptive title
- Provide detailed description of the proposed functionality
- Explain why this enhancement would be useful
- Include examples if applicable

### Pull Requests

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** if you're adding functionality
4. **Ensure all tests pass** by running `uv run pytest`
5. **Run code quality checks** (linting, formatting, type checking)
6. **Update documentation** if needed (README, docstrings, CHANGELOG)
7. **Submit a pull request** with a clear description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/easylimit.git
cd easylimit

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtualenv and install dependencies
uv sync --all-extras --dev

# Activate virtualenv (optional, uv run works without activation)
source .venv/bin/activate
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run only non-legacy tests
uv run pytest -m 'not legacy'

# Run with coverage
uv run pytest --cov=easylimit --cov-report=html

# Run specific test file
uv run pytest tests/test_rate_limiter.py

# Run single test
uv run pytest tests/test_rate_limiter.py::TestRateLimiter::test_basic_rate_limiting
```

## Code Quality Checks

All code must pass these checks before being merged:

```bash
# Lint code (checks for errors and style issues)
uv run ruff check .

# Format code (auto-formats to project style)
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Type check
uv run mypy src/

# Run all checks (what CI runs)
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest
```

## Coding Standards

### Python Style
- **Line length**: 119 characters maximum
- **Quotes**: Double quotes (enforced by ruff format)
- **Indentation**: Spaces, no tabs
- Follow PEP 8 guidelines (enforced by ruff)

### Type Annotations
- All functions must have type annotations
- Use `typing` module for complex types
- Mypy strict mode is enforced:
  - `disallow_untyped_defs=true`
  - No implicit Optional
  - All overloads must be properly typed

### Testing
- Tests live in `tests/` directory
- Use pytest for all tests
- Class-based test organization: `class Test*`
- Use markers for test categories:
  - `@pytest.mark.legacy` - Tests for deprecated API
  - `@pytest.mark.asyncio` - Async tests
- Aim for high test coverage (currently 100%)

### Threading and Async
- All state mutations must be protected by `self._lock`
- Async methods must use `_to_thread()` for state changes
- Never block the event loop in async code
- Release locks during sleeps to prevent deadlocks

### Backwards Compatibility
- Maintain compatibility with Python 3.8+
- Don't break existing API without deprecation cycle
- Use `@overload` for type-safe API variants
- Add `DeprecationWarning` for deprecated features

## Commit Messages

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Please read the [full specification](https://www.conventionalcommits.org/en/v1.0.0/) for details.

### Quick Reference

Format: `<type>[optional scope]: <description>`

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Examples:**
```bash
feat: add exponential backoff support
fix(async): resolve race condition in async_acquire
docs: update README with async examples
feat!: remove deprecated max_calls_per_second parameter  # Breaking change
```

**Guidelines:**
- Use lowercase for type and description
- Keep first line under 72 characters
- Use imperative mood: "add" not "added"
- Reference issues in footer: `Fixes #123`

## Documentation

- Update README.md if adding features or changing behavior
- Add docstrings for public APIs using Google-style format
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
- Add examples in `examples/` directory for significant features
- Keep CLAUDE.md updated with architectural changes

## Version Numbers

**Single source of truth:** `src/easylimit/__init__.py` - `__version__` variable

That's it! The build system automatically reads the version from there. **Do not edit version anywhere else.**

Follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible new features
- PATCH version for backwards-compatible bug fixes

**To release a new version:**
1. Update `__version__` in `src/easylimit/__init__.py`
2. Update `CHANGELOG.md` with changes
3. Build and publish: `uv build && uv publish`

## Testing on Multiple Python Versions

CI tests on Python 3.8-3.13. If you want to test locally:

```bash
# Using pyenv to test multiple versions
pyenv install 3.8.18 3.9.18 3.10.13 3.11.9 3.12.7 3.13.2
pyenv local 3.8.18 3.9.18 3.10.13 3.11.9 3.12.7 3.13.2

# Run tests on each version
for version in 3.8 3.9 3.10 3.11 3.12 3.13; do
  echo "Testing Python $version"
  uv run --python $version pytest
done
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to:
- Open an issue with your question
- Start a discussion in GitHub Discussions
- Reach out to the maintainers at opensource@man8.com

Thank you for contributing! 🎉
