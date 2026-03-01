"""Configuration schema for RVP pipeline."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

# ⚡ Perf: Use orjson (~6x faster) with fallback to stdlib json
try:
  from typing import Any
  from typing import TextIO

  import orjson

  def _load_json(file_handle: TextIO) -> Any:
    """Load JSON using orjson for performance."""
    return orjson.loads(file_handle.read())

  def _dump_json(data: Any, file_handle: TextIO) -> None:
    """Write JSON using orjson for performance (~6x faster)."""
    # orjson.dumps returns bytes, need to decode for text mode
    json_bytes = orjson.dumps(
      data,
      option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
    )
    file_handle.write(json_bytes.decode("utf-8"))

except ImportError:
  import json
  from typing import Any
  from typing import TextIO

  def _load_json(file_handle: TextIO) -> Any:
    """Load JSON using stdlib json (fallback)."""
    return json.load(file_handle)

  def _dump_json(data: Any, file_handle: TextIO) -> None:
    """Write JSON using stdlib json (fallback)."""
    json.dump(data, file_handle, indent=2, sort_keys=True)


_ENV_VAR_PATTERN = re.compile(r"\${(\w+)(?::-(.*))?}")


def _interpolate_env_vars(data: Any) -> Any:
  """
  Recursively interpolate environment variables in configuration data.

  Supports:
  - ${VAR}
  - ${VAR:-default}

  Args:
      data: Configuration data (dict, list, or string).

  Returns:
      Data with environment variables substituted.
  """
  if isinstance(data, str):

    def replace(match: re.Match[str]) -> str:
      var_name = match.group(1)
      default_value = match.group(2)
      # If var exists, use it; else use default; else keep original placeholder
      val = os.getenv(var_name)
      if val is not None:
        return val
      if default_value is not None:
        return default_value
      return match.group(0)

    return _ENV_VAR_PATTERN.sub(replace, data)
  if isinstance(data, dict):
    return {k: _interpolate_env_vars(v) for k, v in data.items()}
  if isinstance(data, list):
    return [_interpolate_env_vars(v) for v in data]
  return data


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
      revanced_patch_bundles: List of patch bundle paths (supports multiple).
      revanced_integrations_path: Path to integrations.apk.
      revanced_optimize: Enable APK optimization (debloat, minify, zipalign).
      revanced_debloat: Enable debloating (requires optimize).
      revanced_minify: Enable resource minification (requires optimize).
      revanced_patch_ads: Enable regex-based ad patching (requires optimize).
      revanced_patches: List of specific patches to apply (strings or dicts).
      revanced_include_patches: List of patch names to include.
      revanced_exclude_patches: List of patch names to exclude.
      debloat_patterns: File patterns to remove during debloat.
      minify_patterns: Resource patterns to remove during minification.
      apktool_path: Path to apktool executable/jar.
      zipalign_path: Path to zipalign executable.
      rkpairip_apktool_mode: Use ApkTool mode for RKPairip decompilation.
      rkpairip_merge_skip: Enable merge skip mode for separate DEX handling.
      rkpairip_dex_repair: Enable DEX repair after string modifications.
      rkpairip_corex_hook: Enable CoreX hook for Unity/Flutter/crashed APKs.
      rkpairip_anti_split: Enable anti-split merge for split APK files.
  """

  input_apk: str | None = None
  output_dir: str = "out"
  engines: list[str] = field(default_factory=lambda: ["revanced"])

  # Engine specific configs
  dtlx_analyze: bool = False
  dtlx_optimize: bool = False

  # ReVanced configuration
  revanced_cli_path: str = "revanced-cli.jar"
  revanced_patch_bundles: list[str] = field(default_factory=list)
  revanced_integrations_path: str = "integrations.apk"
  revanced_optimize: bool = True
  revanced_debloat: bool = True
  revanced_minify: bool = True
  revanced_patch_ads: bool = False
  revanced_patches: list[str | dict[str, Any]] = field(default_factory=list)
  revanced_include_patches: list[str] = field(default_factory=list)
  revanced_exclude_patches: list[str] = field(default_factory=list)

  # Optimization configuration
  debloat_patterns: list[str] = field(
    default_factory=lambda: [
      # Ad frameworks & libraries
      "*/admob/*",
      "*/google/ads/*",
      "*/facebook/ads/*",
      "*/mopub/*",
      "*/applovin/*",
      "*/unity3d/ads/*",
      "*/vungle/*",
      "*/chartboost/*",
      "*/inmobi/*",
      "*/flurry/*",
      "assets/extensions/ads/*",
      "assets/extensions/search/*",
      # Analytics & tracking
      "*/analytics/*",
      "*/crashlytics/*",
      "*/firebase/analytics/*",
      "*/firebase/crashlytics/*",
      "*/google/firebase/analytics/*",
      "*/adjust/*",
      "*/branch/*",
      "*/appsflyer/*",
      "*/kochava/*",
      # License files
      "LICENSE_UNICODE",
      "LICENSE_OFL",
      "LICENSE.txt",
      "NOTICE.txt",
      "THIRD_PARTY_LICENSES",
      "*/licenses/*",
      # Metadata & build artifacts
      "META-INF/*",
      "car-app-api.level",
      "*.properties",
      "*/build-data.properties",
      # Localization data (non-German/English)
      "com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_A[CDEFGH]*",
      "com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_[B-Z]*",
      "com/google/android/libraries/phonenumbers/data/PhoneNumberAlternateFormatsProto_*",
      "org/joda/time/format/messages_*.properties",
      "org/joda/time/tz/data/Africa/*",
      "org/joda/time/tz/data/America/*",
      "org/joda/time/tz/data/Antarctica/*",
      "org/joda/time/tz/data/Asia/*",
      "org/joda/time/tz/data/Atlantic/*",
      "org/joda/time/tz/data/Australia/*",
      "org/joda/time/tz/data/Indian/*",
      "org/joda/time/tz/data/Pacific/*",
      # Google services bloat
      "*/gms/*",
      "*/play/core/*",
      "*/android/gms/ads/*",
      "*/android/gms/analytics/*",
      # Social SDK bloat
      "*/twitter/sdk/*",
      "*/linkedin/platform/*",
      "*/snapchat/kit/*",
      # Unused assets
      "assets/unused_*",
      "assets/debug/*",
      "assets/test/*",
    ]
  )
  minify_patterns: list[str] = field(
    default_factory=lambda: [
      # High DPI drawables (xxxhdpi, xxhdpi often overkill)
      "res/drawable-xxxhdpi/*",
      "res/drawable-xxhdpi/*",
      # Raw media files
      "res/raw/*.mp3",
      "res/raw/*.wav",
      "res/raw/*.ogg",
      "res/raw/*.m4a",
      # Large image assets
      "assets/kazoo/*",
      "assets/images/*.png",
      "assets/images/*.jpg",
      "assets/backgrounds/*",
      "assets/splash/*",
      # Video files
      "res/raw/*.mp4",
      "res/raw/*.webm",
      "assets/video/*",
      # Fonts (keep only essential)
      "res/font/*-bold.ttf",
      "res/font/*-light.ttf",
      "assets/fonts/*-thin.ttf",
      # Unused resources
      "res/raw/unused_*",
      "assets/unused/*",
    ]
  )

  # Tool paths
  apktool_path: str = "apktool"
  zipalign_path: str = "zipalign"

  # RKPairip configuration
  rkpairip_apktool_mode: bool = False
  rkpairip_merge_skip: bool = False
  rkpairip_dex_repair: bool = False
  rkpairip_corex_hook: bool = False
  rkpairip_anti_split: bool = False

  # Legacy support (backward compatibility)
  revanced_patches_path: str = "patches.jar"

  @classmethod
  def load_from_file(cls, path: Path) -> Config:
    """
    Load configuration from a JSON file.

    Uses orjson for ~6x faster parsing when available, falls back to stdlib.

    Args:
        path: Path to the JSON config file.

    Returns:
        Config: Loaded configuration instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If file contains invalid JSON.
    """
    if not path.exists():
      raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as f:
      raw_data = _load_json(f)
      data = _interpolate_env_vars(raw_data)

      # ⚡ Robustness: Only pass valid fields to dataclass constructor
      import dataclasses

      field_names = {f.name for f in dataclasses.fields(cls)}
      filtered_data = {k: v for k, v in data.items() if k in field_names}

      return cls(**filtered_data)

  def save_to_file(self, path: Path) -> None:
    """
    Save configuration to a JSON file.

    Uses orjson for ~6x faster serialization when available.

    Args:
        path: Path to save the JSON config file.

    Raises:
        OSError: If file cannot be written.
    """
    from dataclasses import asdict

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
      data = asdict(self)
      _dump_json(data, f)
