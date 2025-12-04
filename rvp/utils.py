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
) -> subprocess.CompletedProcess[str]:
  """
  Execute a subprocess with real-time logging to context.

  Args:
      cmd: Command list (e.g., ["java", "-jar", ...]).
      ctx: Pipeline context for logging.
      cwd: Working directory for the command.
      check: Raise CalledProcessError on non-zero exit code.

  Returns:
      subprocess.CompletedProcess: Completed process info.

  Raises:
      subprocess.CalledProcessError: If check=True and command fails.
  """
  cmd_str = " ".join(str(x) for x in cmd)
  ctx.log(f"EXEC: {cmd_str}")

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

    retcode = proc.wait()

    if check and retcode != 0:
      raise subprocess.CalledProcessError(retcode, cmd)

    return subprocess.CompletedProcess(cmd, retcode)

  except Exception as e:
    ctx.log(f"ERR: Command failed: {e}")
    if check:
      raise
    return subprocess.CompletedProcess(cmd, 1)
