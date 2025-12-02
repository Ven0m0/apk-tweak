from __future__ import annotations
from pathlib import Path
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
    out_apk.write_bytes(input_apk.read_bytes())

    ctx.log(f"lspatch: wrote stub-patched apk to {out_apk}")
    ctx.set_current_apk(out_apk)
