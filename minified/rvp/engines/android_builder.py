from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ..utils import TIMEOUT_BUILD
from ..utils import check_dependencies
from ..utils import find_latest_apk
from ..utils import run_command


def run(ctx):
  L = "gradlew"
  K = "gradle"
  J = "android_builder"
  A = ctx
  A.log("android_builder: starting Gradle compilation")
  D = A.options.get(J, {})
  G = D.get("android_source_dir", A.metadata.get("source_project_path"))
  if not G:
    A.log(
      "android_builder: ERROR - 'android_source_dir' option or 'source_project_path' metadata is missing",
      level=logging.ERROR,
    )
    raise ValueError("Android source project directory not specified")
  B = Path(G)
  if not B.is_dir():
    A.log(
      f"android_builder: ERROR - Source directory not found: {B}", level=logging.ERROR
    )
    raise ValueError(f"Android source project directory not found: {B}")
  M, Q = check_dependencies([K])
  if not M and not (B / L).exists():
    A.log(
      "android_builder: ERROR - Gradle or gradlew not found in PATH.",
      level=logging.ERROR,
    )
    raise FileNotFoundError("Gradle dependency missing")
  E = D.get("android_build_task", "assembleRelease")
  N = ["./gradlew"] if (B / L).exists() else [K]
  O = N + [E]
  A.log(f"android_builder: Running task '{E}' in {B.name}")
  try:
    run_command(O, A, cwd=B, timeout=TIMEOUT_BUILD)
  except subprocess.CalledProcessError as P:
    A.log(f"android_builder: Gradle build failed: {P.returncode}", level=logging.ERROR)
    raise
  F = D.get("android_output_pattern", "**/*release.apk")
  H = list(B.glob(F))
  if not H:
    A.log(
      f"android_builder: No output file found matching pattern: {F}",
      level=logging.ERROR,
    )
    raise FileNotFoundError(f"No build output found matching pattern: {F}")
  I = find_latest_apk(B) or max(H, key=lambda p: p.stat().st_mtime)
  C = A.output_dir / f"{B.name}-{I.name}"
  shutil.copy2(I, C)
  A.set_current_apk(C)
  A.log(f"android_builder: Build successful → {C}")
  A.metadata[J] = {"source_dir": str(B), "task": E, "output_apk": str(C)}
