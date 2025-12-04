"""Validator tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from rvp.validators import ValidationError, validate_apk_path, validate_output_dir


def test_validate_apk_path_success(tmp_path: Path) -> None:
  """Test successful APK validation."""
  apk = tmp_path / "test.apk"
  apk.write_text("fake_apk_data", encoding="utf-8")

  # Should not raise
  validate_apk_path(apk)


def test_validate_apk_path_not_found(tmp_path: Path) -> None:
  """Test APK validation with missing file."""
  apk = tmp_path / "missing.apk"

  with pytest.raises(ValidationError, match="not found"):
    validate_apk_path(apk)


def test_validate_apk_path_not_file(tmp_path: Path) -> None:
  """Test APK validation with directory."""
  apk = tmp_path / "test.apk"
  apk.mkdir()

  with pytest.raises(ValidationError, match="not a file"):
    validate_apk_path(apk)


def test_validate_apk_path_wrong_extension(tmp_path: Path) -> None:
  """Test APK validation with wrong extension."""
  apk = tmp_path / "test.txt"
  apk.write_text("data", encoding="utf-8")

  with pytest.raises(ValidationError, match="not an APK"):
    validate_apk_path(apk)


def test_validate_apk_path_empty(tmp_path: Path) -> None:
  """Test APK validation with empty file."""
  apk = tmp_path / "test.apk"
  apk.touch()

  with pytest.raises(ValidationError, match="empty"):
    validate_apk_path(apk)


def test_validate_output_dir_success(tmp_path: Path) -> None:
  """Test successful output directory validation."""
  output_dir = tmp_path / "out"

  # Should not raise
  validate_output_dir(output_dir)


def test_validate_output_dir_exists(tmp_path: Path) -> None:
  """Test output directory validation with existing directory."""
  output_dir = tmp_path / "out"
  output_dir.mkdir()

  # Should not raise
  validate_output_dir(output_dir)


def test_validate_output_dir_not_directory(tmp_path: Path) -> None:
  """Test output directory validation with file."""
  output_dir = tmp_path / "out"
  output_dir.write_text("data", encoding="utf-8")

  with pytest.raises(ValidationError, match="not a directory"):
    validate_output_dir(output_dir)
