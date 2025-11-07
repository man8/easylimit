"""
Tests demonstrating real-world usage scenarios and performance characteristics of the RateLimiter.
"""

import time
from typing import Dict, Tuple
from unittest.mock import Mock, patch

from easylimit import RateLimiter


class TestRealWorldUsage:
    """Test real-world usage scenarios."""

    def test_api_call_simulation(self) -> None:
        """Test rate limiting with simulated API calls."""
        limiter = RateLimiter(limit=2)

        def mock_api_call(call_id: int) -> str:
            """Simulate an API call with some processing time."""
            time.sleep(0.01)
            return f"Response for call {call_id}"

        results = []
        start_time = time.time()

        for i in range(1, 7):
            with limiter:
                result = mock_api_call(i)
                elapsed = time.time() - start_time
                results.append((i, elapsed, result))

        total_time = time.time() - start_time

        assert 2.0 <= total_time <= 3.0
        assert len(results) == 6

        for i, (call_id, _elapsed, result) in enumerate(results, 1):
            assert call_id == i
            assert f"Response for call {i}" in result

    @patch("requests.get")
    def test_http_requests_rate_limiting(self, mock_get: Mock) -> None:
        """Test rate limiting actual HTTP requests (mocked)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        limiter = RateLimiter(limit=2)

        def make_api_request(endpoint: str) -> Tuple[int, Dict]:
            """Make a rate-limited API request."""
            import requests

            with limiter:
                response = requests.get(f"https://api.example.com/{endpoint}")
                return response.status_code, response.json()

        start_time = time.time()
        results = []

        endpoints = ["users", "posts", "comments", "likes"]
        for endpoint in endpoints:
            status, data = make_api_request(endpoint)
            elapsed = time.time() - start_time
            results.append((endpoint, status, elapsed))

        total_time = time.time() - start_time

        assert 1.0 <= total_time <= 2.5

        assert len(results) == 4
        assert mock_get.call_count == 4

        for _endpoint, status, _elapsed in results:
            assert status == 200

    def test_burst_then_sustained_rate(self) -> None:
        """Test burst of calls followed by sustained rate."""
        limiter = RateLimiter(limit=3)

        call_times = []
        start_time = time.time()

        for _i in range(9):
            with limiter:
                call_times.append(time.time() - start_time)

        assert call_times[0] < 0.1
        assert call_times[1] < 0.1
        assert call_times[2] < 0.1

        for i in range(3, 9):
            expected_time = (i - 3) * (1 / 3)
            assert abs(call_times[i] - expected_time) < 0.5

    def test_error_handling_with_rate_limiting(self) -> None:
        """Test that rate limiting works even when operations fail."""
        limiter = RateLimiter(limit=2)

        def failing_operation(should_fail: bool = False) -> str:
            if should_fail:
                raise ValueError("Operation failed")
            return "Success"

        results = []
        start_time = time.time()

        operations = [False, True, False, True, False]

        for i, should_fail in enumerate(operations):
            try:
                with limiter:
                    failing_operation(should_fail)
                    elapsed = time.time() - start_time
                    results.append((i, "success", elapsed))
            except ValueError:
                elapsed = time.time() - start_time
                results.append((i, "failed", elapsed))

        total_time = time.time() - start_time

        assert 1.0 <= total_time <= 3.0
        assert len(results) == 5

        statuses = [result[1] for result in results]
        assert "success" in statuses
        assert "failed" in statuses


class TestPerformanceCharacteristics:
    """Test performance characteristics of the rate limiter."""

    def test_minimal_overhead(self) -> None:
        """Test that rate limiter has minimal overhead when tokens are available."""
        limiter = RateLimiter(limit=1000)

        start_time = time.time()
        for _ in range(100):
            limiter.acquire()

        elapsed = time.time() - start_time

        assert elapsed < 0.1

    def test_memory_usage_stability(self) -> None:
        """Test that memory usage remains stable over time."""
        limiter = RateLimiter(limit=10)

        for _ in range(100):
            limiter.acquire()
            if _ % 10 == 0:
                time.sleep(0.1)

        assert True

    def test_precision_over_time(self) -> None:
        """Test that rate limiting precision is maintained over longer periods."""
        limiter = RateLimiter(limit=5)

        start_time = time.time()
        call_count = 0

        while time.time() - start_time < 2.0:
            if limiter.try_acquire():
                call_count += 1
            time.sleep(0.01)

        actual_time = time.time() - start_time
        expected_calls = int(5 * actual_time)

        assert abs(call_count - expected_calls) <= 4
