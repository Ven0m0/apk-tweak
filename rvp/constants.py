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
ENGINE_ANDROID_BUILDER = "android_builder"
ENGINE_DISCORD = "discord"
ENGINE_DTLX = "dtlx"
ENGINE_LSPATCH = "lspatch"
ENGINE_MEDIA_OPTIMIZER = "media_optimizer"
ENGINE_MODIFY = "modify"
ENGINE_REVANCED = "revanced"
ENGINE_RKPAIRIP = "rkpairip"
ENGINE_STRING_CLEANER = "string_cleaner"
ENGINE_WHATSAPP = "whatsapp"

# Performance thresholds (bytes)
MMAP_FILE_SIZE_THRESHOLD = 102_400  # 100 KiB - use mmap for larger files
LARGE_FILE_THRESHOLD = 1_048_576  # 1 MB
SMALL_FILE_THRESHOLD = 10_240  # 10 KB

# Thread pool configuration
MAX_WORKER_THREADS = 32  # Maximum concurrent workers
DEFAULT_CPU_MULTIPLIER = 4  # CPU count multiplier for I/O-bound tasks
MAX_PROCESS_WORKERS = 8  # Maximum workers for CPU-bound process pools


def get_optimal_thread_workers() -> int:
  """
  Calculate optimal worker count for I/O-bound ThreadPoolExecutor tasks.

  Returns:
      Optimal number of workers based on CPU count + multiplier.
  """
  import os

  cpu_count = os.cpu_count() or 1
  return min(MAX_WORKER_THREADS, cpu_count + DEFAULT_CPU_MULTIPLIER)


def get_optimal_process_workers() -> int:
  """
  Calculate optimal worker count for CPU-bound ProcessPoolExecutor tasks.

  Returns:
      Optimal number of workers capped at MAX_PROCESS_WORKERS.
  """
  import os

  cpu_count = os.cpu_count() or 1
  return min(cpu_count, MAX_PROCESS_WORKERS)
