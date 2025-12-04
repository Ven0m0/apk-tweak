"""LSPatch patching engine."""

from __future__ import annotations

from pathlib import Path

from ..context import Context
from ..utils import run_command


def run(ctx: Context) -> None:
    """
    Execute LSPatch engine.

    Requires 'lspatch_jar' in options/tools.

    Args:
        ctx: Pipeline context.

    Raises:
        ValueError: If no input APK is available.
        FileNotFoundError: If lspatch.jar is not found.
    """
    ctx.log("lspatch: Initializing...")

    input_apk = ctx.current_apk
    if not input_apk:
        raise ValueError("No input APK available")

    # Config Resolution
    tools = ctx.options.get("tools", {})
    lspatch_jar = Path(tools.get("lspatch_jar", "lspatch.jar"))

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

    # LSPatch output handling (it might generate a specific name)
    # For robust handling, we find the newest file in output dir
    # Assuming standard behavior:
    expected_out = ctx.output_dir / f"{input_apk.stem}-lspatched.apk"

    if expected_out.exists():
        ctx.set_current_apk(expected_out)
    else:
        # Fallback: Find the file created by lspatch (often named *-lspatched.apk)
        # O(n) where n = files in output dir
        candidates = list(ctx.output_dir.glob("*-lspatched.apk"))
        if candidates:
            # Pick the most recently modified
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            ctx.set_current_apk(newest)
        else:
            raise FileNotFoundError("LSPatch completed but output APK not found")
