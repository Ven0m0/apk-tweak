"""Media optimization engine for APK size reduction."""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

from ..context import Context

# Constants
DPI_FOLDERS = {
  "ldpi": 120,
  "mdpi": 160,
  "hdpi": 240,
  "xhdpi": 320,
  "xxhdpi": 480,
  "xxxhdpi": 640,
  "tvdpi": 213,
  "nodpi": 0,  # Special case - always keep
}


def _check_dependencies(ctx: Context) -> dict[str, bool]:
  """
  Check availability of optimization tools.

  Args:
      ctx: Pipeline context.

  Returns:
      dict with tool availability status.
  """
  tools = {
    "pngquant": shutil.which("pngquant") is not None,
    "jpegoptim": shutil.which("jpegoptim") is not None,
    "ffmpeg": shutil.which("ffmpeg") is not None,
  }

  missing = [name for name, available in tools.items() if not available]
  if missing:
    ctx.log(f"media_optimizer: missing tools: {', '.join(missing)}")
    ctx.log("media_optimizer: install via package manager (Arch: pacman -S pngquant jpegoptim ffmpeg)")

  return tools


def _optimize_png(ctx: Context, png_path: Path, quality: str = "65-80") -> bool:
  """
  Optimize PNG file using pngquant.

  Args:
      ctx: Pipeline context.
      png_path: Path to PNG file.
      quality: Quality range (default: 65-80 for good compression).

  Returns:
      True if optimization succeeded, False otherwise.
  """
  try:
    # pngquant overwrites with -f flag, quality range ensures good compression
    result = subprocess.run(
      [
        "pngquant",
        "--quality",
        quality,
        "--ext",
        ".png",
        "--force",
        str(png_path),
      ],
      capture_output=True,
      text=True,
      timeout=30,
      check=False,
    )
    return result.returncode == 0
  except (subprocess.TimeoutExpired, Exception) as e:
    ctx.log(f"media_optimizer: PNG optimization failed for {png_path.name}: {e}")
    return False


def _optimize_jpg(ctx: Context, jpg_path: Path, quality: int = 85) -> bool:
  """
  Optimize JPEG file using jpegoptim.

  Args:
      ctx: Pipeline context.
      jpg_path: Path to JPEG file.
      quality: Quality level (default: 85 for good balance).

  Returns:
      True if optimization succeeded, False otherwise.
  """
  try:
    # jpegoptim with --max=quality and --strip-all for metadata removal
    result = subprocess.run(
      ["jpegoptim", f"--max={quality}", "--strip-all", str(jpg_path)],
      capture_output=True,
      text=True,
      timeout=30,
      check=False,
    )
    return result.returncode == 0
  except (subprocess.TimeoutExpired, Exception) as e:
    ctx.log(f"media_optimizer: JPEG optimization failed for {jpg_path.name}: {e}")
    return False


def _optimize_audio(ctx: Context, audio_path: Path, output_path: Path, bitrate: str = "96k") -> bool:
  """
  Optimize audio file using ffmpeg.

  Args:
      ctx: Pipeline context.
      audio_path: Path to input audio file.
      output_path: Path to output audio file.
      bitrate: Target bitrate (default: 96k for good quality).

  Returns:
      True if optimization succeeded, False otherwise.
  """
  try:
    # Detect format and use appropriate codec
    suffix = audio_path.suffix.lower()
    if suffix == ".mp3":
      codec = "libmp3lame"
    elif suffix == ".ogg":
      codec = "libvorbis"
    else:
      return False

    result = subprocess.run(
      [
        "ffmpeg",
        "-i",
        str(audio_path),
        "-codec:a",
        codec,
        "-b:a",
        bitrate,
        "-y",  # Overwrite output
        str(output_path),
      ],
      capture_output=True,
      text=True,
      timeout=60,
      check=False,
    )

    if result.returncode == 0 and output_path.exists():
      # Replace original with optimized version
      shutil.move(output_path, audio_path)
      return True
    return False

  except (subprocess.TimeoutExpired, Exception) as e:
    ctx.log(f"media_optimizer: Audio optimization failed for {audio_path.name}: {e}")
    return False


