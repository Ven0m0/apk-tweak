"""ReVanced patching engine with multi-patch and optimization support."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

from ..context import Context
from ..optimizer import optimize_apk
from ..utils import TIMEOUT_PATCH, check_dependencies, run_command


def _build_revanced_cli_cmd(
  ctx: Context, input_apk: Path, output_apk: Path
) -> list[str]:
  """
  Build revanced-cli command from context options.

  Supports both binary CLI and JAR-based approaches.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK path.
      output_apk: Output APK path.

  Returns:
      Command list for subprocess execution.
  """
  # Check if using binary CLI or JAR
  if shutil.which("revanced-cli"):
    cmd = ["revanced-cli", "patch"]
  else:
    tools = ctx.options.get("tools", {})
    cli_jar = Path(tools.get("revanced_cli", "revanced-cli.jar"))
    cmd = ["java", "-jar", str(cli_jar), "patch"]

  # Patches
  patches: Any = ctx.options.get("revanced_patches", [])
  for patch in patches:
    if isinstance(patch, str):
      cmd.extend(["-p", f"patches/revanced/{patch}.rvp"])
    elif isinstance(patch, dict):
      patch_name = cast(str, patch["name"])
      cmd.extend(["-p", f"patches/revanced/{patch_name}.rvp"])
      # Add options
      for key, value in patch.get("options", {}).items():
        if value is True:
          cmd.append(f"-O{key}")
        elif value:
          cmd.append(f"-O{key}={value}")

  # Excludes
  exclude_patches: Any = ctx.options.get("revanced_exclude_patches", [])
  for exclude in exclude_patches:
    cmd.extend(["-e", str(exclude)])

  # Exclusive mode
  if ctx.options.get("revanced_exclusive", False):
    cmd.append("--exclusive")

  # Signing
  keystore_opts = ctx.options.get("revanced_keystore")
  if keystore_opts:
    keystore_dict = cast(dict[str, Any], keystore_opts)
    cmd.extend(
      [
        "--keystore",
        str(keystore_dict["path"]),
        "--keystore-entry-alias",
        str(keystore_dict["alias"]),
        "--keystore-password",
        str(keystore_dict["password"]),
        "--keystore-entry-password",
        str(keystore_dict.get("entry_password", keystore_dict["password"])),
      ]
    )

  # Output
  cmd.extend(["-o", str(output_apk), str(input_apk)])
  return cmd


def _run_revanced_cli(ctx: Context, input_apk: Path, output_apk: Path) -> bool:
  """
  Execute ReVanced CLI patching with binary command.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK path.
      output_apk: Output APK path.

  Returns:
      True if successful, False otherwise.
  """
  cmd = _build_revanced_cli_cmd(ctx, input_apk, output_apk)
  ctx.log(f"revanced: running CLI → {output_apk.name}")

  try:
    result = run_command(cmd, ctx, timeout=TIMEOUT_PATCH, check=False)

    if result.returncode == 0 and output_apk.exists():
      ctx.log("revanced: CLI patching successful")
      return True
    ctx.log(f"revanced: CLI failed (exit code: {result.returncode})")
    return False

  except (OSError, subprocess.SubprocessError) as e:
    ctx.log(f"revanced: CLI error: {e}")
    return False


def _create_stub_apk(
  ctx: Context, input_apk: Path, patch_bundles_count: int
) -> None:
  """
  Create stub APK when ReVanced tools are not available.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK file to copy.
      patch_bundles_count: Number of patch bundles configured.
  """
  out_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"
  shutil.copy2(input_apk, out_apk)
  ctx.set_current_apk(out_apk)
  ctx.metadata["revanced"] = {
    "patch_bundles_applied": patch_bundles_count,
    "optimized": False,
    "final_apk": str(out_apk),
    "stub_mode": True,
  }
  ctx.log(f"revanced: stub mode - copied to {out_apk}")


def run(ctx: Context) -> None:
  """
  Execute ReVanced patch engine with multiple approaches.

  Supports:
  - Binary revanced-cli command (preferred)
  - JAR-based patching with multiple patch bundles
  - Custom patches with options and exclusions
  - APK optimization (debloat, minify, zipalign)
  - Keystore signing
  - Exclusive patching mode

  Args:
      ctx: Pipeline context.

  Options:
      revanced_patches: List of patches (str or dict with options)
      revanced_exclude_patches: List of patches to exclude
      revanced_patch_bundles: List of patch bundle JARs (legacy)
      revanced_exclusive: Enable exclusive mode
      revanced_keystore: Dict with path, alias, password
      revanced_optimize: Enable optimization (default: True)
      revanced_debloat: Enable debloating (default: True)
      revanced_minify: Enable minification (default: True)

  Raises:
      ValueError: If no input APK is available.
  """
  ctx.log("revanced: starting patcher")
  input_apk = ctx.current_apk or ctx.input_apk
  if not input_apk:
    raise ValueError("No input APK found in context")

  # Check dependencies
  deps_ok, missing_deps = check_dependencies(["revanced-cli", "java"])
  if not deps_ok:
    ctx.log(f"revanced: Missing dependencies: {', '.join(missing_deps)}")
    ctx.log("revanced: Install with: yay -S revanced-cli-bin jdk17-openjdk")
    ctx.log("revanced: Falling back to stub mode")
    _create_stub_apk(ctx, input_apk, 0)
    return

  # Try binary CLI approach first (luniume-style)
  use_cli = ctx.options.get("revanced_use_cli", True)
  if use_cli and shutil.which("revanced-cli"):
    output_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"
    if _run_revanced_cli(ctx, input_apk, output_apk):
      # CLI succeeded, optionally optimize
      optimize_enabled = ctx.options.get("revanced_optimize", False)
      if optimize_enabled:
        ctx.log("revanced: Starting optimization phase")
        optimized_apk = ctx.output_dir / f"{input_apk.stem}.revanced-opt.apk"
        optimize_apk(
          input_apk=output_apk,
          output_apk=optimized_apk,
          ctx=ctx,
          debloat=ctx.options.get("revanced_debloat", True),
          minify=ctx.options.get("revanced_minify", True),
        )
        ctx.set_current_apk(optimized_apk)
      else:
        ctx.set_current_apk(output_apk)

      ctx.metadata["revanced"] = {
        "method": "cli",
        "patched_apk": str(ctx.current_apk),
        "patches": ctx.options.get("revanced_patches", []),
        "optimized": optimize_enabled,
      }
      return

  # Fall back to JAR-based multi-bundle approach
  ctx.log("revanced: using JAR-based multi-patch pipeline")

  # Get configuration
  tools = ctx.options.get("tools", {})
  tools_dict = cast(dict[str, Any], tools)
  cli_jar = Path(tools_dict.get("revanced_cli", "revanced-cli.jar"))
  integrations_apk = Path(
    tools_dict.get("revanced_integrations", "integrations.apk")
  )
  # Support multiple patch bundles
  patch_bundles_obj = ctx.options.get("revanced_patch_bundles", [])
  patch_bundles: list[str] = cast(list[str], patch_bundles_obj)
  # Fallback to single patch bundle for backward compatibility
  if not patch_bundles:
    patches_path = tools_dict.get("patches", "patches.jar")
    if patches_path:
      patch_bundles = [str(patches_path)]

  if not patch_bundles:
    ctx.log("revanced: No patch bundles specified, using stub mode")
    _create_stub_apk(ctx, input_apk, 0)
    return
  # Verify tools exist (production mode)
  if not cli_jar.exists():
    ctx.log(f"revanced: CLI jar not found at {cli_jar}, using stub mode")
    _create_stub_apk(ctx, input_apk, len(patch_bundles))
    return
  # Apply patches sequentially
  current_apk = input_apk
  work_dir = ctx.work_dir / "revanced"
  work_dir.mkdir(parents=True, exist_ok=True)
  for idx, patch_bundle_str in enumerate(patch_bundles, 1):
    patch_jar = Path(patch_bundle_str)
    if not patch_jar.exists():
      ctx.log(f"revanced: Patch bundle not found: {patch_jar}, skipping")
      continue
    ctx.log(
      f"revanced: Applying patch bundle {idx}/{len(patch_bundles)}: {patch_jar.name}"
    )
    # Determine output name
    if idx == len(patch_bundles):
      # Last patch - use final name
      patched_apk = work_dir / f"{input_apk.stem}.patched.apk"
    else:
      # Intermediate patch
      patched_apk = work_dir / f"{input_apk.stem}.patch{idx}.apk"
    # Build ReVanced CLI command
    cmd = [
      "java",
      "-jar",
      str(cli_jar),
      "patch",
      "--patch-bundle",
      str(patch_jar),
      "--out",
      str(patched_apk),
    ]
    # Add integrations if available
    if integrations_apk.exists():
      cmd.extend(["--merge", str(integrations_apk)])
    # Add include/exclude patches if specified
    include_patches = ctx.options.get("revanced_include_patches", [])
    exclude_patches = ctx.options.get("revanced_exclude_patches", [])
    for patch in include_patches:
      cmd.extend(["--include", patch])
    for patch in exclude_patches:
      cmd.extend(["--exclude", patch])
    # Add current APK as input
    cmd.append(str(current_apk))
    # Execute patching
    run_command(cmd, ctx)
    # Update current APK for next iteration
    current_apk = patched_apk
  # Optimization phase
  optimize_enabled = ctx.options.get("revanced_optimize", True)
  if optimize_enabled:
    ctx.log("revanced: Starting optimization phase")
    optimized_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"
    # Run full optimization pipeline
    optimize_apk(
      input_apk=current_apk,
      output_apk=optimized_apk,
      ctx=ctx,
      debloat=ctx.options.get("revanced_debloat", True),
      minify=ctx.options.get("revanced_minify", True),
    )
    ctx.set_current_apk(optimized_apk)
    ctx.log(f"revanced: Optimization complete - {optimized_apk}")
  else:
    # No optimization - just rename to final name
    final_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"
    current_apk.rename(final_apk)
    ctx.set_current_apk(final_apk)
    ctx.log(f"revanced: Patching complete (no optimization) - {final_apk}")
  # Store metadata
  ctx.metadata["revanced"] = {
    "method": "jar-multi-bundle",
    "patch_bundles_applied": len(patch_bundles),
    "optimized": optimize_enabled,
    "final_apk": str(ctx.current_apk),
  }
