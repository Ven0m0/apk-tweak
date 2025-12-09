"""APK optimization utilities using apktool, zipalign, and aapt2."""

from __future__ import annotations

import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .ad_patterns import AD_PATTERNS, AdPattern
from .constants import (
    APKTOOL_PATH_KEY,
    DEFAULT_APKTOOL,
    DEFAULT_ZIPALIGN,
    ZIPALIGN_PATH_KEY,
)
from .context import Context
from .utils import run_command


def decompile_apk(apk: Path, output_dir: Path, ctx: Context) -> Path:
    """
    Decompile APK using apktool.

    Args:
        apk: Path to APK file.
        output_dir: Directory for decompiled output.
        ctx: Pipeline context for logging.

    Returns:
        Path: Directory containing decompiled APK.
    """
    decompiled_dir = output_dir / f"{apk.stem}_decompiled"
    apktool = ctx.options.get(APKTOOL_PATH_KEY, DEFAULT_APKTOOL)
    cmd = [str(apktool), "d", str(apk), "-o", str(decompiled_dir), "-f"]
    ctx.log(f"optimizer: Decompiling {apk.name}")
    run_command(cmd, ctx)
    return decompiled_dir


def debloat_apk(decompiled_dir: Path, ctx: Context) -> None:
    """
    Remove bloatware from decompiled APK.

    Args:
        decompiled_dir: Directory containing decompiled APK.
        ctx: Pipeline context for logging and options.
    """
    ctx.log("optimizer: Starting debloat process")
    # Get debloat patterns from options
    debloat_patterns = ctx.options.get("debloat_patterns", [])
    if not debloat_patterns:
        ctx.log("optimizer: No debloat patterns specified, skipping")
        return
    removed_count = 0
    # Remove files matching debloat patterns (O(n*m) where n=files, m=patterns)
    for pattern in debloat_patterns:
        matches = list(decompiled_dir.rglob(pattern))
        for match in matches:
            if match.is_file():
                ctx.log(
                    f"optimizer: Removing {match.relative_to(decompiled_dir)}"
                )
                match.unlink()
                removed_count += 1
            elif match.is_dir():
                ctx.log(
                    f"optimizer: Removing directory {match.relative_to(decompiled_dir)}"
                )
                shutil.rmtree(match)
                removed_count += 1
    ctx.log(f"optimizer: Debloat complete - removed {removed_count} items")


def minify_resources(decompiled_dir: Path, ctx: Context) -> None:
    """
    Minify APK resources (remove unused resources).

    Args:
        decompiled_dir: Directory containing decompiled APK.
        ctx: Pipeline context for logging.
    """
    ctx.log("optimizer: Starting resource minification")
    # Remove unused resource files
    # Common unused resources: drawable-xxxhdpi, raw audio, etc.
    minify_patterns = ctx.options.get(
        "minify_patterns",
        [
            "res/drawable-xxxhdpi/*",  # Extra high DPI (often unnecessary)
            "res/raw/*.mp3",  # Large audio files
            "res/raw/*.wav",
            "assets/unused/*",  # Unused assets
        ],
    )
    removed_count = 0
    removed_size = 0
    for pattern in minify_patterns:
        matches = list(decompiled_dir.rglob(pattern))
        for match in matches:
            if match.is_file():
                size = match.stat().st_size
                ctx.log(
                    f"optimizer: Removing {match.relative_to(decompiled_dir)} ({size} bytes)"
                )
                match.unlink()
                removed_count += 1
                removed_size += size
    ctx.log(
        f"optimizer: Minification complete - removed {removed_count} files ({removed_size} bytes)"
    )


def _apply_patch_to_file(
    file_path: Path, patterns: list[AdPattern], ctx: Context
) -> bool:
    """
    Apply ad-blocking patches to a single smali file.

    Args:
        file_path: Path to smali file to patch.
        patterns: List of (pattern, replacement, description) tuples.
        ctx: Pipeline context for logging.

    Returns:
        True if file was modified, False otherwise.
    """
    try:
        # Use 'ignore' errors to match original script behavior
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        original_content = content

        for pattern, replacement, _ in patterns:
            # Use re.sub directly
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            file_path.write_text(content, encoding="utf-8", errors="ignore")
            return True

        return False
    except Exception as e:
        ctx.log(f"optimizer: Error patching {file_path.name}: {e}")
        return False


