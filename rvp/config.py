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
        revanced_patch_bundles: List of patch bundle paths (supports multiple).
        revanced_integrations_path: Path to integrations.apk.
        revanced_optimize: Enable APK optimization (debloat, minify, zipalign).
        revanced_debloat: Enable debloating (requires optimize).
        revanced_minify: Enable resource minification (requires optimize).
        revanced_patch_ads: Enable regex-based ad patching (requires optimize).
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
    revanced_include_patches: list[str] = field(default_factory=list)
    revanced_exclude_patches: list[str] = field(default_factory=list)

    # Optimization configuration
    debloat_patterns: list[str] = field(
        default_factory=lambda: [
            "*/admob/*",
            "*/google/ads/*",
            "*/facebook/ads/*",
            "*/analytics/*",
            "*/crashlytics/*",
        ]
    )
    minify_patterns: list[str] = field(
        default_factory=lambda: [
            "res/drawable-xxxhdpi/*",
            "res/raw/*.mp3",
            "res/raw/*.wav",
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
