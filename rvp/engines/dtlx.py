"""DTL-X analysis and optimization engine.

Integrates with Gameye98/DTL-X - Python APK reverser and patcher tool.
Supports comprehensive APK modification including ad removal, tracker removal,
security bypasses, and code optimization.

Available DTL-X flags:
  Ad Removal: rmads1-5, rmtrackers
  Security: sslbypass, rmcopy, rmvpndet, rmusbdebug, rmssrestrict, rmrootxposedvpn
  Protection: rmpairip, bppairip
  Code: rmnop, rmnown, nokill
  Modification: customfont, changepackagename, changeactivity, cloneapk
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..context import Context
from ..utils import require_input_apk

# Constants
DTLX_REPO_URL = "https://github.com/Gameye98/DTL-X"
DTLX_NOT_FOUND_MSG = f"dtlx: DTL-X not found. Install from {DTLX_REPO_URL}"

# All available DTL-X flags mapped to pipeline option names
DTLX_FLAGS: dict[str, str] = {
  # Ad removal options
  "rmads1": "--rmads1",  # Remove Google Mobile Services ad activities
  "rmads2": "--rmads2",  # Remove internet and ad-related permissions
  "rmads3": "--rmads3",  # Replace ad publisher IDs in smali
  "rmads4": "--rmads4",  # Patch ad loader invocations
  "rmads5": "--rmads5",  # Replace CA ad IDs with dummy values
  "rmtrackers": "--rmtrackers",  # Remove known tracker classes
  # Code cleaning options
  "rmnop": "--rmnop",  # Strip no-operation instructions
  "rmnown": "--rmnown",  # Delete unknown directories
  # Security bypass options
  "sslbypass": "--sslbypass",  # SSL certificate pinning bypass
  "rmcopy": "--rmcopy",  # Remove copy protection
  "rmvpndet": "--rmvpndet",  # Remove VPN detection
  "rmusbdebug": "--rmusbdebug",  # Remove USB debugging detection
  "rmssrestrict": "--rmssrestrict",  # Disable screenshot restrictions
  "rmrootxposedvpn": "--rmrootxposedvpn",  # Remove root/Xposed/VPN checks
  "rmexportdata": "--rmexportdata",  # Suppress data export notifications
  # Protection bypass options
  "rmpairip": "--rmpairip",  # Remove Pairip protection
  "bppairip": "--bppairip",  # Bypass Pairip through library spoofing
  "rmprop": "--rmprop",  # Delete .properties files
  # Modification options
  "nokill": "--nokill",  # Prevent system exit calls
  "fixinstall": "--fixinstall",  # Repair installer detection
  "obfuscatemethods": "--obfuscatemethods",  # Rename methods randomly
  "mergeobb": "--mergeobb",  # Consolidate OBB files
  "injectdocsprovider": "--injectdocsprovider",  # Add document provider
  "il2cppdumper": "--il2cppdumper",  # Inject IL2CPP dumper
  "cloneapk": "--cloneapk",  # Duplicate application
  "cleanrun": "--cleanrun",  # Delete project after compilation
  "nocompile": "--nocompile",  # Skip recompilation
}

# Default optimization preset
DEFAULT_OPTIMIZATION_FLAGS = ["rmads4", "rmtrackers", "rmnop", "cleanrun"]


def _write_report(report_file: Path, apk_name: str, status: str, details: str) -> None:
  """
  Write standardized DTL-X analysis report.

  Args:
      report_file: Path to report file.
      apk_name: Name of the APK being analyzed.
      status: Status string (FAILED, TIMEOUT, ERROR, SUCCESS, etc.).
      details: Additional details or error information.
  """
  report_content = (
    f"DTL-X Analysis Report for {apk_name}\n{'=' * 60}\n\nStatus: {status}\n{details}"
  )
  report_file.write_text(report_content, encoding="utf-8")


def _check_dtlx() -> Path | None:
  """
  Check if DTL-X is available.

  Returns:
      Path to dtlx.py if found, None otherwise.
  """
  # Check common installation locations
  locations = [
    Path.home() / "DTL-X" / "dtlx.py",
    Path("/opt/DTL-X/dtlx.py"),
    Path("/usr/local/bin/dtlx.py"),
  ]

  # Use next() with generator for compact iteration
  found = next((loc for loc in locations if loc.is_file()), None)
  if found:
    return found

  # Check if dtlx.py is in PATH
  dtlx_path = shutil.which("dtlx.py")
  return Path(dtlx_path) if dtlx_path else None


def _run_dtlx_command(
  ctx: Context,
  dtlx_path: Path,
  args: list[str],
  timeout: int,
  cwd: Path | None = None,
) -> tuple[subprocess.CompletedProcess[str] | None, Exception | None]:
  """
  Execute DTL-X command with common error handling.

  Args:
      ctx: Pipeline context.
      dtlx_path: Path to dtlx.py executable.
      args: List of arguments to pass to DTL-X.
      timeout: Timeout in seconds.
      cwd: Working directory (optional).

  Returns:
      Tuple of (CompletedProcess, None) on execution (even if returncode != 0),
      or (None, Exception) on timeout/error.
  """
  cmd = [sys.executable, str(dtlx_path)] + args
  try:
    proc = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      timeout=timeout,
      cwd=cwd,
      check=False,
    )
    return proc, None
  except (subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError) as e:
    # Log here to avoid duplication
    if isinstance(e, subprocess.TimeoutExpired):
      ctx.log(f"dtlx: command timed out after {timeout // 60} minutes")
    else:
      ctx.log(f"dtlx: command failed: {e}")
    return None, e


def _run_dtlx_analyze(ctx: Context, apk: Path, report_file: Path) -> bool:
  """
  Run DTL-X in analysis mode.

  Args:
      ctx: Pipeline context.
      apk: Input APK file.
      report_file: Output report file.

  Returns:
      True if analysis succeeded, False otherwise.
  """
  dtlx = _check_dtlx()
  if not dtlx:
    ctx.log(DTLX_NOT_FOUND_MSG)
    _write_report(
      report_file,
      apk.name,
      "FAILED",
      f"Reason: DTL-X not installed\n\nInstall DTL-X from: {DTLX_REPO_URL}\n",
    )
    return False

  ctx.log(f"dtlx: analyzing {apk.name}...")

  # Run DTL-X to get APK information (decompile without patching)
  result, error = _run_dtlx_command(ctx, dtlx, [str(apk)], timeout=300)

  if error:
    # Handle error reporting based on exception type
    if isinstance(error, subprocess.TimeoutExpired):
      status = "TIMEOUT"
      details = "Reason: Analysis exceeded 5 minute timeout\n"
    else:
      status = "ERROR"
      details = f"Error: {error}\n"

    _write_report(report_file, apk.name, status, details)
    return False

  # Should be unreachable if result is None and error is None, but for type safety:
  if result is None:
    return False

  # Generate analysis report
  report_content = [
    f"DTL-X Analysis Report for {apk.name}",
    "=" * 60,
    "",
    f"Status: {'SUCCESS' if result.returncode == 0 else 'COMPLETED WITH WARNINGS'}",
    f"Exit Code: {result.returncode}",
    "",
    "STDOUT:",
    "-" * 60,
    result.stdout if result.stdout else "(no output)",
    "",
  ]

  if result.stderr:
    report_content.extend(
      [
        "STDERR:",
        "-" * 60,
        result.stderr,
        "",
      ]
    )

  report_file.write_text("\n".join(report_content), encoding="utf-8")
  ctx.log(f"dtlx: analysis report saved to {report_file}")
  return True


def _build_flags_from_options(options: dict[str, Any]) -> list[str]:
  """
  Build DTL-X command line flags from pipeline options.

  Args:
      options: Pipeline options dictionary.

  Returns:
      List of command line flags to pass to DTL-X.
  """
  flags: list[str] = []

  # Check each known flag in options
  for opt_name, flag in DTLX_FLAGS.items():
    if options.get(opt_name):
      flags.append(flag)

  # If no specific flags, use defaults
  if not flags:
    flags = [DTLX_FLAGS[f] for f in DEFAULT_OPTIMIZATION_FLAGS]

  return flags


def _run_dtlx_optimize(
  ctx: Context, apk: Path, output_apk: Path, flags: list[str]
) -> bool:
  """
  Run DTL-X in optimization mode.

  Args:
      ctx: Pipeline context.
      apk: Input APK file.
      output_apk: Output APK file.
      flags: Command line flags to pass to DTL-X.

  Returns:
      True if optimization succeeded, False otherwise.
  """
  dtlx = _check_dtlx()
  if not dtlx:
    ctx.log(DTLX_NOT_FOUND_MSG)
    return False

  ctx.log(f"dtlx: optimizing {apk.name} with flags: {' '.join(flags)}")

  try:
    # Create working directory for DTL-X
    work_dir = ctx.work_dir / "dtlx_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Copy APK to working directory
    work_apk = work_dir / apk.name
    shutil.copy2(apk, work_apk)

    # Run DTL-X with optimization flags
    args = flags + [str(work_apk)]
    result, error = _run_dtlx_command(ctx, dtlx, args, timeout=600, cwd=work_dir)

    if error or result is None:
      return False

    # DTL-X typically creates output in the same directory
    # Look for the patched APK
    patched_files = list(work_dir.glob("*_patched.apk"))
    if not patched_files:
      patched_files = list(work_dir.glob("*-patched.apk"))

    if patched_files and result.returncode == 0:
      # Copy the patched APK to output
      shutil.copy2(patched_files[0], output_apk)
      ctx.log(f"dtlx: optimized APK saved to {output_apk}")
      return True

    ctx.log(f"dtlx: optimization failed (exit code: {result.returncode})")
    if result.stderr:
      ctx.log(f"dtlx: error: {result.stderr[:200]}")
    return False

  except OSError as e:
    ctx.log(f"dtlx: file operation failed: {e}")
    return False


def run(ctx: Context) -> None:
  """
  Execute DTL-X analysis/optimization.

  Integrates with Gameye98/DTL-X for APK analysis and optimization.
  Supports comprehensive modifications via context options.

  Pipeline options (ctx.options):
      dtlx_analyze: bool - Run analysis mode
      dtlx_optimize: bool - Run optimization mode

  DTL-X flags (all bool, set True to enable):
      rmads1-5: Ad removal (levels 1-5)
      rmtrackers: Remove tracker classes
      rmnop: Strip NOP instructions
      sslbypass: SSL pinning bypass
      rmcopy: Remove copy protection
      rmvpndet: Remove VPN detection
      rmusbdebug: Remove USB debug detection
      rmssrestrict: Disable screenshot restrictions
      rmrootxposedvpn: Remove root/Xposed/VPN checks
      rmpairip/bppairip: Pairip protection removal/bypass
      nokill: Prevent exit calls
      fixinstall: Fix installer detection
      obfuscatemethods: Randomize method names
      mergeobb: Consolidate OBB files
      cleanrun: Delete project after build
      nocompile: Skip recompilation

  Args:
      ctx: Pipeline context.
  """
  analyze = ctx.options.get("dtlx_analyze", False)
  optimize = ctx.options.get("dtlx_optimize", False)

  if not (analyze or optimize):
    ctx.log("dtlx: neither analyze nor optimize requested; skipping.")
    return

  apk = require_input_apk(ctx)
  ctx.log(f"dtlx: starting (analyze={analyze}, optimize={optimize}) on {apk}.")

  if "dtlx" not in ctx.metadata:
    ctx.metadata["dtlx"] = {}

  # Run analysis if requested
  if analyze:
    report_file = ctx.output_dir / f"{apk.stem}.dtlx-report.txt"
    if _run_dtlx_analyze(ctx, apk, report_file):
      ctx.metadata["dtlx"]["report"] = str(report_file)

  # Run optimization if requested
  if optimize:
    # Build flags from options or use defaults
    flags = _build_flags_from_options(ctx.options)
    ctx.metadata["dtlx"]["flags_used"] = flags

    output_apk = ctx.output_dir / f"{apk.stem}.dtlx-optimized.apk"
    if _run_dtlx_optimize(ctx, apk, output_apk, flags):
      ctx.metadata["dtlx"]["optimized_apk"] = str(output_apk)
      # Update current APK for next engine in pipeline
      ctx.set_current_apk(output_apk)
      ctx.log(f"dtlx: pipeline will continue with {output_apk}")
    else:
      ctx.log("dtlx: optimization failed, pipeline will continue with original APK")
