from __future__ import annotations
import shutil
from ..context import Context


def run(ctx: Context) -> None:
    """
    Stub for LSPatch engine.
    Later: run LSPatch CLI similar to MartinatorTime/auto-lspatch.
    """
    ctx.log("lspatch: starting patch (stub).")

    input_apk = ctx.current_apk or ctx.input_apk
    out_apk = ctx.output_dir / f"{input_apk.stem}.lspatch.apk"

    # TODO: call LSPatch properly.
    # Using shutil.copy2 for efficient file copying with metadata preservation.
    shutil.copy2(input_apk, out_apk)

    ctx.log(f"lspatch: wrote stub-patched apk to {out_apk}")
    ctx.set_current_apk(out_apk)
