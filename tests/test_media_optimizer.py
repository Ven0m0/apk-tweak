"""Tests for media_optimizer engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from rvp.engines.media_optimizer import _optimize_png_optipng_worker
from rvp.engines.media_optimizer import _optimize_png_worker


def test_optimize_png_worker_success() -> None:
  """Test PNG optimization worker with successful result."""
  with patch("rvp.engines.media_optimizer.subprocess.run") as mock_run:
    mock_run.return_value = MagicMock(returncode=0)

    png_path = Path("/tmp/test.png")
    result_path, success = _optimize_png_worker(png_path)

    assert result_path == png_path
    assert success is True
    mock_run.assert_called_once()


def test_optimize_png_worker_failure() -> None:
  """Test PNG optimization worker with failed result."""
  with patch("rvp.engines.media_optimizer.subprocess.run") as mock_run:
    mock_run.return_value = MagicMock(returncode=1)

    png_path = Path("/tmp/test.png")
    result_path, success = _optimize_png_worker(png_path)

    assert result_path == png_path
    assert success is False


def test_optimize_png_optipng_worker_success() -> None:
  """Test optipng optimization worker with successful result."""
  with patch("rvp.engines.media_optimizer.subprocess.run") as mock_run:
    mock_run.return_value = MagicMock(returncode=0)

    png_path = Path("/tmp/test.png")
    result_path, success = _optimize_png_optipng_worker(png_path)

    assert result_path == png_path
    assert success is True
    mock_run.assert_called_once()


def test_optimize_png_optipng_worker_custom_level() -> None:
  """Test optipng worker with custom optimization level."""
  with patch("rvp.engines.media_optimizer.subprocess.run") as mock_run:
    mock_run.return_value = MagicMock(returncode=0)

    png_path = Path("/tmp/test.png")
    result_path, success = _optimize_png_optipng_worker(png_path, optimization_level=5)

    assert result_path == png_path
    assert success is True

    # Verify the command includes the correct optimization level
    call_args = mock_run.call_args[0][0]
    assert "-o5" in call_args


def test_optimize_png_optipng_worker_timeout() -> None:
  """Test optipng worker handling timeout."""
  with patch("rvp.engines.media_optimizer.subprocess.run") as mock_run:
    from subprocess import TimeoutExpired

    mock_run.side_effect = TimeoutExpired("optipng", 60)

    png_path = Path("/tmp/test.png")
    result_path, success = _optimize_png_optipng_worker(png_path)

    assert result_path == png_path
    assert success is False
