from __future__ import annotations

_N = "-codec:a"
_M = "libvorbis"
_L = "libmp3lame"
_K = "--strip-all"
_J = "--force"
_I = "--quality"
_H = ".ogg"
_G = ".mp3"
_F = ".png"
_E = "ffmpeg"
_D = "jpegoptim"
_C = "pngquant"
_B = True
_A = False
import itertools
import os
import shutil
import subprocess
import zipfile
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

from ..utils import check_dependencies
from ..utils import require_input_apk

DPI_FOLDERS = {
  "ldpi": 120,
  "mdpi": 160,
  "hdpi": 240,
  "xhdpi": 320,
  "xxhdpi": 480,
  "xxxhdpi": 640,
  "tvdpi": 213,
  "nodpi": 0,
}


def _get_tool_availability(ctx):
  B = [_C, _D, _E]
  D, A = check_dependencies(B)
  C = {B: B not in A for B in B}
  if A:
    ctx.log(f"media_optimizer: missing tools: {', '.join(A)}")
    ctx.log(
      "media_optimizer: install via package manager (Arch: pacman -S pngquant jpegoptim ffmpeg)"
    )
  return C


def _optimize_png(ctx, png_path, quality="65-80"):
  A = png_path
  try:
    B = subprocess.run(
      [_C, _I, quality, "--ext", _F, _J, str(A)],
      capture_output=_B,
      text=_B,
      timeout=30,
      check=_A,
    )
    return B.returncode == 0
  except (subprocess.TimeoutExpired, Exception) as C:
    ctx.log(f"media_optimizer: PNG optimization failed for {A.name}: {C}")
    return _A


def _optimize_png_worker(png_path, quality="65-80"):
  A = png_path
  try:
    B = subprocess.run(
      [_C, _I, quality, "--ext", _F, _J, str(A)],
      capture_output=_B,
      text=_B,
      timeout=30,
      check=_A,
    )
    return A, B.returncode == 0
  except (subprocess.TimeoutExpired, Exception):
    return A, _A


def _optimize_jpg(ctx, jpg_path, quality=85):
  A = jpg_path
  try:
    B = subprocess.run(
      [_D, f"--max={quality}", _K, str(A)],
      capture_output=_B,
      text=_B,
      timeout=30,
      check=_A,
    )
    return B.returncode == 0
  except (subprocess.TimeoutExpired, Exception) as C:
    ctx.log(f"media_optimizer: JPEG optimization failed for {A.name}: {C}")
    return _A


def _optimize_jpg_worker(jpg_path, quality=85):
  A = jpg_path
  try:
    B = subprocess.run(
      [_D, f"--max={quality}", _K, str(A)],
      capture_output=_B,
      text=_B,
      timeout=30,
      check=_A,
    )
    return A, B.returncode == 0
  except (subprocess.TimeoutExpired, Exception):
    return A, _A


def _optimize_audio(ctx, audio_path, output_path, bitrate="96k"):
  B = output_path
  A = audio_path
  try:
    C = A.suffix.lower()
    if C == _G:
      D = _L
    elif C == _H:
      D = _M
    else:
      return _A
    E = subprocess.run(
      [_E, "-i", str(A), _N, D, "-b:a", bitrate, "-y", str(B)],
      capture_output=_B,
      text=_B,
      timeout=60,
      check=_A,
    )
    if E.returncode == 0 and B.exists():
      shutil.move(B, A)
      return _B
    return _A
  except (subprocess.TimeoutExpired, Exception) as F:
    ctx.log(f"media_optimizer: Audio optimization failed for {A.name}: {F}")
    return _A


def _optimize_audio_worker(audio_path, bitrate="96k"):
  A = audio_path
  try:
    C = A.suffix.lower()
    if C == _G:
      D = _L
    elif C == _H:
      D = _M
    else:
      return A, _A
    B = A.with_suffix(A.suffix + ".tmp")
    E = subprocess.run(
      [_E, "-i", str(A), _N, D, "-b:a", bitrate, "-y", str(B)],
      capture_output=_B,
      text=_B,
      timeout=60,
      check=_A,
    )
    if E.returncode == 0 and B.exists():
      shutil.move(B, A)
      return A, _B
    return A, _A
  except (subprocess.TimeoutExpired, Exception):
    return A, _A


def _extract_apk(ctx, apk, extract_dir):
  A = extract_dir
  try:
    with zipfile.ZipFile(apk, "r") as B:
      B.extractall(A)
    ctx.log(f"media_optimizer: extracted {apk.name} to {A}")
    return _B
  except (OSError, zipfile.BadZipFile) as C:
    ctx.log(f"media_optimizer: extraction failed: {C}")
    return _A


