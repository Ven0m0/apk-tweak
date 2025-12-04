"""Shared utilities for subprocess execution and file handling."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from .context import Context

def run_command(
    cmd: List[str],
    ctx: Context,
    cwd: Optional[Path] = None,
    check: bool = True
) -> subprocess.CompletedProcess[str]:
    """
    Run a subprocess with real-time logging to context.
    
    Args:
        cmd: Command list (e.g. ["java", "-jar", ...])
        ctx: Pipeline context for logging
        cwd: Working directory
        check: Raise error on non-zero exit code
    """
    cmd_str = " ".join(str(x) for x in cmd)
    ctx.log(f"EXEC: {cmd_str}")

    try:
        # Use Popen to stream output in real-time
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True,
            cwd=cwd,
            bufsize=1, # Line buffered
            encoding="utf-8", 
            errors="replace"
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
