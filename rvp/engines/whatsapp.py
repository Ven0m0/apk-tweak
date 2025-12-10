"""WhatsApp APK patcher engine."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from ..context import Context
from ..utils import check_dependencies, clone_repository

# Constants
WHATSAPP_PATCHER_REPO = "https://github.com/Schwartzblat/WhatsAppPatcher"
WHATSAPP_FEATURES = [
  "Signature Verifier Bypass",
  "Enable all AB tests",
  "Keep revoked for all messages",
  "Disable read receipts",
  "Save view once media",
]


def run(ctx: Context) -> None:
  """
  Execute WhatsApp APK patcher.

  Patches WhatsApp Android APK using Schwartzblat/WhatsAppPatcher.

  Features applied:
  - Signature Verifier Bypass (removes signature checks)
  - Enable all AB tests (activates experimental features)
  - Keep revoked for all messages (maintains revocation status)
  - Disable read receipts (prevents read notifications)
  - Save view once media (allows saving disappearing media)

  Required:
  - Java Runtime Environment (JRE)
  - Python 3 with termcolor, requests, pytest, cryptography

  Args:
      ctx: Pipeline context.

  Options:
      whatsapp_patcher_path: Custom patcher directory (default: clone to work_dir)
      whatsapp_ab_tests: Enable A/B testing features (default: True)
      whatsapp_temp_dir: Override temp extraction directory
      whatsapp_timeout: Override 20-minute default timeout (seconds)
  """
  ctx.log("whatsapp: starting WhatsApp APK patcher")
  input_apk = ctx.current_apk or ctx.input_apk

  # Check Java dependency
  deps_ok, _ = check_dependencies(["java"])
  if not deps_ok:
    ctx.log("whatsapp: ERROR - Java runtime not found")
    ctx.log(
      "whatsapp: Install with: pacman -S jdk-openjdk or apt-get install openjdk-17-jre"
    )
    return

  # Locate or clone patcher
  patcher_path = ctx.options.get("whatsapp_patcher_path")
  if patcher_path:
    patcher_dir = Path(str(patcher_path))
  else:
    patcher_dir = ctx.work_dir / "whatsapp-patcher"
    if not clone_repository(WHATSAPP_PATCHER_REPO, patcher_dir, ctx):
      ctx.log("whatsapp: failed to obtain patcher")
      return

    # Install Python dependencies
    req_file = patcher_dir / "requirements.txt"
    if req_file.exists():
      ctx.log("whatsapp: installing Python dependencies")
      subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
        check=False,
      )

  # Prepare output
  output_apk = ctx.output_dir / f"{input_apk.stem}.whatsapp-patched.apk"

  # Prepare temp directory
  temp_dir = ctx.options.get("whatsapp_temp_dir")
  temp_path = Path(temp_dir) if temp_dir else ctx.work_dir / "whatsapp_temp"
  temp_path.mkdir(parents=True, exist_ok=True)

  # Build command
  main_script = patcher_dir / "whatsapp_patcher" / "main.py"
  if not main_script.exists():
    # Try alternative location
    main_script = patcher_dir / "main.py"

  if not main_script.exists():
    ctx.log(f"whatsapp: main.py not found in {patcher_dir}")
    return

  cmd = [
    sys.executable,
    str(main_script),
    "-p",
    str(input_apk),
    "-o",
    str(output_apk),
    "--temp-path",
    str(temp_path),
  ]

  # Add AB tests flag if requested
  if ctx.options.get("whatsapp_ab_tests", True):
    cmd.append("--ab-tests")

  # Execute patcher
  timeout = ctx.options.get("whatsapp_timeout", 1200)  # 20 minutes default
  ctx.log(f"whatsapp: running patcher (timeout: {timeout}s)")
  ctx.log(f"whatsapp: features: {', '.join(WHATSAPP_FEATURES)}")

  try:
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      cwd=patcher_dir,
      timeout=timeout,
      check=False,
    )

    if result.returncode == 0 and output_apk.exists():
      ctx.set_current_apk(output_apk)
      ctx.log(f"whatsapp: success → {output_apk}")

      # Store metadata
      ctx.metadata["whatsapp"] = {
        "patched_apk": str(output_apk),
        "features": WHATSAPP_FEATURES,
        "ab_tests_enabled": ctx.options.get("whatsapp_ab_tests", True),
      }
    else:
      ctx.log(f"whatsapp: patching failed (exit code: {result.returncode})")
      if result.stderr:
        ctx.log(f"whatsapp: stderr: {result.stderr[:500]}")
      if result.stdout:
        ctx.log(f"whatsapp: stdout: {result.stdout[:500]}")

  except subprocess.TimeoutExpired:
    ctx.log(f"whatsapp: patching timed out after {timeout} seconds")
  except Exception as e:
    ctx.log(f"whatsapp: patching error: {e}")
  finally:
    # Cleanup temp directory if using default
    if not ctx.options.get("whatsapp_temp_dir"):
      shutil.rmtree(temp_path, ignore_errors=True)
