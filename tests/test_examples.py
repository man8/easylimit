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
    assert "outputs=" in out


def test_period_based_manual_acquire_runs() -> None:
    out = run_example("period_based_manual_acquire.py")
    assert "acquired=" in out


def test_unlimited_basic_runs() -> None:
    out = run_example("unlimited_basic.py")
    assert "unlimited_ok=True" in out
    assert "tracked_calls=" in out


def test_legacy_basic_runs() -> None:
    out = run_example("legacy_basic.py")
    assert "legacy_ok=True" in out
