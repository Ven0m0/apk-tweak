"""Shared constants for RVP pipeline."""

from __future__ import annotations

# Configuration keys
APKTOOL_PATH_KEY = "apktool_path"
ZIPALIGN_PATH_KEY = "zipalign_path"
REVANCED_CLI_KEY = "revanced_cli"
REVANCED_PATCHES_KEY = "patches"
REVANCED_INTEGRATIONS_KEY = "revanced_integrations"

# Default tool names
DEFAULT_APKTOOL = "apktool"
DEFAULT_ZIPALIGN = "zipalign"

# Engine names
ENGINE_REVANCED = "revanced"
ENGINE_MAGISK = "magisk"
ENGINE_LSPATCH = "lspatch"
ENGINE_DTLX = "dtlx"
ENGINE_RKPAIRIP = "rkpairip"
