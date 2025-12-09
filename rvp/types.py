"""Type definitions for RVP pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
  from pathlib import Path


class RkPairipOptions(TypedDict, total=False):
  """RKPairip engine configuration options."""

  apktool_mode: bool
  merge_skip: bool
  dex_repair: bool
  corex_hook: bool
  anti_split: bool


class ToolPaths(TypedDict, total=False):
  """Paths to external tools."""

  revanced_cli: str
  patches: str
  revanced_integrations: str
  apktool_path: str
  zipalign_path: str


class PipelineOptions(TypedDict, total=False):
  """
  Configuration options for pipeline engines and tools.

  All fields are optional to support partial configuration.
  """

  # DTL-X options
  dtlx_analyze: bool
  dtlx_optimize: bool

  # ReVanced options
  revanced_optimize: bool
  revanced_debloat: bool
  revanced_minify: bool
  revanced_patch_ads: bool
  revanced_include_patches: list[str]
  revanced_exclude_patches: list[str]
  revanced_exclusive: bool
  revanced_patches: list[str | dict[str, Any]]

  # LSPatch options
  lspatch_modules: list[str]

  # Discord options
  discord_keystore: Path | str
  discord_keystore_pass: str
  discord_version: str
  discord_patches: list[str]

  # WhatsApp options
  whatsapp_ab_tests: bool
  whatsapp_timeout: int
  whatsapp_temp_dir: str

  # Media optimizer options
  optimize_images: bool
  optimize_audio: bool
  target_dpi: str

  # Nested configuration
  rkpairip: RkPairipOptions
  tools: ToolPaths

  # Pattern lists for optimization
  debloat_patterns: list[str]
  minify_patterns: list[str]
