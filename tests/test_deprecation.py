"""
Test suite for deprecation warnings.
"""

import warnings
from datetime import timedelta

import pytest

from easylimit import RateLimiter


class TestDeprecationWarnings:
    """Test deprecation warnings for the old API."""

    def test_max_calls_per_second_deprecation_warning(self) -> None:
        """Test that using max_calls_per_second triggers a deprecation warning."""
        with pytest.warns(DeprecationWarning, match="The 'max_calls_per_second' parameter is deprecated"):
            limiter = RateLimiter(max_calls_per_second=2.0)
            assert limiter.max_calls_per_second == 2.0

    def test_new_api_no_deprecation_warning(self) -> None:
        """Test that using the new API does not trigger deprecation warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            limiter = RateLimiter(rate_limit_calls=10, rate_limit_period=timedelta(seconds=5))
            assert limiter.max_calls_per_second == 2.0

    def test_default_constructor_no_deprecation_warning(self) -> None:
        """Test that using default constructor does not trigger deprecation warnings."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            limiter = RateLimiter()
            assert limiter.max_calls_per_second == 1.0

    def test_deprecation_warning_message_content(self) -> None:
        """Test the specific content of the deprecation warning message."""
        with pytest.warns(DeprecationWarning) as warning_info:
            RateLimiter(max_calls_per_second=1.5)

        assert len(warning_info) == 1
        warning_message = str(warning_info[0].message)
        assert "max_calls_per_second" in warning_message
        assert "rate_limit_calls" in warning_message
        assert "rate_limit_period" in warning_message
        assert "deprecated" in warning_message

    def test_functionality_unchanged_with_deprecation(self) -> None:
        """Test that functionality remains unchanged despite deprecation warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            limiter = RateLimiter(max_calls_per_second=3.0)

        assert limiter.max_calls_per_second == 3.0
        assert limiter.bucket_size == 3.0
        assert limiter.available_tokens() == 3.0

        assert limiter.try_acquire() is True
        assert abs(limiter.available_tokens() - 2.0) < 0.01
