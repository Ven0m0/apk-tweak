"""DTL-X analysis and optimization engine."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from ..context import Context


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

  for location in locations:
    if location.is_file():
      return location

  # Check if dtlx.py is in PATH
  dtlx_path = shutil.which("dtlx.py")
  if dtlx_path:
    return Path(dtlx_path)

  return None


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
    ctx.log(
      "dtlx: DTL-X not found. Install from https://github.com/Gameye98/DTL-X"
    )
    report_file.write_text(
      f"DTL-X Analysis Report for {apk.name}\n"
      f"{'=' * 60}\n\n"
      f"Status: FAILED\n"
      f"Reason: DTL-X not installed\n\n"
      f"Install DTL-X from: https://github.com/Gameye98/DTL-X\n",
      encoding="utf-8",
    )
    return False

  ctx.log(f"dtlx: analyzing {apk.name}...")

  try:
    # Run DTL-X to get APK information (decompile without patching)
    result = subprocess.run(
      [sys.executable, str(dtlx), str(apk)],
      capture_output=True,
      text=True,
      timeout=300,  # 5 minute timeout
      check=False,
    )

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

  except subprocess.TimeoutExpired:
    ctx.log("dtlx: analysis timed out after 5 minutes")
    report_file.write_text(
      f"DTL-X Analysis Report for {apk.name}\n"
      f"{'=' * 60}\n\n"
      f"Status: TIMEOUT\n"
      f"Reason: Analysis exceeded 5 minute timeout\n",
      encoding="utf-8",
    )
    return False
  except Exception as e:
    ctx.log(f"dtlx: analysis failed: {e}")
    report_file.write_text(
      f"DTL-X Analysis Report for {apk.name}\n{'=' * 60}\n\nStatus: ERROR\nError: {e}\n",
      encoding="utf-8",
    )
    return False


def _run_dtlx_optimize(ctx: Context, apk: Path, output_apk: Path) -> bool:
  """
  Run DTL-X in optimization mode.

  Args:
      ctx: Pipeline context.
      apk: Input APK file.
      output_apk: Output APK file.

  Returns:
      True if optimization succeeded, False otherwise.
  """
  dtlx = _check_dtlx()
  if not dtlx:
    ctx.log(
      "dtlx: DTL-X not found. Install from https://github.com/Gameye98/DTL-X"
    )
    return False

  # Define optimization flags
  optimization_flags = [
    "--rmads4",  # Remove ad loaders
    "--rmtrackers",  # Remove trackers
    "--rmnop",  # Remove NOP instructions
    "--cleanrun",  # Clean up after patching
  ]

  ctx.log(
    f"dtlx: optimizing {apk.name} with flags: {' '.join(optimization_flags)}"
  )

  try:
    # Create working directory for DTL-X
    work_dir = ctx.work_dir / "dtlx_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Copy APK to working directory
    work_apk = work_dir / apk.name
    shutil.copy2(apk, work_apk)

    # Run DTL-X with optimization flags
    cmd = [sys.executable, str(dtlx)] + optimization_flags + [str(work_apk)]
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      cwd=work_dir,
      timeout=600,  # 10 minute timeout for optimization
      check=False,
    )

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

  except subprocess.TimeoutExpired:
    ctx.log("dtlx: optimization timed out after 10 minutes")
    return False
  except Exception as e:
    ctx.log(f"dtlx: optimization failed: {e}")
    return False


def run(ctx: Context) -> None:
  """
  Execute DTL-X analysis/optimization.

  Integrates with Gameye98/DTL-X for APK analysis and optimization.
  Supports ad removal, tracker removal, and code optimization.

  Args:
      ctx: Pipeline context.
  """
  # Performance: Direct truthiness check instead of bool() conversion
  analyze = ctx.options.get("dtlx_analyze", False)
  optimize = ctx.options.get("dtlx_optimize", False)

  if not (analyze or optimize):
    ctx.log("dtlx: neither analyze nor optimize requested; skipping.")
    return

  apk = ctx.current_apk or ctx.input_apk
  ctx.log(f"dtlx: starting (analyze={analyze}, optimize={optimize}) on {apk}.")

  # Performance: Use direct dict access pattern instead of setdefault
  if "dtlx" not in ctx.metadata:
    ctx.metadata["dtlx"] = {}

  # Run analysis if requested
  if analyze:
    report_file = ctx.output_dir / f"{apk.stem}.dtlx-report.txt"
    if _run_dtlx_analyze(ctx, apk, report_file):
      ctx.metadata["dtlx"]["report"] = str(report_file)

  # Run optimization if requested
  if optimize:
    output_apk = ctx.output_dir / f"{apk.stem}.dtlx-optimized.apk"
    if _run_dtlx_optimize(ctx, apk, output_apk):
      ctx.metadata["dtlx"]["optimized_apk"] = str(output_apk)
      # Update current APK for next engine in pipeline
      ctx.set_current_apk(output_apk)
      ctx.log(f"dtlx: pipeline will continue with {output_apk}")
    else:
      ctx.log(
        "dtlx: optimization failed, pipeline will continue with original APK"
      )
