"""Tests for media_optimizer engine."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from rvp.context import Context
from rvp.engines.media_optimizer import _process_images
from rvp.engines.media_optimizer import _run_optimizer_worker


def test_run_optimizer_worker_success() -> None:
  """Test that _run_optimizer_worker handles successful command execution."""
  path = Path("test.png")
  cmd = ["test_tool", "arg"]

  mock_result = MagicMock()
  mock_result.returncode = 0

  with patch("subprocess.run", return_value=mock_result) as mock_run:
    result_path, success = _run_optimizer_worker(cmd, path)

    assert result_path == path
    assert success is True
    mock_run.assert_called_once_with(
      cmd,
      capture_output=True,
      text=True,
      timeout=30,
      check=False,
    )


def test_run_optimizer_worker_failure() -> None:
  """Test that _run_optimizer_worker handles failed command execution."""
  path = Path("test.png")
  cmd = ["test_tool", "arg"]

  mock_result = MagicMock()
  mock_result.returncode = 1

  with patch("subprocess.run", return_value=mock_result):
    result_path, success = _run_optimizer_worker(cmd, path)

    assert result_path == path
    assert success is False


def test_process_images_calls_worker(tmp_path: Path) -> None:
  """Test that _process_images submits tasks to the executor."""
  work_dir = tmp_path / "work"
  out_dir = tmp_path / "out"
  ctx = Context(
    work_dir=work_dir,
    input_apk=Path("input.apk"),
    output_dir=out_dir,
    engines=["media_optimizer"],
  )
  extract_dir = Path("extract")
  tools = {"optipng": True, "jpegoptim": True}

  # Mock os.walk to return one PNG and one JPG
  with (
    patch("os.walk") as mock_walk,
    patch("rvp.engines.media_optimizer.ProcessPoolExecutor") as mock_executor_cls,
    patch("rvp.engines.media_optimizer.get_optimal_process_workers", return_value=1),
  ):
    mock_walk.return_value = [
      ("extract/res/drawable", [], ["icon.png", "image.jpg"]),
    ]

    mock_executor = MagicMock()
    mock_executor_cls.return_value.__enter__.return_value = mock_executor

    # Mock as_completed to return nothing to avoid hanging
    with patch("rvp.engines.media_optimizer.as_completed", return_value=[]):
      _process_images(ctx, extract_dir, tools)

    # Check if submit was called
    assert mock_executor.submit.call_count == 2

    # Check first call (PNG) - should use optipng by default
    png_call = mock_executor.submit.call_args_list[0]
    assert png_call.args[0] == _run_optimizer_worker
    assert "optipng" in png_call.args[1]
    assert png_call.args[2] == Path("extract/res/drawable/icon.png")

    # Check second call (JPG)
    jpg_call = mock_executor.submit.call_args_list[1]
    assert jpg_call.args[0] == _run_optimizer_worker
    assert "jpegoptim" in jpg_call.args[1]
    assert jpg_call.args[2] == Path("extract/res/drawable/image.jpg")


def test_process_images_pngquant(tmp_path: Path) -> None:
  """Test that _process_images uses pngquant when requested."""
  work_dir = tmp_path / "work"
  out_dir = tmp_path / "out"
  ctx = Context(
    work_dir=work_dir,
    input_apk=Path("input.apk"),
    output_dir=out_dir,
    engines=["media_optimizer"],
    options={"png_optimizer": "pngquant"},
  )
  extract_dir = Path("extract")
  tools = {"pngquant": True, "optipng": True}

  with (
    patch("os.walk") as mock_walk,
    patch("rvp.engines.media_optimizer.ProcessPoolExecutor") as mock_executor_cls,
    patch("rvp.engines.media_optimizer.get_optimal_process_workers", return_value=1),
  ):
    mock_walk.return_value = [
      ("extract/res/drawable", [], ["icon.png"]),
    ]
    mock_executor = MagicMock()
    mock_executor_cls.return_value.__enter__.return_value = mock_executor

    with patch("rvp.engines.media_optimizer.as_completed", return_value=[]):
      _process_images(ctx, extract_dir, tools)

    # Check if submit was called with pngquant
    png_call = mock_executor.submit.call_args_list[0]
    assert "pngquant" in png_call.args[1]


def test_run_optimizer_worker_timeout() -> None:
  """Test that _run_optimizer_worker handles command timeout."""
  path = Path("test.png")
  cmd = ["test_tool", "arg"]

  with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd, 30)):
    result_path, success = _run_optimizer_worker(cmd, path)

    assert result_path == path
    assert success is False


def test_run_optimizer_worker_exception() -> None:
  """Test that _run_optimizer_worker handles general exceptions."""
  path = Path("test.png")
  cmd = ["test_tool", "arg"]

  with patch("subprocess.run", side_effect=RuntimeError("test error")):
    result_path, success = _run_optimizer_worker(cmd, path)

    assert result_path == path
    assert success is False
