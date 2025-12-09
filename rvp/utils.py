"""Shared utilities for subprocess execution and file handling."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .context import Context


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
