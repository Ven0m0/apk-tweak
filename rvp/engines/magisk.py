from __future__ import annotations
from pathlib import Path
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

    (module_dir / apk.name).write_bytes(apk.read_bytes())
    ctx.log(f"magisk: wrote stub module at {module_dir}")
    ctx.metadata.setdefault("magisk", {})["module_dir"] = str(module_dir)
