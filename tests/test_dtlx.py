"""Tests for DTL-X engine."""

from __future__ import annotations

from typing import Any

from rvp.engines.dtlx import DEFAULT_OPTIMIZATION_FLAGS
from rvp.engines.dtlx import DTLX_FLAGS
from rvp.engines.dtlx import _build_flags_from_options


def test_build_flags_empty_options() -> None:
  """Test that empty options return default flags."""
  expected = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]
  assert _build_flags_from_options({}) == expected


def test_build_flags_single_option() -> None:
  """Test that a single known option returns its flag."""
  # Pick a flag that is not in defaults to be sure
  # defaults: rmads4, rmtrackers, rmnop, cleanrun
  # rmads1 is not in defaults
  options = {"rmads1": True}
  assert _build_flags_from_options(options) == ["--rmads1"]


def test_build_flags_multiple_options() -> None:
  """Test that multiple known options return their flags."""
  options = {"rmads1": True, "rmnop": True}
  flags = _build_flags_from_options(options)
  assert "--rmads1" in flags
  assert "--rmnop" in flags
  assert len(flags) == 2


def test_build_flags_false_option() -> None:
  """Test that False options are ignored (and defaults used if result empty)."""
  # If we pass rmads1=False, flags list is empty, so it falls back to defaults
  options = {"rmads1": False}
  expected = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]
  assert _build_flags_from_options(options) == expected


def test_build_flags_mixed_options() -> None:
  """Test that only True options are included."""
  # rmads1=True, rmads2=False
  options = {"rmads1": True, "rmads2": False}
  assert _build_flags_from_options(options) == ["--rmads1"]


def test_build_flags_unknown_option() -> None:
  """Test that unknown options are ignored."""
  # unknown=True -> empty flags -> defaults
  options: dict[str, Any] = {"unknown_flag": True}
  expected = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]
  assert _build_flags_from_options(options) == expected

  # unknown=True, known=True -> known flag only
  options = {"unknown_flag": True, "rmads1": True}
  assert _build_flags_from_options(options) == ["--rmads1"]
