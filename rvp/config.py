"""Configuration schema for RVP pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
  """
  Configuration schema for ReVanced Pipeline.

  Attributes:
      input_apk: Path to input APK file (optional, can be CLI arg).
      output_dir: Directory for output files.
      engines: List of engine names to execute.
      dtlx_analyze: Enable DTL-X analysis mode.
      dtlx_optimize: Enable DTL-X optimization mode.
      revanced_cli_path: Path to revanced-cli.jar.
      revanced_patches_path: Path to patches.jar.
      revanced_integrations_path: Path to integrations.apk.
  """

  input_apk: str | None = None
  output_dir: str = "out"
  engines: list[str] = field(default_factory=lambda: ["revanced"])

  # Engine specific configs
  dtlx_analyze: bool = False
  dtlx_optimize: bool = False

  # Tool paths (can be set via config file)
  revanced_cli_path: str = "revanced-cli.jar"
  revanced_patches_path: str = "patches.jar"
  revanced_integrations_path: str = "integrations.apk"

  @classmethod
  def load_from_file(cls, path: Path) -> Config:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the JSON config file.

    Returns:
        Config: Loaded configuration instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    if not path.exists():
      raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as f:
      data = json.load(f)
      return cls(**data)
