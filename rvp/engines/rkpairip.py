"""RKPairip (Pairip) engine for APK decompilation, modification, and rebuilding."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..context import Context


def run(ctx: Context) -> None:
    """
    Execute RKPairip (Pairip) APK processing engine.

    RKPairip provides advanced APK decompilation and rebuilding with string recovery,
    supporting multiple modes for different use cases.

    Supported modes (via options):
    - apktool_mode: Use ApkTool for decompilation (default: APKEditor)
    - merge_skip: Handle additional DEX files separately
    - dex_repair: Fix DEX files after string modifications
    - corex_hook: Enable CoreX for Unity/Flutter/crashed APKs
    - anti_split: Merge split APK files

    Args:
        ctx: Pipeline context.

    Raises:
        ValueError: If no input APK is available.
        FileNotFoundError: If RKPairip is not installed.
        subprocess.CalledProcessError: If RKPairip execution fails.
    """
    ctx.log("rkpairip: Starting APK processing")

    # Get input APK
    input_apk = ctx.current_apk or ctx.input_apk
    if not input_apk:
        raise ValueError("No input APK found in context")

    # Check if RKPairip is installed
    if not shutil.which("RKPairip"):
        ctx.log(
            "rkpairip: RKPairip not found. Install via: pip install Pairip",
            level=40,
        )
        raise FileNotFoundError("RKPairip not installed. Run: pip install Pairip")

    # Get configuration options
    options = ctx.options.get("rkpairip", {})
    use_apktool = options.get("apktool_mode", False)
    merge_skip = options.get("merge_skip", False)
    dex_repair = options.get("dex_repair", False)
    corex_hook = options.get("corex_hook", False)
    anti_split = options.get("anti_split", False)

    # Prepare output directory
    work_dir = ctx.work_dir / "rkpairip"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = ["RKPairip", "-i", str(input_apk)]

    # Add mode flags
    if use_apktool:
        cmd.append("-a")
        ctx.log("rkpairip: Using ApkTool mode")
    if merge_skip:
        cmd.append("-s")
        ctx.log("rkpairip: Merge skip mode enabled")
    if dex_repair:
        cmd.append("-r")
        ctx.log("rkpairip: DEX repair enabled")
    if corex_hook:
        cmd.append("-x")
        ctx.log("rkpairip: CoreX hook enabled (Unity/Flutter support)")
    if anti_split:
        cmd.append("-m")
        ctx.log("rkpairip: Anti-split merge mode enabled")

    # Execute RKPairip
    ctx.log(f"rkpairip: Executing command: {' '.join(cmd)}")

    try:
        # RKPairip typically outputs to current directory
        # We'll run it in the work directory
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Log output
        if result.stdout:
            for line in result.stdout.splitlines():
                ctx.log(f"  {line}")
        if result.stderr:
            for line in result.stderr.splitlines():
                ctx.log(f"  {line}")

    except subprocess.CalledProcessError as e:
        ctx.log(f"rkpairip: Command failed with code {e.returncode}", level=40)
        if e.stdout:
            ctx.log(f"STDOUT: {e.stdout}", level=40)
        if e.stderr:
            ctx.log(f"STDERR: {e.stderr}", level=40)
        raise

    # Find output APK (RKPairip typically creates output in current dir)
    # Pattern: often creates files with "_signed" or similar suffix
    output_candidates = list(work_dir.glob("*.apk"))

    if not output_candidates:
        ctx.log("rkpairip: No output APK found, checking parent directory", level=30)
        # Sometimes output is in parent directory
        output_candidates = list(Path.cwd().glob("*_signed.apk"))

    if output_candidates:
        # Use the most recently modified APK as output
        output_apk = max(output_candidates, key=lambda p: p.stat().st_mtime)
        ctx.log(f"rkpairip: Found output APK: {output_apk.name}")

        # Move to output directory with standardized name
        final_apk = ctx.output_dir / f"{input_apk.stem}.rkpairip.apk"
        shutil.move(str(output_apk), str(final_apk))

        ctx.set_current_apk(final_apk)
        ctx.log(f"rkpairip: Processing complete - {final_apk}")

        # Store metadata
        ctx.metadata["rkpairip"] = {
            "apktool_mode": use_apktool,
            "merge_skip": merge_skip,
            "dex_repair": dex_repair,
            "corex_hook": corex_hook,
            "anti_split": anti_split,
            "output_apk": str(final_apk),
        }
    else:
        ctx.log(
            "rkpairip: No output APK generated. Check RKPairip logs above.",
            level=40,
        )
        raise FileNotFoundError("RKPairip did not produce an output APK")
