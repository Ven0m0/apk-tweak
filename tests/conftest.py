"""Common test fixtures for RVP."""

from __future__ import annotations

from pathlib import Path

import pytest

from rvp.context import Context


@pytest.fixture
def mock_context(tmp_path: Path) -> Context:
  """
  Provide a configured Context object with temporary paths.

  Args:
      tmp_path: Pytest temporary path fixture.

  Returns:
      A Context instance configured for testing.
  """
  work_dir = tmp_path / "work"
  output_dir = tmp_path / "output"
  input_apk = tmp_path / "input.apk"
  input_apk.touch()

  return Context(
    work_dir=work_dir,
    input_apk=input_apk,
    output_dir=output_dir,
    engines=[],
    options={},
  )
