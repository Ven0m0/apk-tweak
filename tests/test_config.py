import json
from pathlib import Path

from rvp.config import Config


def test_save_to_file(tmp_path: Path) -> None:
  """Test that configuration is correctly serialized to JSON."""
  config_path = tmp_path / "test_config_save.json"

  # Create a config instance
  cfg = Config(
    input_apk="input.apk",
    output_dir="custom_out",
    engines=["revanced", "dtlx"],
    revanced_cli_path="custom-cli.jar",
    dtlx_analyze=True,
  )

  # Save the config
  cfg.save_to_file(config_path)

  # Verify file was created
  assert config_path.exists()

  # Verify JSON content
  with open(config_path, encoding="utf-8") as f:
    data = json.load(f)

  assert data["input_apk"] == "input.apk"
  assert data["output_dir"] == "custom_out"
  assert data["engines"] == ["revanced", "dtlx"]
  assert data["revanced_cli_path"] == "custom-cli.jar"
  assert data["dtlx_analyze"] is True
  # Verify default values were also saved
  assert data["dtlx_optimize"] is False


def test_save_to_file_creates_parent_dirs(tmp_path: Path) -> None:
  """Test that save_to_file creates missing parent directories."""
  config_path = tmp_path / "nested" / "dirs" / "test_config.json"

  cfg = Config()
  cfg.save_to_file(config_path)

  assert config_path.exists()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
  """Test saving a config and loading it back maintains fidelity."""
  config_path = tmp_path / "roundtrip_config.json"

  # Original config with modified values
  original_cfg = Config(
    input_apk="test.apk",
    engines=["a", "b", "c"],
    revanced_patches=["patch1", "patch2", {"patch3": "value"}],
  )

  original_cfg.save_to_file(config_path)

  # Load it back
  loaded_cfg = Config.load_from_file(config_path)

  assert loaded_cfg.input_apk == original_cfg.input_apk
  assert loaded_cfg.engines == original_cfg.engines
  assert loaded_cfg.revanced_patches == original_cfg.revanced_patches
