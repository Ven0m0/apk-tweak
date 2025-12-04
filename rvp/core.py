from __future__ import annotations
import pkgutil
import importlib
from pathlib import Path
from typing import Dict, Callable, List
import sys

from .context import Context
from .engines import revanced, magisk, lspatch, dtlx
from . import plugins as plugins_pkg

EngineFn = Callable[[Context], None]

_ENGINES: Dict[str, EngineFn] = {
    "revanced": revanced.run,
    "magisk": magisk.run,
    "lspatch": lspatch.run,
    "dtlx": dtlx.run,
}

_PLUGIN_HANDLERS: List[Callable[[Context, str], None]] | None = None

def get_engines() -> Dict[str, EngineFn]:
    return _ENGINES

def load_plugins() -> List[Callable[[Context, str], None]]:
    """
    Dynamically discover plugins in the rvp.plugins package.
    """
    global _PLUGIN_HANDLERS
    if _PLUGIN_HANDLERS is not None:
        return _PLUGIN_HANDLERS

    hook_funcs: List[Callable[[Context, str], None]] = []
    
    # ⚡ Perf: Iterate over all modules in the plugins package
    if hasattr(plugins_pkg, "__path__"):
        for _, name, _ in pkgutil.iter_modules(plugins_pkg.__path__):
            try:
                # Import module dynamically
                full_name = f"{plugins_pkg.__name__}.{name}"
                module = importlib.import_module(full_name)
                
                if hasattr(module, "handle_hook") and callable(module.handle_hook):
                    hook_funcs.append(module.handle_hook)
                    
            except Exception as e:
                # Log error but don't crash pipeline
                print(f"[rvp] WARN: Failed to load plugin {name}: {e}", file=sys.stderr)

    _PLUGIN_HANDLERS = hook_funcs
    return hook_funcs

def clear_plugin_cache() -> None:
    global _PLUGIN_HANDLERS
    _PLUGIN_HANDLERS = None

def dispatch_hooks(
    ctx: Context, stage: str, plugin_handlers: List[Callable[[Context, str], None]]
) -> None:
    if not plugin_handlers:
        return
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
    ctx.set_current_apk(input_apk)

    all_engines = get_engines()
    plugin_handlers = load_plugins()

    dispatch_hooks(ctx, "pre_pipeline", plugin_handlers)

    for name in engines:
        if name not in all_engines:
            ctx.log(f"⚠️ Skipping unknown engine: {name}")
            continue
            
        dispatch_hooks(ctx, f"pre_engine:{name}", plugin_handlers)
        
        ctx.log(f"Running engine: {name}")
        try:
            all_engines[name](ctx)
        except Exception as e:
            ctx.log(f"❌ Engine {name} failed: {e}")
            raise # Fail fast or continue based on policy? Defaulting to fail fast.

        dispatch_hooks(ctx, f"post_engine:{name}", plugin_handlers)

    dispatch_hooks(ctx, "post_pipeline", plugin_handlers)
    ctx.log(f"Pipeline finished. Final APK: {ctx.current_apk}")

    return ctx
