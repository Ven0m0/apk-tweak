from pathlib import Path

import pytest

from rvp.context import Context


@pytest.fixture
def mock_context(tmp_path: Path) -> Context:
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
