from __future__ import annotations
import shutil
from ..context import Context


def run(ctx: Context) -> None:
    """
    Stub for ReVanced patch engine.
    Later: call rvx-cli or official ReVanced CLI with proper args.
    """
    ctx.log("revanced: starting patch (stub).")

    input_apk = ctx.current_apk or ctx.input_apk
    out_apk = ctx.output_dir / f"{input_apk.stem}.revanced.apk"

    # TODO: Replace with real ReVanced CLI invocation.
    # For now, just pretend we created a new APK by copying.
    # Using shutil.copy2 for efficient file copying with metadata preservation.
    shutil.copy2(input_apk, out_apk)

    ctx.log(f"revanced: wrote patched apk (stub) to {out_apk}")
    ctx.set_current_apk(out_apk)
