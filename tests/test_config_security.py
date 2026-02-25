"""Security tests for configuration loading and environment variable interpolation."""

import json
import os
from pathlib import Path

from rvp.config import Config


def test_interpolate_env_vars(tmp_path: Path) -> None:
  """Test that environment variables are correctly interpolated in config files."""
  config_path = tmp_path / "test_config.json"

  # Set environment variables for testing
  os.environ["TEST_VAR"] = "interpolated_value"
  os.environ["TEST_PASS"] = "secret123"

  config_data = {
    "output_dir": "${TEST_VAR}",
    "revanced_cli_path": "${TEST_PASS}",
    "apktool_path": "${NON_EXISTENT_VAR:-default_val}",
    "zipalign_path": "${ANOTHER_NON_EXISTENT_VAR}",
  }

  with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f)

  # Load config
  cfg = Config.load_from_file(config_path)

  # Verify interpolation
  assert cfg.output_dir == "interpolated_value"
  assert cfg.revanced_cli_path == "secret123"
  assert cfg.apktool_path == "default_val"
  # Should keep the original placeholder if no env var and no default
  assert cfg.zipalign_path == "${ANOTHER_NON_EXISTENT_VAR}"


def test_filter_extra_fields(tmp_path: Path) -> None:
  """Test that extra fields in config JSON do not cause loading to fail."""
  config_path = tmp_path / "extra_fields.json"

  config_data = {
    "description": "Some description",
    "version": "1.0",
    "engines": ["revanced"],
    "unknown_field": "some_value",
    "output_dir": "custom_out",
  }

  with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f)

  # This should NOT raise TypeError
  cfg = Config.load_from_file(config_path)

  assert cfg.output_dir == "custom_out"
  assert cfg.engines == ["revanced"]


def test_modify_pipeline_config_loads() -> None:
  """Test that the updated modify_pipeline.json loads correctly despite extra fields."""
  config_path = Path("config/modify_pipeline.json")

  # Set the environment variable used in the config
  os.environ["MODIFY_KEYSTORE_PASSWORD"] = "test_password"

  # This should NOT raise TypeError and should load correctly
  cfg = Config.load_from_file(config_path)

  assert cfg.engines == ["modify"]
