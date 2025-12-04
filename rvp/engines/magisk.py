from __future__ import annotations
import shutil
from ..context import Context


def run(ctx: Context) -> None:
    """
    Stub for Magisk module packaging.
    Later: implement module layout similar to j-hc/revanced-magisk-module.
    """
    ctx.log("magisk: packaging Magisk module (stub).")

    apk = ctx.current_apk or ctx.input_apk
    module_dir = ctx.output_dir / "magisk-module"
    module_dir.mkdir(parents=True, exist_ok=True)

    # Stub: write a dummy module.prop and copy the apk
    (module_dir / "module.prop").write_text(
        "id=rvp-example\n"
        "name=ReVanced Pipeline Example\n"
        "version=1.0.0\n"
        "versionCode=1\n"
        "author=rvp\n"
        "description=Stub Magisk module\n",
        encoding="utf-8",
    )

    # Using shutil.copy2 for efficient file copying with metadata preservation.
    shutil.copy2(apk, module_dir / apk.name)
    ctx.log(f"magisk: wrote stub module at {module_dir}")

    # Performance: Use direct dict access pattern instead of setdefault
    if "magisk" not in ctx.metadata:
        ctx.metadata["magisk"] = {}
    ctx.metadata["magisk"]["module_dir"] = str(module_dir)
