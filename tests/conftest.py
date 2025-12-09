"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_apk(tmp_path: Path) -> Path:
  """
  Create a sample APK file for testing.

  Args:
      tmp_path: Pytest temporary directory fixture.

  Returns:
      Path to the created sample APK.
  """
  apk = tmp_path / "sample.apk"
  # Create a minimal ZIP/APK structure
  apk.write_bytes(
    b"PK\x03\x04"  # ZIP signature
    b"\x14\x00\x00\x00\x08\x00"  # Version, flags
    b"\x00" * 50  # Padding
  )
  return apk


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
  """
  Create a work directory for testing.

  Args:
      tmp_path: Pytest temporary directory fixture.

  Returns:
      Path to the created work directory.
  """
  work = tmp_path / "work"
  work.mkdir()
  return work


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
  """
  Create an output directory for testing.

  Args:
      tmp_path: Pytest temporary directory fixture.

  Returns:
      Path to the created output directory.
  """
  output = tmp_path / "output"
  output.mkdir()
  return output