def patch_ads(decompiled_dir: Path, ctx: Context) -> None:
    """
    Apply regex-based ad patching to smali files.

    Args:
        decompiled_dir: Directory containing decompiled APK.
        ctx: Pipeline context.
    """
    ctx.log("optimizer: Starting regex-based ad patching")

    # Find all smali files
    smali_files = list(decompiled_dir.rglob("*.smali"))
    if not smali_files:
        ctx.log("optimizer: No smali files found")
        return

    ctx.log(f"optimizer: Scanning {len(smali_files)} smali files...")

    # Pre-compile regex patterns if possible, but the patterns list has descriptions
    # We'll just pass the raw patterns list to the helper for simplicity/compatibility
    total_patched = 0

    # Use ThreadPool for performance (IO boundish, but regex is CPU)
    # O(n) scan of files
    with ThreadPoolExecutor() as executor:
        futures = []
        for smali_file in smali_files:
            futures.append(
                executor.submit(
                    _apply_patch_to_file, smali_file, AD_PATTERNS, ctx
                )
            )

        for future in futures:
            if future.result():
                total_patched += 1

    ctx.log(f"optimizer: Ad patching complete - modified {total_patched} files")


def recompile_apk(decompiled_dir: Path, output_apk: Path, ctx: Context) -> None:
    """
    Recompile APK using apktool.

    Args:
        decompiled_dir: Directory containing decompiled APK.
        output_apk: Path for output APK.
        ctx: Pipeline context for logging.
    """
    apktool = ctx.options.get(APKTOOL_PATH_KEY, DEFAULT_APKTOOL)
    cmd = [str(apktool), "b", str(decompiled_dir), "-o", str(output_apk)]
    ctx.log(f"optimizer: Recompiling APK to {output_apk.name}")
    run_command(cmd, ctx)


def zipalign_apk(input_apk: Path, output_apk: Path, ctx: Context) -> None:
    """
    Optimize APK using zipalign.

    Args:
        input_apk: Path to input APK.
        output_apk: Path for aligned APK.
        ctx: Pipeline context for logging.
    """
    zipalign = ctx.options.get(ZIPALIGN_PATH_KEY, DEFAULT_ZIPALIGN)
    # -f = force overwrite, -v = verbose, 4 = alignment in bytes
    cmd = [str(zipalign), "-f", "-v", "4", str(input_apk), str(output_apk)]
    ctx.log(f"optimizer: Running zipalign on {input_apk.name}")
    run_command(cmd, ctx)


def optimize_apk(
    input_apk: Path,
    output_apk: Path,
    ctx: Context,
    debloat: bool = True,
    minify: bool = True,
) -> None:
    """
    Complete APK optimization pipeline.

    Args:
        input_apk: Path to input APK.
        output_apk: Path for optimized APK.
        ctx: Pipeline context.
        debloat: Enable debloating.
        minify: Enable resource minification.
    """
    ctx.log("optimizer: Starting optimization pipeline")
    work_dir = ctx.work_dir / "optimizer"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Check if ad patching is enabled via options
    patch_ads_enabled = ctx.options.get("revanced_patch_ads", False)

    # Step 1: Decompile
    decompiled_dir = decompile_apk(input_apk, work_dir, ctx)

    # Step 2: Debloat (if enabled)
    if debloat:
        debloat_apk(decompiled_dir, ctx)

    # Step 3: Minify resources (if enabled)
    if minify:
        minify_resources(decompiled_dir, ctx)

    # Step 4: Ad Patching (if enabled)
    if patch_ads_enabled:
        patch_ads(decompiled_dir, ctx)

    # Step 5: Recompile
    temp_apk = work_dir / f"{input_apk.stem}_recompiled.apk"
    recompile_apk(decompiled_dir, temp_apk, ctx)

    # Step 6: Zipalign
    zipalign_apk(temp_apk, output_apk, ctx)
    ctx.log(f"optimizer: Optimization complete - {output_apk}")
