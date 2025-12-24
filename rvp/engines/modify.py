"""APK Modifier engine with icon changes, URL replacement, and custom signing.

Inspired by charwasp/modify project (https://github.com/charwasp/modify).
Provides advanced APK modification capabilities including:
- Icon modification via ImageMagick
- Server URL replacement in Smali code
- Custom keystore signing
- APK decompilation and recompilation
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from typing import cast

from ..context import Context
from ..utils import TIMEOUT_PATCH
from ..utils import check_dependencies
from ..utils import require_input_apk
from ..utils import run_command


def _run_apktool(
  ctx: Context, args: list[str], success_path: Path, action: str
) -> bool:
  """
  Run apktool with shared error handling and logging.

  Args:
      ctx: Pipeline context.
      args: Apktool arguments.
      success_path: Path that should exist on success.
      action: Description for logging.

  Returns:
      True if the command succeeds, False otherwise.
  """
  ctx.log(f"modify: {action} with apktool")

  cmd = ["apktool", *args]

  try:
    run_command(cmd, ctx, timeout=TIMEOUT_PATCH)
    return success_path.exists()
  except (subprocess.SubprocessError, OSError) as e:
    ctx.log(f"modify: {action} failed: {e}")
    return False


def _modify_icon(ctx: Context, decompiled_dir: Path, icon_path: Path | None) -> bool:
  """
  Modify APK icon using ImageMagick.

  Args:
      ctx: Pipeline context.
      decompiled_dir: Path to decompiled APK directory.
      icon_path: Path to new icon file.

  Returns:
      True if successful, False otherwise.
  """
  if not icon_path or not icon_path.exists():
    ctx.log("modify: No icon specified or icon file not found")
    return False

  # Check for ImageMagick
  if not shutil.which("magick") and not shutil.which("convert"):
    ctx.log("modify: ImageMagick not found, skipping icon modification")
    return False

  # Find icon directories in decompiled APK
  res_dir = decompiled_dir / "res"
  if not res_dir.exists():
    ctx.log("modify: res directory not found in decompiled APK")
    return False

  icon_dirs = [
    d
    for d in res_dir.iterdir()
    if d.is_dir() and (d.name.startswith("mipmap-") or d.name.startswith("drawable-"))
  ]

  if not icon_dirs:
    ctx.log("modify: No icon directories found")
    return False

  ctx.log(f"modify: Replacing icons in {len(icon_dirs)} directories")

  magick_cmd = "magick" if shutil.which("magick") else "convert"

  for icon_dir in icon_dirs:
    for icon_file in icon_dir.glob("ic_launcher*"):
      try:
        # Resize icon to match original dimensions
        result = subprocess.run(
          [
            magick_cmd,
            str(icon_path),
            "-resize",
            "512x512",
            str(icon_file),
          ],
          capture_output=True,
          text=True,
          check=False,
        )
        if result.returncode == 0:
          ctx.log(f"  ✓ Updated {icon_file.relative_to(decompiled_dir)}")
        else:
          ctx.log(f"  ✗ Failed to update {icon_file.name}")
      except OSError as e:
        ctx.log(f"  ✗ Error updating {icon_file.name}: {e}")

  return True


def _replace_server_url(
  ctx: Context, decompiled_dir: Path, old_url: str, new_url: str
) -> bool:
  """
  Replace server URLs in Smali code.

  ⚡ Optimized: Uses grep to pre-filter files containing the URL before loading.

  Args:
      ctx: Pipeline context.
      decompiled_dir: Path to decompiled APK directory.
      old_url: URL to replace.
      new_url: Replacement URL.

  Returns:
      True if successful, False otherwise.
  """
  smali_dir = decompiled_dir / "smali"
  smali_classes_dir = decompiled_dir / "smali_classes2"

  search_dirs = [d for d in [smali_dir, smali_classes_dir] if d.exists()]

  if not search_dirs:
    ctx.log("modify: No smali directories found")
    return False

  ctx.log(f"modify: Replacing '{old_url}' with '{new_url}' in Smali files")

  files_modified = 0

  # ⚡ Perf: First use grep to find files containing the URL
  # This avoids loading thousands of files into memory unnecessarily
  candidate_files: list[Path] = []
  for search_dir in search_dirs:
    try:
      # Use grep to find files containing the URL (much faster than Python iteration)
      result = subprocess.run(
        ["grep", "-rl", "--include=*.smali", old_url, str(search_dir)],
        capture_output=True,
        text=True,
        check=False,
      )
      if result.returncode == 0:
        # Grep found matches
        candidate_files.extend(
          Path(line.strip()) for line in result.stdout.splitlines() if line.strip()
        )
    except (OSError, subprocess.SubprocessError):
      # Grep not available or failed, fall back to manual search
      ctx.log("modify: grep not available, falling back to slower file-by-file search")
      candidate_files = list(search_dir.rglob("*.smali"))
      break

  if not candidate_files:
    ctx.log("modify: No files contain the target URL")
    return False

  ctx.log(f"modify: Found {len(candidate_files)} files to check")

  # Now only process files that potentially contain the URL
  for smali_file in candidate_files:
    try:
      content = smali_file.read_text(encoding="utf-8", errors="ignore")
      if old_url in content:
        new_content = content.replace(old_url, new_url)
        smali_file.write_text(new_content, encoding="utf-8")
        files_modified += 1
        ctx.log(f"  ✓ Modified {smali_file.relative_to(decompiled_dir)}")
    except (OSError, UnicodeError) as e:
      ctx.log(f"  ✗ Error processing {smali_file.name}: {e}")

  ctx.log(f"modify: Modified {files_modified} Smali file(s)")
  return files_modified > 0


def _decompile_apk(ctx: Context, input_apk: Path, output_dir: Path) -> bool:
  """
  Decompile APK using apktool.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK path.
      output_dir: Output directory for decompiled files.

  Returns:
      True if successful, False otherwise.
  """
  return _run_apktool(
    ctx,
    ["d", "-f", "-o", str(output_dir), str(input_apk)],
    output_dir,
    "Decompiling APK",
  )


def _recompile_apk(ctx: Context, decompiled_dir: Path, output_apk: Path) -> bool:
  """
  Recompile APK using apktool.

  Args:
      ctx: Pipeline context.
      decompiled_dir: Decompiled APK directory.
      output_apk: Output APK path.

  Returns:
      True if successful, False otherwise.
  """
  return _run_apktool(
    ctx,
    ["b", "-f", "-o", str(output_apk), str(decompiled_dir)],
    output_apk,
    "Recompiling APK",
  )


def _sign_apk(ctx: Context, unsigned_apk: Path, signed_apk: Path) -> bool:
  """
  Sign APK with custom or default keystore.

  Args:
      ctx: Pipeline context.
      unsigned_apk: Unsigned APK path.
      signed_apk: Signed APK output path.

  Returns:
      True if successful, False otherwise.
  """
  ctx.log("modify: Signing APK")

  # Get keystore options from context
  keystore_opts = cast(dict[str, Any], ctx.options.get("modify_keystore", {}))
  keystore_path = Path(str(keystore_opts.get("path", ctx.work_dir / "keystore.jks")))
  keystore_alias = str(keystore_opts.get("alias", "key0"))
  keystore_pass = str(keystore_opts.get("password", "android"))

  # Create keystore if it doesn't exist
  if not keystore_path.exists():
    ctx.log(f"modify: Creating new keystore at {keystore_path}")
    # Use environment variables to avoid password exposure in process listings
    keytool_cmd = [
      "keytool",
      "-genkey",
      "-v",
      "-keystore",
      str(keystore_path),
      "-alias",
      keystore_alias,
      "-keyalg",
      "RSA",
      "-keysize",
      "2048",
      "-validity",
      "10000",
      "-storepass:env",
      "KEYSTORE_PASS",
      "-keypass:env",
      "KEYSTORE_PASS",
      "-dname",
      "CN=APK Modifier, OU=Dev, O=APK, L=City, S=State, C=US",
    ]

    try:
      # Pass password via environment variable to avoid exposure
      env = os.environ.copy()
      env["KEYSTORE_PASS"] = keystore_pass
      run_command(keytool_cmd, ctx, env=env)
    except (subprocess.SubprocessError, OSError) as e:
      ctx.log(f"modify: Keystore creation failed: {e}")
      return False

  # Sign APK using apksigner with environment variable for password
  sign_cmd = [
    "apksigner",
    "sign",
    "--ks",
    str(keystore_path),
    "--ks-key-alias",
    keystore_alias,
    "--ks-pass",
    "pass:env:KEYSTORE_PASS",
    "--out",
    str(signed_apk),
    str(unsigned_apk),
  ]

  try:
    # Pass password via environment variable to avoid exposure
    env = os.environ.copy()
    env["KEYSTORE_PASS"] = keystore_pass
    run_command(sign_cmd, ctx, timeout=TIMEOUT_PATCH, env=env)
    return signed_apk.exists()
  except (subprocess.SubprocessError, OSError) as e:
    ctx.log(f"modify: Signing failed: {e}")
    return False


def run(ctx: Context) -> None:
  """
  Execute APK Modifier engine.

  Workflow:
  1. Decompile APK with apktool
  2. Modify icon (if specified and ImageMagick available)
  3. Replace server URLs (if specified)
  4. Recompile modified APK
  5. Sign with custom keystore

  Args:
      ctx: Pipeline context.

  Options:
      modify_icon: Path to new icon file (PNG/SVG)
      modify_server_url_old: Old server URL to replace
      modify_server_url_new: New server URL
      modify_keystore: Dict with path, alias, password
      modify_use_apkeditor: Use apkeditor instead of apktool (default: False)

  Raises:
      ValueError: If no input APK is available.
      RuntimeError: If dependencies are missing.
  """
  ctx.log("modify: starting APK modifier")

  input_apk = require_input_apk(ctx)

  # Check dependencies
  required_deps = ["apktool", "java", "keytool", "apksigner"]
  deps_ok, missing_deps = check_dependencies(required_deps)

  if not deps_ok:
    raise RuntimeError(
      f"modify: Missing dependencies: {', '.join(missing_deps)}\n"
      f"Install with: apt-get install -y apktool default-jdk apksigner\n"
      f"Or on Arch: pacman -S android-tools jdk-openjdk"
    )

  # Create work directory
  modify_work = ctx.work_dir / "modify"
  modify_work.mkdir(parents=True, exist_ok=True)

  decompiled_dir = modify_work / "decompiled"
  unsigned_apk = modify_work / f"{input_apk.stem}.unsigned.apk"
  final_apk = ctx.output_dir / f"{input_apk.stem}.modified.apk"

  # Step 1: Decompile APK
  if not _decompile_apk(ctx, input_apk, decompiled_dir):
    raise RuntimeError("modify: Decompilation failed")

  # Step 2: Modify icon (optional)
  icon_path_obj = ctx.options.get("modify_icon")
  if icon_path_obj:
    icon_path = Path(cast(str, icon_path_obj))
    _modify_icon(ctx, decompiled_dir, icon_path)

  # Step 3: Replace server URLs (optional)
  old_url = ctx.options.get("modify_server_url_old")
  new_url = ctx.options.get("modify_server_url_new")
  if old_url and new_url:
    _replace_server_url(ctx, decompiled_dir, str(old_url), str(new_url))

  # Step 4: Recompile APK
  if not _recompile_apk(ctx, decompiled_dir, unsigned_apk):
    raise RuntimeError("modify: Recompilation failed")

  # Step 5: Sign APK
  if not _sign_apk(ctx, unsigned_apk, final_apk):
    raise RuntimeError("modify: Signing failed")

  # Update context
  ctx.set_current_apk(final_apk)

  # Get keystore path for metadata
  keystore_meta = cast(dict[str, Any], ctx.options.get("modify_keystore", {}))
  keystore_path_str = str(keystore_meta.get("path", "auto-generated"))

  ctx.metadata["modify"] = {
    "icon_modified": bool(icon_path_obj),
    "url_replaced": bool(old_url and new_url),
    "signed_apk": str(final_apk),
    "keystore": keystore_path_str,
  }

  ctx.log(f"modify: APK modification complete → {final_apk}")
