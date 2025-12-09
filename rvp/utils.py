"""Shared utilities for subprocess execution and file handling."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .context import Context

# Timeout constants (seconds)
TIMEOUT_CLONE = 120  # Git clone
TIMEOUT_PATCH = 900  # Large patching operations (15 min)
TIMEOUT_ANALYZE = 300  # Analysis operations (5 min)
TIMEOUT_OPTIMIZE = 600  # Optimization operations (10 min)
TIMEOUT_BUILD = 1200  # Build operations (20 min)


def run_command(
  cmd: list[str],
  ctx: Context,
  cwd: Path | None = None,
  check: bool = True,
  timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
  """
  Execute a subprocess with real-time logging to context.

  ⚡ Perf: Supports configurable timeout to prevent hanging processes.

  Args:
      cmd: Command list (e.g., ["java", "-jar", ...]).
      ctx: Pipeline context for logging.
      cwd: Working directory for the command.
      check: Raise CalledProcessError on non-zero exit code.
      timeout: Command timeout in seconds (None = no timeout).

  Returns:
      subprocess.CompletedProcess: Completed process info.

  Raises:
      subprocess.CalledProcessError: If check=True and command fails.
      subprocess.TimeoutExpired: If command exceeds timeout.
  """
  ctx.log(f"EXEC: {' '.join(str(x) for x in cmd)}")
  if timeout:
    ctx.log(f"  Timeout: {timeout}s")

  try:
    # Use Popen to stream output in real-time
    with subprocess.Popen(
      cmd,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,  # Merge stderr into stdout
      text=True,
      cwd=cwd,
      bufsize=1,  # Line buffered
      encoding="utf-8",
      errors="replace",
    ) as proc:
      if proc.stdout:
        for line in proc.stdout:
          ctx.log(f"  {line.strip()}")

    # ⚡ Perf: Use timeout-aware wait
    try:
      retcode = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
      proc.kill()  # Ensure process is terminated
      proc.wait()  # Clean up zombie process
      ctx.log(f"ERR: Command timed out after {timeout}s")
      raise

    if check and retcode != 0:
      raise subprocess.CalledProcessError(retcode, cmd)

    return subprocess.CompletedProcess(cmd, retcode)

  except subprocess.TimeoutExpired:
    # Re-raise timeout exceptions
    raise
  except Exception as e:
    ctx.log(f"ERR: Command failed: {e}")
    if check:
      raise
    return subprocess.CompletedProcess(cmd, 1)


def check_dependencies(required: list[str]) -> tuple[bool, list[str]]:
  """
  Check if required tools are available in PATH.

  Args:
      required: List of tool names to check.

  Returns:
      Tuple of (all_found: bool, missing_tools: list[str]).
  """
  missing = [tool for tool in required if not shutil.which(tool)]
  return (not missing, missing)


def clone_repository(
  url: str,
  target_dir: Path,
  ctx: Context,
  timeout: int = TIMEOUT_CLONE,
) -> bool:
  """
  Clone git repository with error handling.

  Args:
      url: Git repository URL.
      target_dir: Directory to clone into.
      ctx: Pipeline context for logging.
      timeout: Clone timeout in seconds.

  Returns:
      True if successful, False otherwise.
  """
  if target_dir.exists():
    ctx.log(f"Repository already cloned at {target_dir}, skipping")
    return True

  ctx.log(f"Cloning repository from {url}")
  try:
    subprocess.run(
      ["git", "clone", url, str(target_dir)],
      capture_output=True,
      text=True,
      timeout=timeout,
      check=True,
    )
    ctx.log(f"Repository cloned successfully to {target_dir}")
    return True
  except subprocess.TimeoutExpired:
    ctx.log(f"ERR: Clone timed out after {timeout}s")
    return False
  except subprocess.CalledProcessError as e:
    ctx.log(f"ERR: Clone failed: {e.stderr or e.stdout}")
    return False
  except Exception as e:
    ctx.log(f"ERR: Clone error: {e}")
    return False


def find_latest_apk(directory: Path) -> Path | None:
  """
  Find the most recently modified APK file in a directory.

  Args:
      directory: Directory to search for APK files.

  Returns:
      Path to the latest APK or None if not found.
  """
  if not directory.exists():
    return None

  apk_files = list(directory.glob("*.apk"))
  if not apk_files:
    return None

  # Return the most recently modified APK
  return max(apk_files, key=lambda p: p.stat().st_mtime)
