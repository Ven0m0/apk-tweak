"""LSPatch patching engine."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..context import Context
from ..utils import (
  TIMEOUT_PATCH,
  check_dependencies,
  find_latest_apk,
  run_command,
)


def _build_lspatch_cmd(
  ctx: Context, input_apk: Path, output_dir: Path
) -> list[str]:
  """
  Build lspatch command from context options.

  Supports both binary CLI and JAR-based approaches.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK path.
      output_dir: Output directory.

  Returns:
      Command list for subprocess execution.
  """
  # Check if using binary or JAR
  if shutil.which("lspatch"):
    cmd = ["lspatch", "-v", "-l", "2", "-f", "-o", str(output_dir)]
  else:
    tools = ctx.options.get("tools", {})
    lspatch_jar = Path(str(tools.get("lspatch_jar", "lspatch.jar")))
    cmd = ["java", "-jar", str(lspatch_jar), "-l", "2", "-o", str(output_dir)]

  # Modules
  modules = ctx.options.get("lspatch_modules", [])
  for module in modules:
    # Support both direct paths and patch directory references
    if isinstance(module, Path) or "/" in str(module):
      module_path = Path(module)
    else:
      module_path = ctx.work_dir / f"patches/lspatch/{module}.apk"

    if module_path.exists():
      cmd.extend(["-m", str(module_path)])
    else:
      ctx.log(f"lspatch: Module not found: {module_path}")

  # Manager mode (alternative to embedded)
  if ctx.options.get("lspatch_manager_mode", False):
    cmd.extend(["--manager", "--injectdex"])

  cmd.append(str(input_apk))
  return cmd


def _run_lspatch_cli(
  ctx: Context, input_apk: Path, output_dir: Path
) -> Path | None:
  """
  Execute LSPatch patching with binary command.

  Args:
      ctx: Pipeline context.
      input_apk: Input APK path.
      output_dir: Output directory.

  Returns:
      Path to patched APK if successful, None otherwise.
  """
  cmd = _build_lspatch_cmd(ctx, input_apk, output_dir)
  ctx.log(f"lspatch: running CLI → {output_dir}")

  try:
    result = run_command(cmd, ctx, timeout=TIMEOUT_PATCH, check=False)

    if result.returncode == 0:
      # LSPatch outputs as {package_name}.apk or *-lspatched.apk
      patched = find_latest_apk(output_dir)
      if patched:
        ctx.log("lspatch: CLI patching successful")
        return patched

    ctx.log(f"lspatch: CLI failed (exit code: {result.returncode})")
    return None

  except Exception as e:
    ctx.log(f"lspatch: CLI error: {e}")
    return None


def run(ctx: Context) -> None:
  """
  Execute LSPatch engine with multiple approaches.

  Supports:
  - Binary lspatch command (preferred)
  - JAR-based patching
  - Module embedding
  - Manager mode for external LSPatch support

  Args:
      ctx: Pipeline context.

  Options:
      lspatch_modules: List of module APKs to embed
      lspatch_manager_mode: Use manager mode instead of embedded
      lspatch_jar: Path to lspatch.jar (for JAR mode)
      lspatch_use_cli: Prefer CLI over JAR (default: True)

  Raises:
      ValueError: If no input APK is available.
  """
  ctx.log("lspatch: starting patcher")

  input_apk = ctx.current_apk
  if not input_apk:
    raise ValueError("No input APK available")

  # Check dependencies
  deps_ok, missing_deps = check_dependencies(["lspatch", "java"])
  if not deps_ok:
    ctx.log(f"lspatch: Missing dependencies: {', '.join(missing_deps)}")
    ctx.log("lspatch: Install from: https://github.com/LSPosed/LSPatch")
    raise FileNotFoundError(f"LSPatch dependencies missing: {missing_deps}")

  # Try binary CLI approach first (luniume-style)
  use_cli = ctx.options.get("lspatch_use_cli", True)
  if use_cli and shutil.which("lspatch"):
    lspatch_work = ctx.work_dir / "lspatch_output"
    lspatch_work.mkdir(parents=True, exist_ok=True)

    patched_apk = _run_lspatch_cli(ctx, input_apk, lspatch_work)
    if patched_apk:
      final_apk = ctx.output_dir / f"{input_apk.stem}.lspatch.apk"
      shutil.copy2(patched_apk, final_apk)
      ctx.set_current_apk(final_apk)
      ctx.metadata["lspatch"] = {
        "method": "cli",
        "patched_apk": str(final_apk),
        "modules": ctx.options.get("lspatch_modules", []),
      }
      ctx.log(f"lspatch: patching complete → {final_apk}")
      return

  # Fall back to JAR-based approach
  ctx.log("lspatch: using JAR-based approach")

  # Config Resolution
  tools = ctx.options.get("tools", {})
  lspatch_jar = Path(str(tools.get("lspatch_jar", "lspatch.jar")))

  if not lspatch_jar.exists():
    ctx.log(f"LSPatch jar not found at {lspatch_jar}", level=40)  # ERROR
    raise FileNotFoundError(f"LSPatch jar missing: {lspatch_jar}")

  # Construct Command
  # Usage: java -jar lspatch.jar [options] input.apk
  # -m <module> : Embed module
  # -l <level>  : 2 = embed
  cmd = [
    "java",
    "-jar",
    str(lspatch_jar),
    "-l",
    "2",
    "-o",
    str(ctx.output_dir),  # LSPatch takes a dir and auto-names
    str(input_apk),
  ]

  # Add modules if defined in config
  modules = ctx.options.get("lspatch_modules", [])
  for mod in modules:
    cmd.extend(["-m", str(mod)])

  ctx.log(f"lspatch: Running patch on {input_apk.name}")
  run_command(cmd, ctx)

  # Find the output APK (LSPatch generates *-lspatched.apk or similar)
  expected_out = ctx.output_dir / f"{input_apk.stem}-lspatched.apk"
  if expected_out.exists():
    ctx.set_current_apk(expected_out)
  else:
    # Fallback: Find the most recently created APK
    newest = find_latest_apk(ctx.output_dir)
    if newest:
      ctx.set_current_apk(newest)
    else:
      raise FileNotFoundError("LSPatch completed but output APK not found")

  # Store metadata
  ctx.metadata["lspatch"] = {
    "method": "jar",
    "patched_apk": str(ctx.current_apk),
    "modules": modules,
  }
  ctx.log(f"lspatch: patching complete → {ctx.current_apk}")
