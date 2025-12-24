from __future__ import annotations

_M = "final_apk"
_L = "patch_bundles_applied"
_K = "revanced_exclude_patches"
_J = "revanced_patches"
_I = "revanced-cli.jar"
_H = "revanced_cli"
_G = "optimized"
_F = "java"
_E = "patch"
_D = "revanced"
_C = "revanced-cli"
_B = False
_A = True
import shutil
import subprocess
from pathlib import Path
from typing import Any
from typing import cast

from ..optimizer import optimize_apk
from ..utils import TIMEOUT_PATCH
from ..utils import check_dependencies
from ..utils import require_input_apk
from ..utils import run_command


def _build_revanced_cli_cmd(ctx, input_apk, output_apk):
  H = "password"
  B = ctx
  if shutil.which(_C):
    A = [_C, _E]
  else:
    I = B.options.get("tools", {})
    J = Path(I.get(_H, _I))
    A = [_F, "-jar", str(J), _E]
  K = B.options.get(_J, [])
  for C in K:
    if isinstance(C, str):
      A.extend(["-p", f"patches/revanced/{C}.rvp"])
    elif isinstance(C, dict):
      L = cast(str, C["name"])
      A.extend(["-p", f"patches/revanced/{L}.rvp"])
      for F, E in C.get("options", {}).items():
        if E is _A:
          A.append(f"-O{F}")
        elif E:
          A.append(f"-O{F}={E}")
  M = B.options.get(_K, [])
  for N in M:
    A.extend(["-e", str(N)])
  if B.options.get("revanced_exclusive", _B):
    A.append("--exclusive")
  G = B.options.get("revanced_keystore")
  if G:
    D = cast(dict[str, Any], G)
    A.extend(
      [
        "--keystore",
        str(D["path"]),
        "--keystore-entry-alias",
        str(D["alias"]),
        "--keystore-password",
        str(D[H]),
        "--keystore-entry-password",
        str(D.get("entry_password", D[H])),
      ]
    )
  A.extend(["-o", str(output_apk), str(input_apk)])
  return A


def _run_revanced_cli(ctx, input_apk, output_apk):
  B = output_apk
  A = ctx
  D = _build_revanced_cli_cmd(A, input_apk, B)
  A.log(f"revanced: running CLI → {B.name}")
  try:
    C = run_command(D, A, timeout=TIMEOUT_PATCH, check=_B)
    if C.returncode == 0 and B.exists():
      A.log("revanced: CLI patching successful")
      return _A
    A.log(f"revanced: CLI failed (exit code: {C.returncode})")
    return _B
  except (OSError, subprocess.SubprocessError) as E:
    A.log(f"revanced: CLI error: {E}")
    return _B


def _create_stub_apk(ctx, input_apk, patch_bundles_count):
  C = input_apk
  A = ctx
  B = A.output_dir / f"{C.stem}.revanced.apk"
  shutil.copy2(C, B)
  A.set_current_apk(B)
  A.metadata[_D] = {_L: patch_bundles_count, _G: _B, _M: str(B), "stub_mode": _A}
  A.log(f"revanced: stub mode - copied to {B}")


def run(ctx):
  X = "patches"
  W = "method"
  V = "revanced_minify"
  U = "revanced_debloat"
  T = "revanced: Starting optimization phase"
  S = "revanced_optimize"
  A = ctx
  A.log("revanced: starting patcher")
  B = require_input_apk(A)
  Y, Z = check_dependencies([_C, _F])
  if not Y:
    A.log(f"revanced: Missing dependencies: {', '.join(Z)}")
    A.log("revanced: Install with: yay -S revanced-cli-bin jdk17-openjdk")
    A.log("revanced: Falling back to stub mode")
    _create_stub_apk(A, B, 0)
    return
  a = A.options.get("revanced_use_cli", _A)
  if a and shutil.which(_C):
    I = A.output_dir / f"{B.stem}.revanced.apk"
    if _run_revanced_cli(A, B, I):
      E = A.options.get(S, _B)
      if E:
        A.log(T)
        D = A.output_dir / f"{B.stem}.revanced-opt.apk"
        optimize_apk(
          input_apk=I,
          output_apk=D,
          ctx=A,
          debloat=A.options.get(U, _A),
          minify=A.options.get(V, _A),
        )
        A.set_current_apk(D)
      else:
        A.set_current_apk(I)
      A.metadata[_D] = {
        W: "cli",
        "patched_apk": str(A.current_apk),
        X: A.options.get(_J, []),
        _G: E,
      }
      return
  A.log("revanced: using JAR-based multi-patch pipeline")
  b = A.options.get("tools", {})
  J = cast(dict[str, Any], b)
  K = Path(J.get(_H, _I))
  Q = Path(J.get("revanced_integrations", "integrations.apk"))
  c = A.options.get("revanced_patch_bundles", [])
  C = cast(list[str], c)
  if not C:
    R = J.get(X, "patches.jar")
    if R:
      C = [str(R)]
  if not C:
    A.log("revanced: No patch bundles specified, using stub mode")
    _create_stub_apk(A, B, 0)
    return
  if not K.exists():
    A.log(f"revanced: CLI jar not found at {K}, using stub mode")
    _create_stub_apk(A, B, len(C))
    return
  G = B
  L = A.work_dir / _D
  L.mkdir(parents=_A, exist_ok=_A)
  for M, d in enumerate(C, 1):
    H = Path(d)
    if not H.exists():
      A.log(f"revanced: Patch bundle not found: {H}, skipping")
      continue
    A.log(f"revanced: Applying patch bundle {M}/{len(C)}: {H.name}")
    if len(C) == M:
      N = L / f"{B.stem}.patched.apk"
    else:
      N = L / f"{B.stem}.patch{M}.apk"
    F = [_F, "-jar", str(K), _E, "--patch-bundle", str(H), "--out", str(N)]
    if Q.exists():
      F.extend(["--merge", str(Q)])
    e = A.options.get("revanced_include_patches", [])
    f = A.options.get(_K, [])
    for O in e:
      F.extend(["--include", O])
    for O in f:
      F.extend(["--exclude", O])
    F.append(str(G))
    run_command(F, A)
    G = N
  E = A.options.get(S, _A)
  if E:
    A.log(T)
    D = A.output_dir / f"{B.stem}.revanced.apk"
    optimize_apk(
      input_apk=G,
      output_apk=D,
      ctx=A,
      debloat=A.options.get(U, _A),
      minify=A.options.get(V, _A),
    )
    A.set_current_apk(D)
    A.log(f"revanced: Optimization complete - {D}")
  else:
    P = A.output_dir / f"{B.stem}.revanced.apk"
    G.rename(P)
    A.set_current_apk(P)
    A.log(f"revanced: Patching complete (no optimization) - {P}")
  A.metadata[_D] = {W: "jar-multi-bundle", _L: len(C), _G: E, _M: str(A.current_apk)}
