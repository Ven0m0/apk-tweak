import subprocess
from unittest.mock import MagicMock

import pytest

from rvp.context import Context
from rvp.utils import run_command


@pytest.fixture
def mock_context():
  ctx = MagicMock(spec=Context)
  ctx.log = MagicMock()
  return ctx


def test_run_command_success(mock_context):
  """Test successful command execution."""
  cmd = ["echo", "test_output"]
  result = run_command(cmd, mock_context, check=True)

  assert result.returncode == 0
  # Verify that 'test_output' was logged.
  # The exact log message format depends on implementation, but it should contain the output.
  # Check if any call to log contained 'test_output'
  found = any("test_output" in call.args[0] for call in mock_context.log.call_args_list)
  assert found, "Output not logged"


def test_run_command_timeout(mock_context):
  """Test command timeout."""
  # Use sleep to simulate a long running process
  cmd = ["sleep", "2"]

  with pytest.raises(subprocess.TimeoutExpired):
    run_command(cmd, mock_context, timeout=1, check=True)


def test_run_command_failure(mock_context):
  """Test command failure."""
  cmd = ["false"]  # Returns non-zero exit code

  with pytest.raises(subprocess.CalledProcessError):
    run_command(cmd, mock_context, check=True)


def test_run_command_failure_no_check(mock_context):
  """Test command failure with check=False."""
  cmd = ["false"]
  result = run_command(cmd, mock_context, check=False)
  assert result.returncode != 0


def test_require_input_apk_success(mock_context):
  """Test require_input_apk successfully returns the APK."""
  from pathlib import Path

  from rvp.utils import require_input_apk

  # Test with current_apk set
  mock_context.current_apk = Path("current.apk")
  mock_context.input_apk = Path("input.apk")
  assert require_input_apk(mock_context) == Path("current.apk")

  # Test with current_apk missing, but input_apk set
  mock_context.current_apk = None
  mock_context.input_apk = Path("input.apk")
  assert require_input_apk(mock_context) == Path("input.apk")


def test_require_input_apk_missing(mock_context):
  """Test require_input_apk raises ValueError when no APK is found."""
  from rvp.utils import require_input_apk

  mock_context.current_apk = None
  mock_context.input_apk = None

  with pytest.raises(ValueError, match="No input APK found in context"):
    require_input_apk(mock_context)
