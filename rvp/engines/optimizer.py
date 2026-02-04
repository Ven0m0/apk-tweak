"""Multi-purpose APK optimizer engine combining various optimization techniques."""

from __future__ import annotations

import os
import re
import shutil
import zipfile
from pathlib import Path

from ..context import Context
from ..utils import require_input_apk


def _extract_apk_structure(apk_path: Path, extract_dir: Path) -> bool:
  """Extract APK to directory for processing."""
  try:
    with zipfile.ZipFile(apk_path, "r") as zf:
      base_path = extract_dir.resolve()
      for member in zf.infolist():
        member_path = (extract_dir / member.filename).resolve()
        try:
          # Ensure the target path is within the extraction directory
          member_path.relative_to(base_path)
        except ValueError:
          # Detected a path traversal attempt or invalid path
          raise OSError("Illegal file path in APK archive") from None
        zf.extract(member, extract_dir)
    return True
  except (OSError, zipfile.BadZipFile):
    return False


def _repack_apk_optimized(extract_dir: Path, output_apk: Path) -> bool:
  """Repack APK with optimized settings."""
  try:
    # Extensions that are already compressed
    no_compress_exts = {
      ".png",
      ".jpg",
      ".jpeg",
      ".gif",
      ".webp",
      ".mp3",
      ".ogg",
      ".mp4",
      ".so",
      ".ttf",
      ".woff",
      ".woff2",
      ".gz",
      ".xz",
      ".zip",
    }

    with zipfile.ZipFile(output_apk, "w") as zf:
      for file_path in extract_dir.rglob("*"):
        if file_path.is_file():
          arcname = file_path.relative_to(extract_dir)

          if file_path.suffix.lower() in no_compress_exts:
            zf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
          else:
            zf.write(
              file_path,
              arcname,
              compress_type=zipfile.ZIP_DEFLATED,
              compresslevel=6,
            )
    return True
  except (OSError, zipfile.BadZipFile):
    return False


def _remove_debug_symbols(ctx: Context, extract_dir: Path) -> int:
  """Remove debug symbols and unnecessary files."""
  removed_count = 0

  # Patterns that indicate a directory (and all contents) should be removed
  dir_patterns = [
    r".*proguard.*",
    r".*debug.*",
    r".*Debug.*",
    r".*/tests?",
    r".*/test.*",
  ]

  # Patterns for individual files
  file_patterns = [
    r".*\.map$",
    r".*\.log$",
    r".*proguard.*",
    r".*mapping\.txt$",
    r".*debug.*",
    r".*Debug.*",
    r".*/tests?/.*",
    r".*/test.*",
  ]

  # Compile regexes
  dir_combined = "|".join(f"(?:{p})" for p in dir_patterns)
  dir_regex = re.compile(dir_combined, re.IGNORECASE)

  file_combined = "|".join(f"(?:{p})" for p in file_patterns)
  file_regex = re.compile(file_combined, re.IGNORECASE)

  extract_dir_str = str(extract_dir)

  # Use os.walk for efficiency
  for root, dirs, files in os.walk(extract_dir_str, topdown=True):
    # Iterate backwards to allow safely modifying dirs list
    for i in range(len(dirs) - 1, -1, -1):
      d_name = dirs[i]
      d_path = os.path.join(root, d_name)  # noqa: PTH118

      # Check against dir regex
      # We append separator to match patterns expecting trailing slash (like .../tests/...)
      # We check both d_path and d_path + sep to cover various pattern styles
      if dir_regex.match(d_path) or dir_regex.match(d_path + os.sep):
        try:
          # Remove directory tree and count removed files in a single traversal
          count = 0
          for r_root, r_dirs, r_files in os.walk(d_path, topdown=False):
            for f in r_files:
              f_path_inner = os.path.join(r_root, f)  # noqa: PTH118
              os.unlink(f_path_inner)  # noqa: PTH108
              count += 1
            for d in r_dirs:
              os.rmdir(os.path.join(r_root, d))  # noqa: PTH118
          os.rmdir(d_path)
          removed_count += count
          del dirs[i]  # Stop recursing into this dir
        except OSError:
          continue

    for f_name in files:
      f_path = os.path.join(root, f_name)  # noqa: PTH118
      if file_regex.match(f_path):
        try:
          os.unlink(f_path)  # noqa: PTH108
          removed_count += 1
        except OSError:
          continue

  if removed_count > 0:
    ctx.log(f"optimizer: removed {removed_count} debug/symbol files")

  return removed_count


def _minimize_manifest(ctx: Context, extract_dir: Path) -> bool:
  """Minimize AndroidManifest.xml by safely removing comments in text manifests."""
  manifest_path = extract_dir / "AndroidManifest.xml"
  if not manifest_path.exists():
    return False

  try:
    # Read raw bytes first so we do not accidentally corrupt binary AXML manifests.
    raw_content = manifest_path.read_bytes()
  except OSError:
    return False

  try:
    # Decode as UTF-8 without ignoring errors. If this fails, treat it as binary and skip.
    content = raw_content.decode("utf-8")
  except UnicodeDecodeError:
    ctx.log("optimizer: skipping non-text AndroidManifest.xml")
    return False

  # Basic sanity check: only process if it looks like XML text.
  if not content.lstrip().startswith("<"):
    ctx.log("optimizer: AndroidManifest.xml is not plain XML, skipping minimization")
    return False

  # Remove XML comments but leave other whitespace intact to avoid changing semantics.
  content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

  try:
    manifest_path.write_text(content, encoding="utf-8")
    ctx.log("optimizer: minimized AndroidManifest.xml (comments removed)")
    return True
  except OSError:
    return False


