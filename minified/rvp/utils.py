from __future__ import annotations

_A = True
import shutil
import subprocess

TIMEOUT_CLONE = 120
TIMEOUT_PATCH = 900
TIMEOUT_ANALYZE = 300
TIMEOUT_OPTIMIZE = 600
TIMEOUT_BUILD = 1200


def require_input_apk(ctx):
  A = ctx.current_apk or ctx.input_apk
  if not A:
    raise ValueError("No input APK found in context")
  return A


def run_command(cmd, ctx, cwd=None, check=_A, timeout=None):
  H = check
  E = timeout
  B = cmd
  A = ctx
  A.log(f"EXEC: {' '.join(str(A) for A in B)}")
  if E:
    A.log(f"  Timeout: {E}s")
  try:
    with subprocess.Popen(
      B,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=_A,
      cwd=cwd,
      bufsize=8192,
      encoding="utf-8",
      errors="replace",
    ) as C:
      if C.stdout:
        D = []
        for J in C.stdout:
          I = J.strip()
          if I:
            D.append(I)
            if len(D) >= 10:
              for F in D:
                A.log(f"  {F}")
              D = []
        for F in D:
          A.log(f"  {F}")
    try:
      G = C.wait(timeout=E)
    except subprocess.TimeoutExpired:
      C.kill()
      C.wait()
      A.log(f"ERR: Command timed out after {E}s")
      raise
    if H and G != 0:
      raise subprocess.CalledProcessError(G, B)
    return subprocess.CompletedProcess(B, G)
  except subprocess.TimeoutExpired:
    raise
  except (OSError, ValueError) as K:
    A.log(f"ERR: Command failed: {K}")
    if H:
      raise
    return subprocess.CompletedProcess(B, 1)


def check_dependencies(required):
  A = [A for A in required if not shutil.which(A)]
  return not A, A


def clone_repository(url, target_dir, ctx, timeout=TIMEOUT_CLONE):
  E = timeout
  D = False
  B = target_dir
  A = ctx
  if B.exists():
    A.log(f"Repository already cloned at {B}, skipping")
    return _A
  A.log(f"Cloning repository from {url}")
  try:
    subprocess.run(
      ["git", "clone", url, str(B)], capture_output=_A, text=_A, timeout=E, check=_A
    )
    A.log(f"Repository cloned successfully to {B}")
    return _A
  except subprocess.TimeoutExpired:
    A.log(f"ERR: Clone timed out after {E}s")
    return D
  except subprocess.CalledProcessError as C:
    A.log(f"ERR: Clone failed: {C.stderr or C.stdout}")
    return D
  except OSError as C:
    A.log(f"ERR: Clone error: {C}")
    return D


def find_latest_apk(directory):
  A = directory
  if not A.exists():
    return None
  B = list(A.glob("*.apk"))
  if not B:
    return None
  return max(B, key=lambda p: p.stat().st_mtime)
