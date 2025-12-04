from __future__ import annotations
import pkgutil
import importlib
import sys
from pathlib import Path
from typing import Dict, Callable, List

from .context import Context
# Remove hardcoded imports
from . import engines as engines_pkg
from . import plugins as plugins_pkg

EngineFn = Callable[[Context], None]

# Cache
_ENGINES: Dict[str, EngineFn] | None = None
_PLUGIN_HANDLERS: List[Callable[[Context, str], None]] | None = None

def get_engines() -> Dict[str, EngineFn]:
    """Dynamically discover engines in rvp.engines package."""
    global _ENGINES
    if _ENGINES is not None:
        return _ENGINES

    engines: Dict[str, EngineFn] = {}
    
    # ⚡ Perf: Auto-discovery instead of manual registry
    if hasattr(engines_pkg, "__path__"):
        for _, name, _ in pkgutil.iter_modules(engines_pkg.__path__):
            try:
                full_name = f"{engines_pkg.__name__}.{name}"
                module = importlib.import_module(full_name)
                if hasattr(module, "run") and callable(module.run):
                    engines[name] = module.run
            except Exception as e:
                print(f"[rvp] WARN: Engine '{name}' load fail: {e}", file=sys.stderr)

    _ENGINES = engines
    return engines

def load_plugins() -> List[Callable[[Context, str], None]]:
    # ... (Keep existing plugin logic)
    global _PLUGIN_HANDLERS
    if _PLUGIN_HANDLERS is not None:
        return _PLUGIN_HANDLERS

    hook_funcs: List[Callable[[Context, str], None]] = []
    
    if hasattr(plugins_pkg, "__path__"):
        for _, name, _ in pkgutil.iter_modules(plugins_pkg.__path__):
            try:
                full_name = f"{plugins_pkg.__name__}.{name}"
                module = importlib.import_module(full_name)
                if hasattr(module, "handle_hook") and callable(module.handle_hook):
                    hook_funcs.append(module.handle_hook)
            except Exception as e:
                print(f"[rvp] WARN: Plugin '{name}' load fail: {e}", file=sys.stderr)

    _PLUGIN_HANDLERS = hook_funcs
    return hook_funcs

# ... (Keep existing dispatch_hooks and run_pipeline)
# Ensure run_pipeline calls get_engines()
def run_pipeline(
    input_apk: Path,
    output_dir: Path,
    engines: List[str],
    options: Dict[str, object] | None = None,
) -> Context:
    # ... setup ctx ...
    #
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

    all_engines = get_engines() # Now dynamic
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
            raise

        dispatch_hooks(ctx, f"post_engine:{name}", plugin_handlers)

    dispatch_hooks(ctx, "post_pipeline", plugin_handlers)
    ctx.log(f"Pipeline finished. Final APK: {ctx.current_apk}")

    return ctx
