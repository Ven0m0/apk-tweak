"""Luniume APK patcher engine (ReVanced/LSPatch orchestrator)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from ..context import Context

# Constants
LUNIUME_REPO = "https://github.com/shomykohai/luniume"


def _check_method_dependencies(method: str) -> tuple[bool, list[str]]:
    """
    Check dependencies for specified patching method.

    Args:
        method: "revanced" or "lspatch".

    Returns:
        Tuple of (all_found, missing_tools).
    """
    if method == "revanced":
        required = ["revanced-cli", "java"]
        missing = [tool for tool in required if not shutil.which(tool)]
        return (not missing, missing)
    if method == "lspatch":
        required = ["lspatch", "java"]
        missing = [tool for tool in required if not shutil.which(tool)]
        return (not missing, missing)
    return (False, ["unknown method"])


def _build_revanced_cmd(
    ctx: Context, input_apk: Path, output_apk: Path
) -> list[str]:
    """
    Build revanced-cli command from context options.

    Args:
        ctx: Pipeline context.
        input_apk: Input APK path.
        output_apk: Output APK path.

    Returns:
        Command list for subprocess execution.
    """
    cmd = ["revanced-cli", "patch"]

    # Patches
    patches = ctx.options.get("luniume_patches", [])
    for patch in patches:
        if isinstance(patch, str):
            cmd.extend(["-p", f"patches/revanced/{patch}.rvp"])
        elif isinstance(patch, dict):
            patch_name = patch["name"]
            cmd.extend(["-p", f"patches/revanced/{patch_name}.rvp"])
            # Add options
            for key, value in patch.get("options", {}).items():
                if value is True:
                    cmd.append(f"-O{key}")
                elif value:
                    cmd.append(f"-O{key}={value}")

    # Excludes
    for exclude in ctx.options.get("luniume_exclude_patches", []):
        cmd.extend(["-e", exclude])

    # Exclusive mode
    if ctx.options.get("luniume_exclusive", False):
        cmd.append("--exclusive")

    # Signing
    keystore_opts = ctx.options.get("luniume_keystore")
    if keystore_opts:
        cmd.extend(
            [
                "--keystore",
                keystore_opts["path"],
                "--keystore-entry-alias",
                keystore_opts["alias"],
                "--keystore-password",
                keystore_opts["password"],
                "--keystore-entry-password",
                keystore_opts["password"],
            ]
        )
    else:
        # Use default signer
        cmd.append("--signer=Luniume")

    # Output
    cmd.extend(["-o", str(output_apk), str(input_apk)])
    return cmd


def _build_lspatch_cmd(
    ctx: Context, input_apk: Path, output_dir: Path
) -> list[str]:
    """
    Build lspatch command from context options.

    Args:
        ctx: Pipeline context.
        input_apk: Input APK path.
        output_dir: Output directory.

    Returns:
        Command list for subprocess execution.
    """
    cmd = ["lspatch", "-v", "-l", "2", "-f", "-o", str(output_dir)]

    # Modules
    modules = ctx.options.get("luniume_modules", [])
    for module in modules:
        module_path = ctx.work_dir / f"patches/lspatch/{module}.apk"
        if module_path.exists():
            cmd.extend(["-m", str(module_path)])

    # Manager mode (alternative to embedded)
    if ctx.options.get("luniume_manager_mode", False):
        cmd.extend(["--manager", "--injectdex"])

    cmd.append(str(input_apk))
    return cmd


def _run_revanced(ctx: Context, input_apk: Path, output_apk: Path) -> bool:
    """
    Execute ReVanced CLI patching.

    Args:
        ctx: Pipeline context.
        input_apk: Input APK path.
        output_apk: Output APK path.

    Returns:
        True if successful, False otherwise.
    """
    cmd = _build_revanced_cmd(ctx, input_apk, output_apk)
    ctx.log(f"luniume: running ReVanced CLI → {output_apk.name}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=900, check=False
        )

        if result.returncode == 0 and output_apk.exists():
            ctx.log("luniume: ReVanced patching successful")
            return True
        ctx.log(
            f"luniume: ReVanced failed (exit code: {result.returncode})"
        )
        if result.stderr:
            ctx.log(f"luniume: {result.stderr[:500]}")
        return False

    except subprocess.TimeoutExpired:
        ctx.log("luniume: ReVanced timed out after 15 minutes")
        return False
    except Exception as e:
        ctx.log(f"luniume: ReVanced error: {e}")
        return False


def _run_lspatch(ctx: Context, input_apk: Path, output_dir: Path) -> Path | None:
    """
    Execute LSPatch patching.

    Args:
        ctx: Pipeline context.
        input_apk: Input APK path.
        output_dir: Output directory.

    Returns:
        Path to patched APK if successful, None otherwise.
    """
    cmd = _build_lspatch_cmd(ctx, input_apk, output_dir)
    ctx.log(f"luniume: running LSPatch → {output_dir}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=900, check=False
        )

        if result.returncode == 0:
            # LSPatch outputs as {package_name}.apk
            patched_files = list(output_dir.glob("*.apk"))
            if patched_files:
                ctx.log("luniume: LSPatch patching successful")
                return patched_files[0]
        ctx.log(f"luniume: LSPatch failed (exit code: {result.returncode})")
        if result.stderr:
            ctx.log(f"luniume: {result.stderr[:500]}")
        return None

    except subprocess.TimeoutExpired:
        ctx.log("luniume: LSPatch timed out after 15 minutes")
        return None
    except Exception as e:
        ctx.log(f"luniume: LSPatch error: {e}")
        return None


def run(ctx: Context) -> None:
    """
    Execute Luniume APK patcher.

    Orchestrates ReVanced CLI or LSPatch for patching Line, Instagram,
    and other Android apps with custom modules and patches.

    Supports:
    - ReVanced CLI with custom patches and options
    - LSPatch with embedded modules
    - Custom keystore signing
    - Exclusive patching mode

    Args:
        ctx: Pipeline context.

    Options:
        luniume_method: "revanced" or "lspatch" (default: "lspatch")
        luniume_patches: List of patches (str or dict with options)
        luniume_exclude_patches: List of patches to exclude (ReVanced)
        luniume_modules: List of LSPatch modules (LSPatch)
        luniume_exclusive: Enable exclusive mode (ReVanced)
        luniume_manager_mode: Use manager mode instead of embedded (LSPatch)
        luniume_keystore: Dict with path, alias, password (ReVanced)
    """
    ctx.log("luniume: starting patcher")
    input_apk = ctx.current_apk or ctx.input_apk

    # Get patching method
    method = ctx.options.get("luniume_method", "lspatch")
    if method not in ["revanced", "lspatch"]:
        ctx.log(f"luniume: ERROR - invalid method '{method}'")
        ctx.log("luniume: use --luniume-method=revanced or --luniume-method=lspatch")
        return

    # Check dependencies
    deps_ok, missing_deps = _check_method_dependencies(method)
    if not deps_ok:
        ctx.log(
            f"luniume: ERROR - Missing dependencies for {method}: {', '.join(missing_deps)}"
        )
        if method == "revanced":
            ctx.log(
                "luniume: Install with: yay -S revanced-cli-bin jdk17-openjdk"
            )
        else:
            ctx.log(
                "luniume: Install LSPatch from: https://github.com/LSPosed/LSPatch"
            )
        return

    # Execute patching based on method
    if method == "revanced":
        output_apk = ctx.output_dir / f"{input_apk.stem}.luniume-revanced.apk"
        if _run_revanced(ctx, input_apk, output_apk):
            ctx.set_current_apk(output_apk)
            ctx.metadata["luniume"] = {
                "method": "revanced",
                "patched_apk": str(output_apk),
                "patches": ctx.options.get("luniume_patches", []),
            }

    elif method == "lspatch":
        lspatch_work = ctx.work_dir / "luniume_lspatch"
        lspatch_work.mkdir(parents=True, exist_ok=True)

        patched_apk = _run_lspatch(ctx, input_apk, lspatch_work)
        if patched_apk:
            final_apk = (
                ctx.output_dir / f"{input_apk.stem}.luniume-lspatch.apk"
            )
            shutil.copy2(patched_apk, final_apk)
            ctx.set_current_apk(final_apk)
            ctx.metadata["luniume"] = {
                "method": "lspatch",
                "patched_apk": str(final_apk),
                "modules": ctx.options.get("luniume_modules", []),
            }
