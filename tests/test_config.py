"""Configuration loading tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rvp.config import Config


def test_config_defaults() -> None:
  """Test default configuration values."""
  cfg = Config()

  assert cfg.output_dir == "out"
  assert cfg.engines == ["revanced"]
  assert cfg.dtlx_analyze is False
  assert cfg.dtlx_optimize is False
  assert cfg.revanced_optimize is True
  assert cfg.revanced_debloat is True


def test_config_load_from_valid_file(tmp_path: Path) -> None:
  """Test loading valid configuration file."""
  config_file = tmp_path / "config.json"
  config_data = {
    "input_apk": "test.apk",
    "output_dir": "custom_out",
    "engines": ["revanced", "dtlx"],
    "dtlx_analyze": True,
  }
  config_file.write_text(json.dumps(config_data), encoding="utf-8")

  cfg = Config.load_from_file(config_file)

  assert cfg.input_apk == "test.apk"
  assert cfg.output_dir == "custom_out"
  assert cfg.engines == ["revanced", "dtlx"]
  assert cfg.dtlx_analyze is True


def test_config_load_missing_file(tmp_path: Path) -> None:
  """Test loading missing config file raises error."""
  config_file = tmp_path / "missing.json"

  with pytest.raises(FileNotFoundError, match="Config file not found"):
    Config.load_from_file(config_file)


def test_config_load_invalid_json(tmp_path: Path) -> None:
  """Test loading invalid JSON raises error."""
  config_file = tmp_path / "invalid.json"
  config_file.write_text("{ invalid json", encoding="utf-8")

  with pytest.raises(json.JSONDecodeError):
    Config.load_from_file(config_file)


def test_config_partial_options(tmp_path: Path) -> None:
  """Test loading config with partial options uses defaults."""
  config_file = tmp_path / "partial.json"
  config_data = {
    "input_apk": "test.apk",
    # Other fields should use defaults
  }
  config_file.write_text(json.dumps(config_data), encoding="utf-8")

  cfg = Config.load_from_file(config_file)

  assert cfg.input_apk == "test.apk"
  assert cfg.output_dir == "out"  # Default
  assert cfg.engines == ["revanced"]  # Default


def test_config_empty_file(tmp_path: Path) -> None:
  """Test loading empty config file."""
  config_file = tmp_path / "empty.json"
  config_file.write_text("{}", encoding="utf-8")

  cfg = Config.load_from_file(config_file)

  # Should have all defaults
  assert cfg.input_apk is None
  assert cfg.output_dir == "out"
  assert cfg.engines == ["revanced"]