def _optimize_resources(ctx: Context, extract_dir: Path) -> int:
  """Optimize resource files by removing unused resources."""
  res_dir = extract_dir / "res"
  if not res_dir.exists():
    return 0

  # Look for potentially unused resource files
  removed_count = 0

  # Walk directory once to remove unwanted files
  # This is significantly faster than using rglob multiple times
  # or even a single rglob("*") which instantiates Path objects for everything
  for root, _, files in os.walk(res_dir):
    for name in files:
      if name == ".DS_Store" or name.endswith("~"):
        file_path = os.path.join(root, name)  # noqa: PTH118
        try:
          os.unlink(file_path)  # noqa: PTH108
          removed_count += 1
        except OSError:
          continue

  if removed_count > 0:
    ctx.log(f"optimizer: removed {removed_count} unnecessary resource files")

  return removed_count


def _remove_locale_resources(
  ctx: Context, extract_dir: Path, keep_locales: list[str]
) -> int:
  """Remove locale-specific resources that are not in the keep list."""
  res_dir = extract_dir / "res"
  if not res_dir.exists():
    return 0

  removed_count = 0
  keep_locales_lower = {loc.lower() for loc in keep_locales}

  # Find all locale-specific resource directories
  for resource_dir in res_dir.iterdir():
    if resource_dir.is_dir() and resource_dir.name.startswith("values-"):
      # Extract locale from directory name (e.g., values-en, values-es-rES)
      locale_part = resource_dir.name[7:]  # Remove "values-" prefix
      locale_prefix = locale_part.split("-")[0].lower()

      if locale_prefix not in keep_locales_lower:
        try:
          shutil.rmtree(resource_dir)
          removed_count += 1
        except OSError:
          continue

  if removed_count > 0:
    ctx.log(f"optimizer: removed {removed_count} locale resource directories")

  return removed_count


def run(ctx: Context) -> None:
  """Execute comprehensive APK optimization pipeline."""
  # Get optimization options
  optimize_general = ctx.options.get("optimize_general", True)
  remove_debug = ctx.options.get("remove_debug_symbols", True)
  minimize_manifest = ctx.options.get("minimize_manifest", True)
  optimize_resources = ctx.options.get("optimize_resources", True)
  keep_locales = ctx.options.get("keep_locales", ["en"])

  if not any([optimize_general, remove_debug, minimize_manifest, optimize_resources]):
    ctx.log("optimizer: no optimization options enabled, skipping")
    return

  apk = require_input_apk(ctx)
  ctx.log(f"optimizer: starting optimization for {apk.name}")

  # Create working directory
  work_dir = ctx.work_dir / "optimizer"
  work_dir.mkdir(parents=True, exist_ok=True)
  extract_dir = work_dir / "extracted"

  # Extract APK
  if not _extract_apk_structure(apk, extract_dir):
    ctx.log("optimizer: failed to extract APK, aborting")
    return

  # Initialize metadata
  if "optimizer" not in ctx.metadata:
    ctx.metadata["optimizer"] = {}

  # Track optimization results
  optimization_results = {
    "original_size": apk.stat().st_size,
    "operations_performed": [],
  }

  # Remove debug symbols
  if remove_debug:
    removed_debug = _remove_debug_symbols(ctx, extract_dir)
    if removed_debug > 0:
      optimization_results["operations_performed"].append(
        {"type": "debug_symbol_removal", "count": removed_debug}
      )

  # Minimize manifest
  if minimize_manifest and _minimize_manifest(ctx, extract_dir):
    optimization_results["operations_performed"].append(
      {"type": "manifest_minimization", "success": True}
    )

  # Optimize resources
  if optimize_resources:
    removed_resources = _optimize_resources(ctx, extract_dir)
    if removed_resources > 0:
      optimization_results["operations_performed"].append(
        {"type": "resource_optimization", "count": removed_resources}
      )

  # Remove locale resources
  if keep_locales and isinstance(keep_locales, list):
    removed_locales = _remove_locale_resources(ctx, extract_dir, keep_locales)
    if removed_locales > 0:
      optimization_results["operations_performed"].append(
        {
          "type": "locale_removal",
          "count": removed_locales,
          "kept_locales": keep_locales,
        }
      )

  # Repackage optimized APK
  output_apk = ctx.output_dir / f"{apk.stem}.optimized.apk"
  if _repack_apk_optimized(extract_dir, output_apk):
    ctx.set_current_apk(output_apk)
    ctx.log(f"optimizer: optimization complete, continuing with {output_apk.name}")

    # Calculate size reduction
    original_size = optimization_results["original_size"]
    optimized_size = output_apk.stat().st_size
    reduction = original_size - optimized_size
    reduction_pct = (reduction / original_size) * 100 if original_size > 0 else 0

    ctx.log(
      f"optimizer: size reduction: {reduction / 1024 / 1024:.2f} MB "
      f"({reduction_pct:.1f}%)"
    )

    optimization_results.update(
      {
        "final_size": optimized_size,
        "size_reduction_bytes": reduction,
        "size_reduction_percentage": reduction_pct,
      }
    )

    ctx.metadata["optimizer"] = optimization_results
  else:
    ctx.log("optimizer: failed to repackage optimized APK, continuing with original")
