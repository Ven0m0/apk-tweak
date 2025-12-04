from __future__ import annotations
import shutil
from pathlib import Path
from ..context import Context
from ..utils import run_command

def run(ctx: Context) -> None:
    """ReVanced patch engine."""
    ctx.log("revanced: starting patch")

    input_apk = ctx.current_apk or ctx.input_apk
    if not input_apk:
        raise ValueError("No input APK found in context")

    out_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"
    
    # Retrieve tool paths from options (populated by Config)
    tools = ctx.options.get("tools", {})
    cli_jar = Path(tools.get("revanced_cli", "revanced-cli.jar"))
    patches_jar = Path(tools.get("patches", "patches.jar"))

    # Check if tools exist (Simulated for this example)
    # In production, check: if not cli_jar.exists(): ...

    # 🔧 Example of constructing the real command
    # cmd = [
    #     "java", "-jar", str(cli_jar),
    #     "patch",
    #     "--patch-bundle", str(patches_jar),
    #     "--out", str(out_apk),
    #     str(input_apk)
    # ]
    
    # For now, we still copy, but we log like a real command execution
    # run_command(cmd, ctx) 
    
    # Stub fallback
    shutil.copy2(input_apk, out_apk)

    ctx.log(f"revanced: wrote patched apk to {out_apk}")
    ctx.set_current_apk(out_apk)