def _extract_apk(ctx: Context, apk: Path, extract_dir: Path) -> bool:
  """
  Extract APK contents to directory.

  Args:
      ctx: Pipeline context.
      apk: APK file to extract.
      extract_dir: Destination directory.

  Returns:
      True if extraction succeeded, False otherwise.
  """
  try:
    with zipfile.ZipFile(apk, "r") as zf:
      zf.extractall(extract_dir)
    ctx.log(f"media_optimizer: extracted {apk.name} to {extract_dir}")
    return True
  except Exception as e:
    ctx.log(f"media_optimizer: extraction failed: {e}")
    return False


def _repackage_apk(ctx: Context, extract_dir: Path, output_apk: Path) -> bool:
  """
  Repackage directory contents into APK.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with APK contents.
      output_apk: Output APK file path.

  Returns:
      True if repackaging succeeded, False otherwise.
  """
  try:
    with zipfile.ZipFile(output_apk, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
      for file_path in extract_dir.rglob("*"):
        if file_path.is_file():
          arcname = file_path.relative_to(extract_dir)
          zf.write(file_path, arcname)

    ctx.log(f"media_optimizer: repackaged to {output_apk.name}")
    return True
  except Exception as e:
    ctx.log(f"media_optimizer: repackaging failed: {e}")
    return False


def _process_images(ctx: Context, extract_dir: Path, tools: dict[str, bool]) -> dict[str, int]:
  """
  Process and optimize images in extracted APK.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with extracted APK contents.
      tools: Tool availability dict.

  Returns:
      Stats dict with optimization counts.
  """
  stats = {"png": 0, "jpg": 0}

  # Find all image files
  png_files = list(extract_dir.rglob("*.png"))
  jpg_files = list(extract_dir.rglob("*.jpg")) + list(extract_dir.rglob("*.jpeg"))

  ctx.log(f"media_optimizer: found {len(png_files)} PNG, {len(jpg_files)} JPEG files")

  # Optimize PNGs
  if tools.get("pngquant", False):
    for png in png_files:
      if _optimize_png(ctx, png):
        stats["png"] += 1
  else:
    ctx.log("media_optimizer: pngquant not available, skipping PNG optimization")

  # Optimize JPEGs
  if tools.get("jpegoptim", False):
    for jpg in jpg_files:
      if _optimize_jpg(ctx, jpg):
        stats["jpg"] += 1
  else:
    ctx.log("media_optimizer: jpegoptim not available, skipping JPEG optimization")

  ctx.log(f"media_optimizer: optimized {stats['png']} PNG, {stats['jpg']} JPEG files")
  return stats


def _process_audio(ctx: Context, extract_dir: Path, tools: dict[str, bool]) -> int:
  """
  Process and optimize audio files in extracted APK.

  Args:
      ctx: Pipeline context.
      extract_dir: Directory with extracted APK contents.
      tools: Tool availability dict.

  Returns:
      Number of optimized audio files.
  """
  if not tools.get("ffmpeg", False):
    ctx.log("media_optimizer: ffmpeg not available, skipping audio optimization")
    return 0

  # Find all audio files
  audio_files = list(extract_dir.rglob("*.mp3")) + list(extract_dir.rglob("*.ogg"))
  ctx.log(f"media_optimizer: found {len(audio_files)} audio files")

  optimized = 0
  for audio in audio_files:
    temp_output = audio.with_suffix(audio.suffix + ".tmp")
    if _optimize_audio(ctx, audio, temp_output):
      optimized += 1

  ctx.log(f"media_optimizer: optimized {optimized} audio files")
  return optimized


def _filter_dpi_resources(ctx: Context, extract_dir: Path, target_dpis: list[str]) -> int:
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
    ctx.log(f"media_optimizer: removed {removed_count} DPI folders: {', '.join(removed_folders)}")
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

  apk = ctx.current_apk or ctx.input_apk
  ctx.log(f"media_optimizer: starting (images={optimize_images}, audio={optimize_audio}, dpi={target_dpi})")

  # Check tool availability
  tools = _check_dependencies(ctx)

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

  # Process images
  if optimize_images:
    image_stats = _process_images(ctx, extract_dir, tools)
    ctx.metadata["media_optimizer"]["images"] = image_stats

  # Process audio
  if optimize_audio:
    audio_count = _process_audio(ctx, extract_dir, tools)
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

    ctx.log(f"media_optimizer: size reduction: {reduction / 1024 / 1024:.2f} MB ({reduction_pct:.1f}%)")
    ctx.metadata["media_optimizer"]["size_reduction"] = {
      "bytes": reduction,
      "percentage": reduction_pct,
    }
  else:
    ctx.log("media_optimizer: repackaging failed, pipeline will continue with original APK")
