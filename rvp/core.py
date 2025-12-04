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

# Performance: Cache loaded plugins at module level to avoid repeated loading
_PLUGIN_HANDLERS: List[Callable[[Context, str], None]] | None = None


def get_engines() -> Dict[str, EngineFn]:
    """Return the registered engines dictionary."""
    return _ENGINES


def load_plugins() -> List[Callable[[Context, str], None]]:
    """
    Returns a list of plugin hook dispatchers.
    For now, only built-in example_plugin; later, discover from fs/config.

    Performance optimization: Plugins are cached at module level after first load,
    avoiding repeated hasattr checks and list reconstruction.

    Note: The cache is module-level for performance. For testing scenarios where
    plugins need to be reloaded, call clear_plugin_cache() first.
    """
    global _PLUGIN_HANDLERS

    # Return cached handlers if already loaded
    if _PLUGIN_HANDLERS is not None:
        return _PLUGIN_HANDLERS

    hook_funcs: List[Callable[[Context, str], None]] = []

    # Performance: Direct attribute access is faster than hasattr
    # which internally catches AttributeError
    try:
        handle_hook = plugins_pkg.example_plugin.handle_hook
        if callable(handle_hook):
            hook_funcs.append(handle_hook)
    except AttributeError:
        pass  # Plugin doesn't have handle_hook, skip it

    # Cache for future calls
    _PLUGIN_HANDLERS = hook_funcs
    return hook_funcs


def clear_plugin_cache() -> None:
    """
    Clear the plugin cache. Useful for testing scenarios.

    In production use, plugins are loaded once and cached for performance.
    This function allows tests to reload plugins if needed.
    """
    global _PLUGIN_HANDLERS
    _PLUGIN_HANDLERS = None


def dispatch_hooks(
    ctx: Context, stage: str, plugin_handlers: List[Callable[[Context, str], None]]
) -> None:
    """
    Dispatch hooks to all registered plugin handlers.

    Performance optimization: Early return if no handlers to avoid unnecessary calls.
    """
    # Performance: Skip dispatch if no handlers registered
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
    """
    Run the pipeline with the specified engines.

    Args:
        input_apk: Input APK path (should be resolved for optimal performance)
        output_dir: Output directory path (should be resolved for optimal performance)
        engines: List of engine names to run
        options: Optional configuration dict

    Returns:
        Context object with pipeline state and results

    Note: For best performance, resolve input_apk and output_dir paths before calling.
    """
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
    # Performance: Avoid redundant resolve() - paths should be pre-resolved by caller
    ctx.set_current_apk(input_apk)

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
