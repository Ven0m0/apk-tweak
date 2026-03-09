"""Shared constants for RVP pipeline."""

from __future__ import annotations

# Configuration keys
APKTOOL_PATH_KEY = "apktool_path"
ZIPALIGN_PATH_KEY = "zipalign_path"

# Default tool names
DEFAULT_APKTOOL = "apktool"
DEFAULT_ZIPALIGN = "zipalign"

# Thread pool configuration
MAX_WORKER_THREADS = 32  # Maximum concurrent workers
DEFAULT_CPU_MULTIPLIER = 4  # CPU count multiplier for I/O-bound tasks


def get_optimal_thread_workers() -> int:
  """
  Calculate optimal worker count for I/O-bound ThreadPoolExecutor tasks.

  Returns:
      Optimal number of workers based on CPU count + multiplier.
  """
  import os

  cpu_count = os.cpu_count() or 1
  return min(MAX_WORKER_THREADS, cpu_count + DEFAULT_CPU_MULTIPLIER)
