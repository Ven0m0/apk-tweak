"""Input validation and error handling utilities."""

from __future__ import annotations

from pathlib import Path


class ValidationError(Exception):
  """Raised when input validation fails."""


def validate_apk_path(apk: Path) -> None:
  """
  Validate APK file path.

  Args:
      apk: Path to APK file.

  Raises:
      ValidationError: If APK is invalid.
  """
  if not apk.exists():
    raise ValidationError(f"APK file not found: {apk}")

  if not apk.is_file():
    raise ValidationError(f"APK path is not a file: {apk}")

  if apk.suffix.lower() != ".apk":
    raise ValidationError(f"File is not an APK: {apk}")

  if apk.stat().st_size == 0:
    raise ValidationError(f"APK file is empty: {apk}")


def validate_output_dir(output_dir: Path) -> None:
  """
  Validate and prepare output directory.

  Args:
      output_dir: Path to output directory.

  Raises:
      ValidationError: If output directory is invalid.
  """
  if output_dir.exists() and not output_dir.is_dir():
    raise ValidationError(f"Output path exists but is not a directory: {output_dir}")


def validate_engine_names(engines: list[str], available: dict[str, object]) -> list[str]:
  """
  Validate engine names against available engines.

  Args:
      engines: List of engine names to validate.
      available: Dictionary of available engines.

  Returns:
      list[str]: List of unknown engine names (for warnings).
  """
  unknown = [name for name in engines if name not in available]
  return unknown
