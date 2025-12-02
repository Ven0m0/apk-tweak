from __future__ import annotations
from pathlib import Path
from typing import Dict, Callable, List

from .context import Context
from .engines import revanced, magisk, lspatch, dtlx
from . import plugins as plugins_pkg


EngineFn = Callable[[Context], None]

# Module-level constant: engine registry (avoids dict creation per call)
_ENGINES: Dict[str, EngineFn] = {
    "revanced": revanced.run,
    "magisk": magisk.run,
    "lspatch": lspatch.run,
    "dtlx": dtlx.run,
}


def get_engines() -> Dict[str, EngineFn]:
    """Return the registered engines dictionary."""
    return _ENGINES


def load_plugins() -> List[Callable[[Context, str], None]]:
    """
    Returns a list of plugin hook dispatchers.
    For now, only built-in example_plugin; later, discover from fs/config.
    """
    hook_funcs: List[Callable[[Context, str], None]] = []

    # Example: a very simple plugin that just logs hook stages
    if hasattr(plugins_pkg.example_plugin, "handle_hook"):
        hook_funcs.append(plugins_pkg.example_plugin.handle_hook)

    return hook_funcs


def dispatch_hooks(ctx: Context, stage: str, plugin_handlers: List[Callable[[Context, str], None]]) -> None:
    for handler in plugin_handlers:
        handler(ctx, stage)


def run_pipeline(
    input_apk: Path,
    output_dir: Path,
    engines: List[str],
    options: Dict[str, object] | None = None,
) -> Context:
    options = options or {}
    work_dir = output_dir / "tmp"
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=engines,
        options=options,
    )

    ctx.log(f"Starting pipeline for: {input_apk}")
    ctx.set_current_apk(input_apk.resolve())

    all_engines = get_engines()
    plugin_handlers = load_plugins()

    dispatch_hooks(ctx, "pre_pipeline", plugin_handlers)

    for name in engines:
        if name not in all_engines:
            ctx.log(f"Skipping unknown engine: {name}")
            continue
        dispatch_hooks(ctx, f"pre_engine:{name}", plugin_handlers)
        ctx.log(f"Running engine: {name}")
        all_engines[name](ctx)
        dispatch_hooks(ctx, f"post_engine:{name}", plugin_handlers)

    dispatch_hooks(ctx, "post_pipeline", plugin_handlers)
    ctx.log(f"Pipeline finished. Final APK: {ctx.current_apk}")

    return ctx
