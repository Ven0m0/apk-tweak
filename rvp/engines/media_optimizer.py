"""Media optimization engine for APK size reduction."""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from concurrent.futures import Executor
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path

from ..constants import get_optimal_process_workers
from ..context import Context
from ..utils import check_dependencies
from ..utils import require_input_apk

# Constants
DPI_FOLDERS = {
  "ldpi": 120,
  "mdpi": 160,
  "tvdpi": 213,
  "hdpi": 240,
  "xhdpi": 320,
  "xxhdpi": 480,
  "xxxhdpi": 640,
}


def _optimize_png_worker(file_path: Path) -> tuple[Path, bool]:
  """Worker function for PNG optimization using pngquant."""
  try:
    cmd = ["pngquant", "--force", "--ext", ".png", "--skip-if-larger", str(file_path)]
    subprocess.run(
      cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return file_path, True
  except subprocess.CalledProcessError:
    return file_path, False


def _optimize_png_optipng_worker(
  file_path: Path, optimization_level: int
) -> tuple[Path, bool]:
  """Worker function for PNG optimization using optipng."""
  try:
    cmd = ["optipng", "-o", str(optimization_level), "-quiet", str(file_path)]
    subprocess.run(
      cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return file_path, True
  except subprocess.CalledProcessError:
    return file_path, False


def _optimize_jpg_worker(file_path: Path) -> tuple[Path, bool]:
  """Worker function for JPEG optimization using jpegoptim."""
  try:
    # Strip all markers, progressive
    cmd = [
      "jpegoptim",
      "--strip-all",
      "--all-progressive",
      "-q",
      str(file_path),
    ]
    subprocess.run(
      cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return file_path, True
  except subprocess.CalledProcessError:
    return file_path, False


def _optimize_audio_worker(file_path: Path) -> tuple[Path, bool]:
  """Worker function for audio optimization using ffmpeg."""
  try:
    # Use ffmpeg to re-encode slightly to reduce size or strip metadata
    # Simple metadata stripping: -map_metadata -1 -c:a copy
    # Note: re-encoding takes time but saves space. Stripping metadata is fast.
    # For now, we strip metadata and use efficient copying.
    temp_file = file_path.with_suffix(file_path.suffix + ".tmp")
    cmd = [
      "ffmpeg",
      "-y",
      "-i",
      str(file_path),
      "-map_metadata",
      "-1",
      "-c:a",
      "copy",
      str(temp_file),
    ]
    subprocess.run(
      cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if temp_file.exists():
      # Only replace if smaller
      if temp_file.stat().st_size < file_path.stat().st_size:
        shutil.move(str(temp_file), str(file_path))
        return file_path, True
      temp_file.unlink()
      return file_path, False
    return file_path, False
  except Exception:
    if "temp_file" in locals() and temp_file.exists():
      temp_file.unlink()
    return file_path, False


def _extract_apk(ctx: Context, apk_path: Path, extract_dir: Path) -> bool:
  """Extract APK contents using apktool."""
  if extract_dir.exists():
    shutil.rmtree(extract_dir)

  ctx.log(f"media_optimizer: extracting {apk_path.name}...")
  try:
    # Use apktool for proper resource decoding
    # Note: apktool is slower than zip unzip but needed for proper resource handling
    # However, for media optimization we might get away with just zip extraction
    # if we are not modifying resources.arsc.
    # But filtering DPIs requires deleting folders which is easier with apktool structure?
    # Actually, standard zip structure has res/drawable-xxx too.
    # Using zipfile is MUCH faster. Let's try zipfile first.
    with zipfile.ZipFile(apk_path, "r") as zf:
      zf.extractall(extract_dir)
    return True
  except Exception as e:
    ctx.log(f"media_optimizer: extraction error: {e}")
    return False


def _repackage_apk(ctx: Context, extract_dir: Path, output_apk: Path) -> bool:
  """Repackage folder into APK."""
  ctx.log(f"media_optimizer: repacking to {output_apk.name}...")
  try:
    # Zip the directory
    with zipfile.ZipFile(
      output_apk, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
      for root, _, files in os.walk(extract_dir):
        root_path = Path(root)
        for file in files:
          file_path = root_path / file
          arcname = file_path.relative_to(extract_dir)
          zf.write(file_path, arcname)

    # Note: We are not signing or zipaligning here as this is an intermediate step
    # usually. But if it's the final step, pipeline should handle signing.
    return True
  except Exception as e:
    ctx.log(f"media_optimizer: repackaging error: {e}")
    if output_apk.exists():
      output_apk.unlink()
    return False


def _get_tool_availability(ctx: Context) -> dict[str, bool]:
  """Check availability of optimization tools."""
  tools = {
    "pngquant": check_dependencies(["pngquant"])[0],
    "optipng": check_dependencies(["optipng"])[0],
    "jpegoptim": check_dependencies(["jpegoptim"])[0],
    "ffmpeg": check_dependencies(["ffmpeg"])[0],
  }
  found = [k for k, v in tools.items() if v]
  ctx.log(f"media_optimizer: available tools: {', '.join(found) if found else 'none'}")
  return tools


def _process_images(
  ctx: Context, extract_dir: Path, tools: dict[str, bool], executor: Executor
) -> dict[str, int]:
  """
  Process and optimize images in extracted APK.

  ⚡ Optimized: Uses shared ProcessPoolExecutor.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with extracted APK contents.
      tools: Tool availability dict.
      executor: Shared process pool executor.

  Returns:
      Dictionary with counts of optimized files.
  """
  stats = {"png": 0, "jpg": 0}

  # ⚡ Perf: Single directory traversal for both formats
  png_files = []
  jpg_files = []
  for root, _, files in os.walk(extract_dir):
    root_path = Path(root)
    for file in files:
      lower_name = file.lower()
      if lower_name.endswith(".png"):
        png_files.append(root_path / file)
      elif lower_name.endswith((".jpg", ".jpeg")):
        jpg_files.append(root_path / file)

  ctx.log(f"media_optimizer: found {len(png_files)} PNG, {len(jpg_files)} JPEG files")

  # Early return if no files to process
  if not png_files and not jpg_files:
    ctx.log("media_optimizer: no images to optimize")
    return stats

  # Check tool availability
  has_pngquant = tools.get("pngquant", False)
  has_optipng = tools.get("optipng", False)
  has_jpegoptim = tools.get("jpegoptim", False)

  # Get PNG optimizer preference from options (default: optipng if available)
  png_optimizer = ctx.options.get("png_optimizer", "optipng")

  if not has_pngquant and not has_optipng and not has_jpegoptim:
    ctx.log(
      "media_optimizer: no optimization tools available, skipping image optimization"
    )
    return stats

  futures = {}

  # Submit PNG optimization tasks based on available tools and preference
  if png_files:
    if png_optimizer == "optipng" and has_optipng:
      ctx.log("media_optimizer: using optipng for PNG optimization (lossless)")
      optimization_level_opt = ctx.options.get("optipng_level", 7)
      optimization_level = (
        optimization_level_opt if isinstance(optimization_level_opt, int) else 7
      )
      for png in png_files:
        future = executor.submit(_optimize_png_optipng_worker, png, optimization_level)
        futures[future] = ("png", png)
    elif png_optimizer == "pngquant" and has_pngquant:
      ctx.log("media_optimizer: using pngquant for PNG optimization (lossy)")
      for png in png_files:
        future = executor.submit(_optimize_png_worker, png)
        futures[future] = ("png", png)
    elif has_optipng:
      # Fallback to optipng if available
      ctx.log("media_optimizer: using optipng for PNG optimization (lossless)")
      optimization_level_opt = ctx.options.get("optipng_level", 7)
      optimization_level = (
        optimization_level_opt if isinstance(optimization_level_opt, int) else 7
      )
      for png in png_files:
        future = executor.submit(_optimize_png_optipng_worker, png, optimization_level)
        futures[future] = ("png", png)
    elif has_pngquant:
      # Fallback to pngquant if available
      ctx.log("media_optimizer: using pngquant for PNG optimization (lossy)")
      for png in png_files:
        future = executor.submit(_optimize_png_worker, png)
        futures[future] = ("png", png)
    else:
      ctx.log("media_optimizer: no PNG optimization tools available")

  # Submit JPEG optimization tasks
  if has_jpegoptim and jpg_files:
    for jpg in jpg_files:
      future = executor.submit(_optimize_jpg_worker, jpg)
      futures[future] = ("jpg", jpg)

  # Process results as they complete with timeout for stuck processes
  total_timeout = 900 if futures else 1  # overall timeout to avoid hanging indefinitely
  for future in as_completed(futures, timeout=total_timeout):
    file_type, _ = futures[future]
    try:
      _, success = future.result(timeout=60)  # 60 second timeout per future
      if success:
        stats[file_type] += 1
    except Exception as e:
      ctx.log(f"media_optimizer: optimization failed for {futures[future][1]}: {e}")

  if not has_jpegoptim:
    ctx.log("media_optimizer: jpegoptim not available, skipped JPEG optimization")

  ctx.log(f"media_optimizer: optimized {stats['png']} PNG, {stats['jpg']} JPEG files")
  return stats


def _process_audio(
  ctx: Context, extract_dir: Path, tools: dict[str, bool], executor: Executor
) -> int:
  """
  Process and optimize audio files in extracted APK.

  ⚡ Optimized: Uses shared ProcessPoolExecutor.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with extracted APK contents.
      tools: Tool availability dict.
      executor: Shared process pool executor.

  Returns:
      Number of optimized audio files.
  """
  if not tools.get("ffmpeg", False):
    ctx.log("media_optimizer: ffmpeg not available, skipping audio optimization")
    return 0

  # ⚡ Perf: Single directory traversal for all audio types
  audio_files = []
  for root, _, files in os.walk(extract_dir):
    root_path = Path(root)
    for file in files:
      lower_name = file.lower()
      if lower_name.endswith((".mp3", ".ogg")):
        audio_files.append(root_path / file)
  ctx.log(f"media_optimizer: found {len(audio_files)} audio files")

  if not audio_files:
    return 0

  ctx.log("media_optimizer: optimizing audio using shared executor")

  optimized = 0
  futures = {
    executor.submit(_optimize_audio_worker, audio): audio for audio in audio_files
  }
  for future in as_completed(futures):
    _, success = future.result()
    if success:
      optimized += 1

  ctx.log(f"media_optimizer: optimized {optimized} audio files")
  return optimized


def _filter_dpi_resources(
  ctx: Context, extract_dir: Path, target_dpis: list[str]
) -> int:
  """
  Remove drawable resources for non-target DPIs.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with extracted APK contents.
      target_dpis: List of target DPI identifiers (e.g., ['xhdpi', 'xxhdpi']).

  Returns:
      Number of folders removed.
  """
  # Find res directory
  res_dir = extract_dir / "res"
  if not res_dir.exists():
    ctx.log("media_optimizer: no res/ directory found")
    return 0

  # Normalize target DPIs
  target_dpis_set = {dpi.lower().strip() for dpi in target_dpis}

  # Always keep nodpi and default drawable
  target_dpis_set.add("nodpi")

  ctx.log(f"media_optimizer: keeping DPIs: {', '.join(sorted(target_dpis_set))}")

  removed_count = 0
  removed_folders = []

  # Find all drawable folders
  for drawable_dir in res_dir.glob("drawable-*"):
    # Extract DPI qualifier from folder name (e.g., drawable-xhdpi-v4 -> xhdpi)
    folder_name = drawable_dir.name
    parts = folder_name.split("-")

    if len(parts) < 2:
      continue

    # Check if any part matches a known DPI
    folder_dpi = None
    for part in parts[1:]:  # Skip "drawable" prefix
      if part in DPI_FOLDERS:
        folder_dpi = part
        break

    # Remove folder if DPI not in target set
    if folder_dpi and folder_dpi not in target_dpis_set:
      shutil.rmtree(drawable_dir)
      removed_folders.append(folder_name)
      removed_count += 1

  if removed_folders:
    ctx.log(
      f"media_optimizer: removed {removed_count} DPI folders: {', '.join(removed_folders)}"
    )
  else:
    ctx.log("media_optimizer: no DPI folders removed")

  return removed_count


def run(ctx: Context) -> None:
  """
  Execute media optimization and DPI filtering.

  Optimizes images (PNG/JPG) and audio (MP3/OGG) files, and removes
  non-target DPI resources to reduce APK size.

  Args:
      ctx: Pipeline context.
  """
  # Get options
  optimize_images = ctx.options.get("optimize_images", False)
  optimize_audio = ctx.options.get("optimize_audio", False)
  target_dpi = ctx.options.get("target_dpi")

  # Skip if nothing requested
  if not (optimize_images or optimize_audio or target_dpi):
    ctx.log("media_optimizer: no operations requested; skipping.")
    return

  apk = require_input_apk(ctx)
  ctx.log(
    f"media_optimizer: starting (images={optimize_images}, audio={optimize_audio}, dpi={target_dpi})"
  )

  # Check tool availability
  tools = _get_tool_availability(ctx)

  # Create working directory
  work_dir = ctx.work_dir / "media_optimizer"
  work_dir.mkdir(parents=True, exist_ok=True)
  extract_dir = work_dir / "extracted"

  # Extract APK
  if not _extract_apk(ctx, apk, extract_dir):
    ctx.log("media_optimizer: extraction failed, aborting")
    return

  # Initialize metadata
  if "media_optimizer" not in ctx.metadata:
    ctx.metadata["media_optimizer"] = {}

  # ⚡ Perf: Shared executor for media operations (images and audio)
  # This avoids creating separate process pools for each operation, reducing overhead
  if optimize_images or optimize_audio:
    max_workers = get_optimal_process_workers()
    ctx.log(f"media_optimizer: initializing shared executor with {max_workers} workers")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
      # Process images
      if optimize_images:
        image_stats = _process_images(ctx, extract_dir, tools, executor)
        ctx.metadata["media_optimizer"]["images"] = image_stats

      # Process audio
      if optimize_audio:
        audio_count = _process_audio(ctx, extract_dir, tools, executor)
        ctx.metadata["media_optimizer"]["audio"] = audio_count

  # Filter DPI resources
  if target_dpi:
    # Parse target DPI (can be comma-separated)
    if isinstance(target_dpi, str):
      target_dpis = [d.strip() for d in target_dpi.split(",")]
    else:
      target_dpis = target_dpi

    dpi_removed = _filter_dpi_resources(ctx, extract_dir, target_dpis)
    ctx.metadata["media_optimizer"]["dpi_folders_removed"] = dpi_removed

  # Repackage APK
  output_apk = ctx.output_dir / f"{apk.stem}.optimized.apk"
  if _repackage_apk(ctx, extract_dir, output_apk):
    ctx.set_current_apk(output_apk)
    ctx.log(f"media_optimizer: pipeline will continue with {output_apk}")

    # Calculate size reduction
    original_size = apk.stat().st_size
    optimized_size = output_apk.stat().st_size
    reduction = original_size - optimized_size
    reduction_pct = (reduction / original_size) * 100 if original_size > 0 else 0

    ctx.log(
      f"media_optimizer: size reduction: {reduction / 1024 / 1024:.2f} MB ({reduction_pct:.1f}%)"
    )
    ctx.metadata["media_optimizer"]["size_reduction"] = {
      "bytes": reduction,
      "percentage": reduction_pct,
    }
  else:
    ctx.log(
      "media_optimizer: repackaging failed, pipeline will continue with original APK"
    )
