"""
Smoke tests to run the example scripts to ensure they don't error and print expected markers.
"""

import re
import subprocess
import sys
from pathlib import Path

EX_DIR = Path(__file__).resolve().parent.parent / "examples"


def run_example(script: str) -> str:
    proc = subprocess.run([sys.executable, str(EX_DIR / script)], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def test_period_based_basic_runs() -> None:
    out = run_example("period_based_basic.py")
    assert "outputs= call-0,call-1,call-2" in out


def test_period_based_manual_acquire_runs() -> None:
    out = run_example("period_based_manual_acquire.py")
    assert "acquired= A,B,-" in out
    assert "acquire_with_timeout= False" in out


def test_unlimited_basic_runs() -> None:
    out = run_example("unlimited_basic.py")
    assert "unlimited_ok=True" in out
    assert "tracked_calls= 5" in out


def test_legacy_basic_runs() -> None:
    out = run_example("legacy_basic.py")
    assert "legacy_ok=True" in out


def test_async_demo_runs() -> None:
    out = run_example("async_demo.py")
    assert "Async Rate Limiter Demo" in out
    assert "Fetched item" in out
    assert "Total time:" in out

    # Check that it fetches all 6 items
    for i in range(1, 7):
        assert f"Fetched item {i}" in out
        assert f"completed {i}" in out

    # Verify rate limiting behavior - should take around 3 seconds for 6 calls at 2/second
    # Extract the total time and average rate
    lines = out.split("\n")
    total_time_line = next(line for line in lines if "Total time:" in line)
    avg_rate_line = next(line for line in lines if "Average rate:" in line)

    # Parse total time - should be around 3 seconds (6 calls - 1 initial) / 2 per second
    total_time_match = re.search(r"Total time: ([\d.]+) seconds", total_time_line)
    assert total_time_match, "Could not parse total time"
    total_time = float(total_time_match.group(1))
    assert 2.5 <= total_time <= 3.5, f"Expected total time around 3s, got {total_time}s"

    # Parse average rate - should be around 2 calls per second
    avg_rate_match = re.search(r"Average rate: ([\d.]+) calls per second", avg_rate_line)
    assert avg_rate_match, "Could not parse average rate"
    avg_rate = float(avg_rate_match.group(1))
    assert 1.8 <= avg_rate <= 2.2, f"Expected average rate around 2.0, got {avg_rate}"


def test_initial_tokens_basic_runs() -> None:
    """Test that initial_tokens_basic.py runs without error."""
    out = run_example("initial_tokens_basic.py")
    assert "Initial Tokens Example" in out
    assert "API Client Example" in out

    # Check specific token availability behaviors
    assert "Available tokens: 3.0" in out  # Default behavior (full bucket)
    assert "Can make 3 immediate calls, then rate limited" in out
    assert "Must wait for tokens to accumulate before making calls" in out
    assert "Can make 2 immediate calls, then rate limited" in out

    # Check behavior comparison results
    assert "Call 1: Success" in out
    assert "Call 2: Success" in out
    assert "Call 3: Success" in out
    assert "Call 4: Rate limited" in out

    # Check that empty bucket limiter is initially rate limited
    empty_bucket_section = out[out.find("Empty bucket limiter:") :]
    rate_limited_count = empty_bucket_section[: empty_bucket_section.find("After waiting")].count("Rate limited")
    assert rate_limited_count == 4, f"Expected 4 rate limited calls, got {rate_limited_count}"

    # Check API client behavior - should succeed 10 times then be rate limited
    api_section = out[out.find("API Client Example") :]
    success_count = api_section.count("Success (tokens remaining:")
    rate_limited_api_count = api_section.count("Rate limited")
    assert success_count == 10, f"Expected 10 successful API calls, got {success_count}"
    assert rate_limited_api_count == 5, f"Expected 5 rate limited API calls, got {rate_limited_api_count}"
    assert "Made 10 successful calls out of 15 attempts" in out


def test_initial_tokens_advanced_runs() -> None:
    """Test that initial_tokens_advanced.py runs without error."""
    out = run_example("initial_tokens_advanced.py")
    assert "Gradual Startup Example" in out
    assert "Burst Control Example" in out
    assert "Call Tracking with Initial Tokens" in out
    assert "Fractional Initial Tokens" in out

    # Check gradual startup behavior
    assert "Startup phase: 2/5 requests accepted" in out
    assert "Service protected from overload during startup" in out
    assert "Service now at full capacity" in out

    # Check burst control scenarios with specific results
    burst_scenarios = [
        ("No burst allowed", "0/12"),
        ("Small burst allowed", "2/12"),
        ("Medium burst allowed", "5/12"),
        ("Full burst allowed", "10/12"),
    ]

    for scenario_name, expected_result in burst_scenarios:
        assert f"{scenario_name} (initial_tokens=" in out
        assert f"Immediate requests successful: {expected_result}" in out

    # Check call tracking results
    assert "Total calls: 4" in out
    assert "Efficiency: 100.0%" in out
    assert "Call 1: Completed" in out
    assert "Call 2: Completed" in out
    assert "Call 3: Completed" in out
    assert "Call 4: Completed" in out

    # Check fractional tokens behavior
    assert "Fractional rate limiter: 1.5 requests/second" in out
    assert "First acquisition: Failed (insufficient tokens)" in out
    assert "Second acquisition: Success" in out

    match = re.search(r"Tokens after acquisition: ([\d.]+)", out)
    assert match, "Could not parse final token value after acquisition"
    value = float(match.group(1))
    assert 0.44 <= value <= 0.46, f"Expected ~0.45 tokens remaining, got {value}"
