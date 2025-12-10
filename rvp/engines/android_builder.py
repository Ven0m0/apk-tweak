"""Android Gradle build engine for compiling source code into an APK/AAB."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..context import Context
from ..utils import (
  TIMEOUT_BUILD,
  check_dependencies,
  find_latest_apk,
  run_command,
)


def run(ctx: Context) -> None:
  """
  Execute the Android Builder engine to compile an APK or AAB.

  It runs `./gradlew assembleRelease` or a specified task on an Android project
  directory specified in options or context metadata.

  Options:
      android_source_dir: Path to the root of the Android project (where build.gradle lives).
      android_build_task: The Gradle task to run (default: assembleRelease).
      android_output_pattern: Glob pattern to find the output file (default: **/*release.apk).

  Args:
      ctx: Pipeline context.

  Raises:
      ValueError: If the source directory is not found.
      FileNotFoundError: If the output APK/AAB is not found.
  """
  ctx.log("android_builder: starting Gradle compilation")

  # Cast to dict for runtime access (TypedDict limitation with nested keys)
  options: dict[str, Any] = ctx.options.get("android_builder", {})  # type: ignore[assignment]

  # 1. Determine Source Directory
  source_dir_str: Any = options.get(
    "android_source_dir", ctx.metadata.get("source_project_path")
  )
  if not source_dir_str:
    ctx.log(
      "android_builder: ERROR - 'android_source_dir' option or 'source_project_path' metadata is missing",
      level=logging.ERROR,
    )
    raise ValueError("Android source project directory not specified")

  source_dir = Path(str(source_dir_str))
  if not source_dir.is_dir():
    ctx.log(
      f"android_builder: ERROR - Source directory not found: {source_dir}",
      level=logging.ERROR,
    )
    raise ValueError(
      f"Android source project directory not found: {source_dir}"
    )

  # 2. Check Dependencies
  deps_ok, _ = check_dependencies(["gradle"])
  if not deps_ok and not (source_dir / "gradlew").exists():
    ctx.log(
      "android_builder: ERROR - Gradle or gradlew not found in PATH.",
      level=logging.ERROR,
    )
    raise FileNotFoundError("Gradle dependency missing")

  # 3. Build Command
  build_task = options.get("android_build_task", "assembleRelease")
  # Prefer using the Gradle Wrapper if it exists
  gradle_cmd = (
    ["./gradlew"] if (source_dir / "gradlew").exists() else ["gradle"]
  )

  cmd = gradle_cmd + [build_task]

  ctx.log(f"android_builder: Running task '{build_task}' in {source_dir.name}")

  try:
    # Execute command, capturing output for logs
    run_command(cmd, ctx, cwd=source_dir, timeout=TIMEOUT_BUILD)

  except subprocess.CalledProcessError as e:
    ctx.log(
      f"android_builder: Gradle build failed: {e.returncode}",
      level=logging.ERROR,
    )
    raise

  # 4. Find Output File
  output_pattern = options.get("android_output_pattern", "**/*release.apk")

  # Search the standard Gradle output location
  output_candidates = list(source_dir.glob(output_pattern))

  if not output_candidates:
    ctx.log(
      f"android_builder: No output file found matching pattern: {output_pattern}",
      level=logging.ERROR,
    )
    raise FileNotFoundError(
      f"No build output found matching pattern: {output_pattern}"
    )

  # Use the most recently modified file as the output APK
  output_apk_path = find_latest_apk(source_dir) or max(
    output_candidates, key=lambda p: p.stat().st_mtime
  )

  # 5. Move to Output Directory and Update Context
  final_apk = ctx.output_dir / f"{source_dir.name}-{output_apk_path.name}"
  shutil.copy2(output_apk_path, final_apk)

  ctx.set_current_apk(final_apk)
  ctx.log(f"android_builder: Build successful → {final_apk}")

  # 6. Store Metadata
  ctx.metadata["android_builder"] = {
    "source_dir": str(source_dir),
    "task": build_task,
    "output_apk": str(final_apk),
  }
