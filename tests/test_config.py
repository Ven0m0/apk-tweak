"""Tests for the rvp.config module."""

import json
from pathlib import Path
from typing import Any

import pytest

from rvp.config import Config


def test_load_from_file_valid_json(tmp_path: Path) -> None:
  """Test that a valid JSON configuration file is loaded correctly."""
  config_path = tmp_path / "valid_config.json"
  config_data = {
    "output_dir": "test_out",
    "engines": ["test_engine"],
    "revanced_cli_path": "test_cli.jar",
    "revanced_optimize": False,
  }
  with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f)

  config = Config.load_from_file(config_path)

  assert config.output_dir == "test_out"
  assert config.engines == ["test_engine"]
  assert config.revanced_cli_path == "test_cli.jar"
  assert config.revanced_optimize is False
  # Default values should remain
  assert config.dtlx_analyze is False


def test_load_from_file_not_found(tmp_path: Path) -> None:
  """Test that FileNotFoundError is raised when config file doesn't exist."""
  config_path = tmp_path / "nonexistent.json"

  with pytest.raises(FileNotFoundError, match="Config file not found"):
    Config.load_from_file(config_path)


def test_load_from_file_invalid_json(tmp_path: Path) -> None:
  """Test that an error is raised when config file contains invalid JSON."""
  config_path = tmp_path / "invalid.json"
  with open(config_path, "w", encoding="utf-8") as f:
    f.write("{ invalid json")

  # Catch json.decoder.JSONDecodeError or orjson.JSONDecodeError
  expected_exceptions: tuple[type[Exception], ...]
  try:
    import orjson
    expected_exceptions = (json.decoder.JSONDecodeError, orjson.JSONDecodeError)
  except ImportError:
    expected_exceptions = (json.decoder.JSONDecodeError,)

  with pytest.raises(expected_exceptions):
    Config.load_from_file(config_path)
