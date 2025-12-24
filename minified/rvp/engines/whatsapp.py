from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

from ..utils import check_dependencies
from ..utils import clone_repository
from ..utils import require_input_apk

WHATSAPP_PATCHER_REPO = "https://github.com/Schwartzblat/WhatsAppPatcher"
WHATSAPP_FEATURES = [
  "Signature Verifier Bypass",
  "Enable all AB tests",
  "Keep revoked for all messages",
  "Disable read receipts",
  "Save view once media",
]


def run(ctx):
  Q = "whatsapp_ab_tests"
  P = "main.py"
  O = "whatsapp_temp_dir"
  N = False
  C = True
  A = ctx
  A.log("whatsapp: starting WhatsApp APK patcher")
  I = require_input_apk(A)
  R, T = check_dependencies(["java"])
  if not R:
    A.log("whatsapp: ERROR - Java runtime not found")
    A.log(
      "whatsapp: Install with: pacman -S jdk-openjdk or apt-get install openjdk-17-jre"
    )
    return
  J = A.options.get("whatsapp_patcher_path")
  if J:
    B = Path(cast(str, J))
  else:
    B = A.work_dir / "whatsapp-patcher"
    if not clone_repository(WHATSAPP_PATCHER_REPO, B, A):
      A.log("whatsapp: failed to obtain patcher")
      return
    K = B / "requirements.txt"
    if K.exists():
      A.log("whatsapp: installing Python dependencies")
      subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(K)], check=N
      )
  E = A.output_dir / f"{I.stem}.whatsapp-patched.apk"
  L = A.options.get(O)
  G = Path(L) if L else A.work_dir / "whatsapp_temp"
  G.mkdir(parents=C, exist_ok=C)
  F = B / "whatsapp_patcher" / P
  if not F.exists():
    F = B / P
  if not F.exists():
    A.log(f"whatsapp: main.py not found in {B}")
    return
  M = [sys.executable, str(F), "-p", str(I), "-o", str(E), "--temp-path", str(G)]
  if A.options.get(Q, C):
    M.append("--ab-tests")
  H = A.options.get("whatsapp_timeout", 1200)
  A.log(f"whatsapp: running patcher (timeout: {H}s)")
  A.log(f"whatsapp: features: {', '.join(WHATSAPP_FEATURES)}")
  try:
    D = subprocess.run(M, capture_output=C, text=C, cwd=B, timeout=H, check=N)
    if D.returncode == 0 and E.exists():
      A.set_current_apk(E)
      A.log(f"whatsapp: success → {E}")
      A.metadata["whatsapp"] = {
        "patched_apk": str(E),
        "features": WHATSAPP_FEATURES,
        "ab_tests_enabled": A.options.get(Q, C),
      }
    else:
      A.log(f"whatsapp: patching failed (exit code: {D.returncode})")
      if D.stderr:
        A.log(f"whatsapp: stderr: {D.stderr[:500]}")
      if D.stdout:
        A.log(f"whatsapp: stdout: {D.stdout[:500]}")
  except subprocess.TimeoutExpired:
    A.log(f"whatsapp: patching timed out after {H} seconds")
  except (OSError, subprocess.CalledProcessError) as S:
    A.log(f"whatsapp: patching error: {S}")
  finally:
    if not A.options.get(O):
      shutil.rmtree(G, ignore_errors=C)
