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

# Performance thresholds (bytes)
MMAP_FILE_SIZE_THRESHOLD = 102_400  # 100 KB - use mmap for larger files
LARGE_FILE_THRESHOLD = 1_048_576  # 1 MB
SMALL_FILE_THRESHOLD = 10_240  # 10 KB

# Thread pool configuration
MAX_WORKER_THREADS = 32  # Maximum concurrent workers
DEFAULT_CPU_MULTIPLIER = 4  # CPU count multiplier for I/O-bound tasks
