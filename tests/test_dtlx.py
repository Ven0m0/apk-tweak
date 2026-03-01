from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from rvp.context import Context
from rvp.engines.dtlx import DEFAULT_OPTIMIZATION_FLAGS
from rvp.engines.dtlx import DTLX_FLAGS
from rvp.engines.dtlx import _build_flags_from_options
from rvp.engines.dtlx import _run_dtlx_analyze
from rvp.engines.dtlx import _run_dtlx_optimize


@pytest.fixture
def mock_ctx(tmp_path):
  ctx = MagicMock(spec=Context)
  ctx.work_dir = tmp_path / "work"
  ctx.output_dir = tmp_path / "output"
  ctx.work_dir.mkdir()
  ctx.output_dir.mkdir()
  ctx.log = MagicMock()
  return ctx


@pytest.fixture
def mock_apk(tmp_path):
  apk = tmp_path / "test.apk"
  apk.touch()
  return apk


@patch("rvp.engines.dtlx._check_dtlx")
@patch("subprocess.run")
def test_run_dtlx_analyze_success(mock_run, mock_check, mock_ctx, mock_apk):
  # Setup mocks
  mock_check.return_value = Path("/usr/bin/dtlx.py")
  mock_run.return_value = MagicMock(returncode=0, stdout="Analysis success", stderr="")

  report_file = mock_ctx.output_dir / "report.txt"

  # Run function
  result = _run_dtlx_analyze(mock_ctx, mock_apk, report_file)

  # Verify assertions
  assert result is True
  mock_run.assert_called_once()
  args = mock_run.call_args[0][0]
  assert args == [sys.executable, "/usr/bin/dtlx.py", str(mock_apk)]
  assert report_file.exists()
  assert "Analysis success" in report_file.read_text()


@patch("rvp.engines.dtlx._check_dtlx")
@patch("subprocess.run")
def test_run_dtlx_analyze_failure(mock_run, mock_check, mock_ctx, mock_apk):
  # Setup mocks
  mock_check.return_value = Path("/usr/bin/dtlx.py")
  mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Analysis failed")

  report_file = mock_ctx.output_dir / "report.txt"

  # Run function
  result = _run_dtlx_analyze(mock_ctx, mock_apk, report_file)

  # Verify assertions
  # _run_dtlx_analyze returns True when the subprocess completes, even on non-zero exit code.
  assert result is True

  assert "COMPLETED WITH WARNINGS" in report_file.read_text()
  assert "Analysis failed" in report_file.read_text()


@patch("rvp.engines.dtlx._check_dtlx")
@patch("subprocess.run")
def test_run_dtlx_analyze_timeout(mock_run, mock_check, mock_ctx, mock_apk):
  mock_check.return_value = Path("/usr/bin/dtlx.py")
  mock_run.side_effect = subprocess.TimeoutExpired(cmd="dtlx", timeout=300)

  report_file = mock_ctx.output_dir / "report.txt"

  result = _run_dtlx_analyze(mock_ctx, mock_apk, report_file)

  assert result is False
  assert "TIMEOUT" in report_file.read_text()


@patch("rvp.engines.dtlx._check_dtlx")
@patch("subprocess.run")
@patch("shutil.copy2")
def test_run_dtlx_optimize_success(mock_copy, mock_run, mock_check, mock_ctx, mock_apk):
  mock_check.return_value = Path("/usr/bin/dtlx.py")
  mock_run.return_value = MagicMock(returncode=0, stdout="Optimization done", stderr="")

  # Simulate patched file creation
  def side_effect_run(*args, **kwargs):
    work_dir = kwargs.get("cwd")
    (work_dir / "test_patched.apk").touch()
    return MagicMock(returncode=0)

  mock_run.side_effect = side_effect_run

  output_apk = mock_ctx.output_dir / "optimized.apk"
  flags = ["--rmads", "--rmtrackers"]

  result = _run_dtlx_optimize(mock_ctx, mock_apk, output_apk, flags)

  assert result is True
  mock_run.assert_called_once()
  # Verify command includes flags and work apk path
  cmd = mock_run.call_args[0][0]
  assert cmd[:2] == [sys.executable, "/usr/bin/dtlx.py"]
  assert cmd[2:4] == flags
  assert cmd[4].endswith("test.apk")

  mock_copy.assert_called()  # Copied to output


@patch("rvp.engines.dtlx._check_dtlx")
@patch("subprocess.run")
def test_run_dtlx_optimize_failure(mock_run, mock_check, mock_ctx, mock_apk):
  mock_check.return_value = Path("/usr/bin/dtlx.py")
  mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

  output_apk = mock_ctx.output_dir / "optimized.apk"
  flags = ["--rmads"]

  result = _run_dtlx_optimize(mock_ctx, mock_apk, output_apk, flags)

  assert result is False

def test_build_flags_from_options_defaults():
  options = {}
  flags = _build_flags_from_options(options)
  expected_flags = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]
  assert flags == expected_flags

def test_build_flags_from_options_specific():
  options = {"rmads1": True, "sslbypass": True}
  flags = _build_flags_from_options(options)
  assert flags == [DTLX_FLAGS["rmads1"], DTLX_FLAGS["sslbypass"]]

def test_build_flags_from_options_falsy():
  options = {"rmads1": False, "sslbypass": False, "rmtrackers": 0, "rmnop": None}
  flags = _build_flags_from_options(options)
  expected_flags = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]
  assert flags == expected_flags

def test_build_flags_from_options_mixed():
  options = {"rmads2": True, "unknown_flag": True, "sslbypass": False, "rmtrackers": True}
  flags = _build_flags_from_options(options)
  assert flags == [DTLX_FLAGS["rmads2"], DTLX_FLAGS["rmtrackers"]]
