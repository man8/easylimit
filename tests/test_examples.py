"""
Smoke tests to run the example scripts to ensure they don't error and print expected markers.
"""

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


def test_initial_tokens_basic_runs() -> None:
    """Test that initial_tokens_basic.py runs without error."""
    out = run_example("initial_tokens_basic.py")
    assert "Initial Tokens Example" in out
    assert "API Client Example" in out


def test_initial_tokens_advanced_runs() -> None:
    """Test that initial_tokens_advanced.py runs without error."""
    out = run_example("initial_tokens_advanced.py")
    assert "Gradual Startup Example" in out
    assert "Burst Control Example" in out
    assert "Call Tracking with Initial Tokens" in out
    assert "Fractional Initial Tokens" in out