def _repackage_apk(ctx, extract_dir, output_apk):
  C = output_apk
  B = extract_dir
  try:
    F = {
      _F,
      ".jpg",
      ".jpeg",
      ".gif",
      ".webp",
      _G,
      _H,
      ".mp4",
      ".so",
      ".ttf",
      ".woff",
      ".woff2",
    }
    with zipfile.ZipFile(C, "w") as D:
      for A in B.rglob("*"):
        if A.is_file():
          E = A.relative_to(B)
          if A.suffix.lower() in F:
            D.write(A, E, compress_type=zipfile.ZIP_STORED)
          else:
            D.write(A, E, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    ctx.log(f"media_optimizer: repackaged to {C.name}")
    return _B
  except (OSError, zipfile.BadZipFile) as G:
    ctx.log(f"media_optimizer: repackaging failed: {G}")
    return _A


def _process_images(ctx, extract_dir, tools):
  L = tools
  K = "jpg"
  J = "png"
  E = extract_dir
  A = ctx
  C = {J: 0, K: 0}
  F = list(E.rglob("*.png"))
  G = list(itertools.chain(E.rglob("*.jpg"), E.rglob("*.jpeg")))
  A.log(f"media_optimizer: found {len(F)} PNG, {len(G)} JPEG files")
  H = L.get(_C, _A)
  I = L.get(_D, _A)
  if not H and not I:
    A.log(
      "media_optimizer: no optimization tools available, skipping image optimization"
    )
    return C
  Q = os.cpu_count() or 1
  M = min(Q, 8)
  A.log(f"media_optimizer: optimizing images with {M} shared workers")
  with ProcessPoolExecutor(max_workers=M) as N:
    D = {}
    if H and F:
      for O in F:
        B = N.submit(_optimize_png_worker, O)
        D[B] = J, O
    if I and G:
      for P in G:
        B = N.submit(_optimize_jpg_worker, P)
        D[B] = K, P
    for B in as_completed(D):
      R, S = D[B]
      S, T = B.result()
      if T:
        C[R] += 1
  if not H:
    A.log("media_optimizer: pngquant not available, skipped PNG optimization")
  if not I:
    A.log("media_optimizer: jpegoptim not available, skipped JPEG optimization")
  A.log(f"media_optimizer: optimized {C[J]} PNG, {C[K]} JPEG files")
  return C


def _process_audio(ctx, extract_dir, tools):
  D = extract_dir
  A = ctx
  if not tools.get(_E, _A):
    A.log("media_optimizer: ffmpeg not available, skipping audio optimization")
    return 0
  B = list(itertools.chain(D.rglob("*.mp3"), D.rglob("*.ogg")))
  A.log(f"media_optimizer: found {len(B)} audio files")
  if not B:
    return 0
  F = os.cpu_count() or 1
  E = min(F, 8)
  A.log(f"media_optimizer: optimizing audio with {E} workers")
  C = 0
  with ProcessPoolExecutor(max_workers=E) as G:
    H = {G.submit(_optimize_audio_worker, A): A for A in B}
    for I in as_completed(H):
      K, J = I.result()
      if J:
        C += 1
  A.log(f"media_optimizer: optimized {C} audio files")
  return C


def _filter_dpi_resources(ctx, extract_dir, target_dpis):
  A = ctx
  F = extract_dir / "res"
  if not F.exists():
    A.log("media_optimizer: no res/ directory found")
    return 0
  B = {A.lower().strip() for A in target_dpis}
  B.add("nodpi")
  A.log(f"media_optimizer: keeping DPIs: {', '.join(sorted(B))}")
  C = 0
  D = []
  for G in F.glob("drawable-*"):
    H = G.name
    I = H.split("-")
    if len(I) < 2:
      continue
    E = None
    for J in I[1:]:
      if J in DPI_FOLDERS:
        E = J
        break
    if E and E not in B:
      shutil.rmtree(G)
      D.append(H)
      C += 1
  if D:
    A.log(f"media_optimizer: removed {C} DPI folders: {', '.join(D)}")
  else:
    A.log("media_optimizer: no DPI folders removed")
  return C


def run(ctx):
  B = "media_optimizer"
  A = ctx
  F = A.options.get("optimize_images", _A)
  G = A.options.get("optimize_audio", _A)
  C = A.options.get("target_dpi")
  if not (F or G or C):
    A.log("media_optimizer: no operations requested; skipping.")
    return
  H = require_input_apk(A)
  A.log(f"media_optimizer: starting (images={F}, audio={G}, dpi={C})")
  K = _get_tool_availability(A)
  L = A.work_dir / B
  L.mkdir(parents=_B, exist_ok=_B)
  D = L / "extracted"
  if not _extract_apk(A, H, D):
    A.log("media_optimizer: extraction failed, aborting")
    return
  if B not in A.metadata:
    A.metadata[B] = {}
  if F:
    O = _process_images(A, D, K)
    A.metadata[B]["images"] = O
  if G:
    P = _process_audio(A, D, K)
    A.metadata[B]["audio"] = P
  if C:
    if isinstance(C, str):
      M = [A.strip() for A in C.split(",")]
    else:
      M = C
    Q = _filter_dpi_resources(A, D, M)
    A.metadata[B]["dpi_folders_removed"] = Q
  E = A.output_dir / f"{H.stem}.optimized.apk"
  if _repackage_apk(A, D, E):
    A.set_current_apk(E)
    A.log(f"media_optimizer: pipeline will continue with {E}")
    I = H.stat().st_size
    R = E.stat().st_size
    J = I - R
    N = J / I * 100 if I > 0 else 0
    A.log(f"media_optimizer: size reduction: {J / 1024 / 1024:.2f} MB ({N:.1f}%)")
    A.metadata[B]["size_reduction"] = {"bytes": J, "percentage": N}
  else:
    A.log(
      "media_optimizer: repackaging failed, pipeline will continue with original APK"
    )
