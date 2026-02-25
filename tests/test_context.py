"""Tests for the Context class."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from rvp.context import Context


def test_context_initialization(tmp_path: Path) -> None:
  """Test that Context correctly initializes state."""
  work_dir = tmp_path / "work"
  output_dir = tmp_path / "output"
  input_apk = tmp_path / "input.apk"
  input_apk.touch()

  # We use autospec=True to ensure that the instance (self) is passed to mock
  with patch.object(Path, "mkdir", autospec=True) as mock_mkdir:
    ctx = Context(
      work_dir=work_dir,
      input_apk=input_apk,
      output_dir=output_dir,
      engines=["revanced"],
    )

    # Verify current_apk is set
    assert ctx.current_apk == input_apk

    # Verify mkdir was called for both directories
    assert mock_mkdir.call_count == 2
    # Verify it was called on the correct paths with correct arguments
    mock_mkdir.assert_any_call(work_dir, parents=True, exist_ok=True)
    mock_mkdir.assert_any_call(output_dir, parents=True, exist_ok=True)


def test_context_directory_creation(tmp_path: Path) -> None:
  """Test that Context actually creates the directories on the filesystem."""
  work_dir = tmp_path / "work"
  output_dir = tmp_path / "output"
  input_apk = tmp_path / "input.apk"
  input_apk.touch()

  assert not work_dir.exists()
  assert not output_dir.exists()

  Context(
    work_dir=work_dir, input_apk=input_apk, output_dir=output_dir, engines=["revanced"]
  )

  assert work_dir.exists()
  assert output_dir.exists()


def test_context_directory_already_exists(tmp_path: Path) -> None:
  """Test that Context doesn't fail if directories already exist."""
  work_dir = tmp_path / "work"
  output_dir = tmp_path / "output"
  input_apk = tmp_path / "input.apk"
  input_apk.touch()

  work_dir.mkdir()
  output_dir.mkdir()

  # This should not raise an exception because of exist_ok=True
  Context(
    work_dir=work_dir, input_apk=input_apk, output_dir=output_dir, engines=["revanced"]
  )

  assert work_dir.exists()
  assert output_dir.exists()
