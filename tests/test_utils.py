"""Utility function tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rvp.context import Context
from rvp.utils import run_command


def test_run_command_success(tmp_path: Path) -> None:
    """Test successful command execution."""
    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
    )
    # Write a dummy APK to satisfy context
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Run a simple command
    result = run_command(["echo", "hello"], ctx)

    assert result.returncode == 0


def test_run_command_failure(tmp_path: Path) -> None:
    """Test command failure handling."""
    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
    )
    # Write a dummy APK to satisfy context
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Run a command that will fail
    try:
        run_command(["false"], ctx, check=True)
        assert False, "Should have raised CalledProcessError"
    except subprocess.CalledProcessError:
        pass  # Expected


def test_run_command_no_check(tmp_path: Path) -> None:
    """Test command failure without check."""
    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
    )
    # Write a dummy APK to satisfy context
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Run a command that will fail but don't check
    result = run_command(["false"], ctx, check=False)

    assert result.returncode == 1
