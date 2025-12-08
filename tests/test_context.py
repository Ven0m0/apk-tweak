"""Context dataclass tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from rvp.context import Context


def test_context_initialization(tmp_path: Path) -> None:
  """Test basic context initialization."""
  apk = tmp_path / "test.apk"
  apk.write_text("fake", encoding="utf-8")

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=apk,
    output_dir=tmp_path / "out",
    engines=["revanced"],
  )

  assert ctx.current_apk == apk
  assert ctx.work_dir.exists()
  assert ctx.output_dir.exists()
  assert len(ctx.options) == 0
  assert len(ctx.metadata) == 0


def test_context_set_current_apk_valid(tmp_path: Path) -> None:
  """Test setting valid current APK."""
  apk1 = tmp_path / "test1.apk"
  apk1.write_text("fake1", encoding="utf-8")
  apk2 = tmp_path / "test2.apk"
  apk2.write_text("fake2", encoding="utf-8")

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=apk1,
    output_dir=tmp_path / "out",
    engines=[],
  )

  ctx.set_current_apk(apk2)
  assert ctx.current_apk == apk2


def test_context_set_current_apk_missing(tmp_path: Path) -> None:
  """Test setting missing APK raises error."""
  apk1 = tmp_path / "test1.apk"
  apk1.write_text("fake1", encoding="utf-8")
  apk2 = tmp_path / "missing.apk"

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=apk1,
    output_dir=tmp_path / "out",
    engines=[],
  )

  with pytest.raises(FileNotFoundError, match="APK not found"):
    ctx.set_current_apk(apk2)


def test_context_metadata_storage(tmp_path: Path) -> None:
  """Test metadata dictionary is mutable."""
  apk = tmp_path / "test.apk"
  apk.write_text("fake", encoding="utf-8")

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=apk,
    output_dir=tmp_path / "out",
    engines=[],
  )

  ctx.metadata["test_key"] = "test_value"
  ctx.metadata["nested"] = {"inner": "data"}

  assert ctx.metadata["test_key"] == "test_value"
  assert ctx.metadata["nested"]["inner"] == "data"


def test_context_options_defaults(tmp_path: Path) -> None:
  """Test options dict is initialized empty."""
  apk = tmp_path / "test.apk"
  apk.write_text("fake", encoding="utf-8")

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=apk,
    output_dir=tmp_path / "out",
    engines=[],
  )

  # Options should be empty dict by default
  assert isinstance(ctx.options, dict)
  assert len(ctx.options) == 0

  # Should be mutable
  ctx.options["test"] = True
  assert ctx.options["test"] is True
