from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from ..utils import check_dependencies
from ..utils import find_latest_apk
from ..utils import require_input_apk


def run(ctx):
  X = "anti_split"
  W = "corex_hook"
  V = "dex_repair"
  U = "merge_skip"
  T = "apktool_mode"
  S = "RKPairip"
  L = "rkpairip"
  G = True
  F = False
  A = ctx
  A.log("rkpairip: Starting APK processing")
  M = require_input_apk(A)
  Y, Z = check_dependencies([S])
  if not Y:
    A.log(
      "rkpairip: RKPairip not found. Install via: pip install Pairip",
      level=logging.ERROR,
    )
    raise FileNotFoundError("RKPairip not installed. Run: pip install Pairip")
  C = A.options.get(L, {})
  N = C.get(T, F)
  O = C.get(U, F)
  P = C.get(V, F)
  Q = C.get(W, F)
  R = C.get(X, F)
  J = A.work_dir / L
  J.mkdir(parents=G, exist_ok=G)
  B = [S, "-i", str(M)]
  if N:
    B.append("-a")
    A.log("rkpairip: Using ApkTool mode")
  if O:
    B.append("-s")
    A.log("rkpairip: Merge skip mode enabled")
  if P:
    B.append("-r")
    A.log("rkpairip: DEX repair enabled")
  if Q:
    B.append("-x")
    A.log("rkpairip: CoreX hook enabled (Unity/Flutter support)")
  if R:
    B.append("-m")
    A.log("rkpairip: Anti-split merge mode enabled")
  A.log(f"rkpairip: Executing command: {' '.join(B)}")
  try:
    H = subprocess.run(B, cwd=J, capture_output=G, text=G, check=G)
    if H.stdout:
      for K in H.stdout.splitlines():
        A.log(f"  {K}")
    if H.stderr:
      for K in H.stderr.splitlines():
        A.log(f"  {K}")
  except subprocess.CalledProcessError as D:
    A.log(f"rkpairip: Command failed with code {D.returncode}", level=logging.ERROR)
    if D.stdout:
      A.log(f"STDOUT: {D.stdout}", level=logging.ERROR)
    if D.stderr:
      A.log(f"STDERR: {D.stderr}", level=logging.ERROR)
    raise
  E = find_latest_apk(J)
  if not E:
    A.log(
      "rkpairip: No output APK found, checking current directory", level=logging.WARNING
    )
    E = find_latest_apk(Path.cwd())
  if E:
    A.log(f"rkpairip: Found output APK: {E.name}")
    I = A.output_dir / f"{M.stem}.rkpairip.apk"
    shutil.move(str(E), str(I))
    A.set_current_apk(I)
    A.log(f"rkpairip: Processing complete - {I}")
    A.metadata[L] = {T: N, U: O, V: P, W: Q, X: R, "output_apk": str(I)}
  else:
    A.log(
      "rkpairip: No output APK generated. Check RKPairip logs above.",
      level=logging.ERROR,
    )
    raise FileNotFoundError("RKPairip did not produce an output APK")
