"""Core pipeline orchestration and dynamic module discovery."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from collections.abc import Callable
from pathlib import Path

from . import engines as engines_pkg
from . import plugins as plugins_pkg
from .context import Context
from .types import PipelineOptions
from .validators import validate_apk_path
from .validators import validate_output_dir

EngineFn = Callable[[Context], None]
PluginHandler = Callable[[Context, str], None]


class _ModuleCache:
  """Thread-safe singleton cache for discovered modules."""

  def __init__(self) -> None:
    self._engines: dict[str, EngineFn] | None = None
    self._plugins: list[PluginHandler] | None = None

  def get_engines(self) -> dict[str, EngineFn]:
    """
    Get cached engines or discover them.

    Returns:
        dict[str, EngineFn]: Mapping of engine names to run functions.
    """
    if self._engines is not None:
      return self._engines

    engines: dict[str, EngineFn] = {}

    # ⚡ Perf: Auto-discovery instead of manual registry
    if hasattr(engines_pkg, "__path__"):
      for _, name, _ in pkgutil.iter_modules(engines_pkg.__path__):
        try:
          full_name = f"{engines_pkg.__name__}.{name}"
          module = importlib.import_module(full_name)
          if hasattr(module, "run") and callable(module.run):
            engines[name] = module.run
        except (ImportError, AttributeError) as e:
          print(
            f"[rvp] WARN: Engine '{name}' load fail: {e}",
            file=sys.stderr,
          )

    self._engines = engines
    return engines

  def get_plugins(self) -> list[PluginHandler]:
    """
    Get cached plugins or discover them.

    Returns:
        list[PluginHandler]: List of plugin hook handlers.
    """
    if self._plugins is not None:
      return self._plugins

    hook_funcs: list[PluginHandler] = []
    if hasattr(plugins_pkg, "__path__"):
      for _, name, _ in pkgutil.iter_modules(plugins_pkg.__path__):
        try:
          full_name = f"{plugins_pkg.__name__}.{name}"
          module = importlib.import_module(full_name)
          if hasattr(module, "handle_hook") and callable(module.handle_hook):
            hook_funcs.append(module.handle_hook)
        except (ImportError, AttributeError) as e:
          print(
            f"[rvp] WARN: Plugin '{name}' load fail: {e}",
            file=sys.stderr,
          )

    self._plugins = hook_funcs
    return hook_funcs


# Singleton instance
_module_cache = _ModuleCache()


def get_engines() -> dict[str, EngineFn]:
  """
  Get all discovered engines.

  Returns:
      dict[str, EngineFn]: Mapping of engine names to run functions.
  """
  return _module_cache.get_engines()


def load_plugins() -> list[PluginHandler]:
  """
  Get all discovered plugins.

  Returns:
      list[PluginHandler]: List of plugin hook handlers.
  """
  return _module_cache.get_plugins()


def dispatch_hooks(ctx: Context, stage: str, handlers: list[PluginHandler]) -> None:
  """
  Dispatch plugin hooks for a specific pipeline stage.

  Args:
      ctx: Pipeline context.
      stage: Hook stage identifier (e.g., "pre_pipeline", "post_engine:revanced").
      handlers: List of plugin handler functions.
  """
  for handler in handlers:
    try:
      handler(ctx, stage)
    except (RuntimeError, ValueError, OSError) as e:
      # ERROR level = 40
      ctx.log(f"Plugin hook error at '{stage}': {e}", level=40)


def run_pipeline(
  input_apk: Path,
  output_dir: Path,
  engines: list[str],
  options: PipelineOptions | None = None,
) -> Context:
  """
  Execute the APK modification pipeline with specified engines.

  Args:
      input_apk: Path to the input APK file.
      output_dir: Directory for output files.
      engines: List of engine names to execute in sequence.
      options: Optional configuration dict for engines and tools.

  Returns:
      Context: Final pipeline context with results.

  Raises:
      ValidationError: If input validation fails.
      ValueError: If required engine is unknown.
  """
  # Validate inputs
  validate_apk_path(input_apk)
  validate_output_dir(output_dir)
  options = options or {}
  work_dir = output_dir / "tmp"
  work_dir.mkdir(parents=True, exist_ok=True)
  output_dir.mkdir(parents=True, exist_ok=True)

  # Initialize context with performance metrics
  ctx = Context(
    work_dir=work_dir,
    input_apk=input_apk,
    output_dir=output_dir,
    engines=engines,
    options=options,
  )

  ctx.log(f"Starting pipeline for: {input_apk}")
  ctx.set_current_apk(input_apk)

  # Pre-load all engines and plugins to avoid repeated lookups
  all_engines = get_engines()  # Dynamic discovery
  plugin_handlers = load_plugins()

  # Record start time for performance tracking
  import time

  start_time = time.time()

  dispatch_hooks(ctx, "pre_pipeline", plugin_handlers)

  # Track engine execution times
  engine_times = {}
  for name in engines:
    if name not in all_engines:
      ctx.log(f"⚠️ Skipping unknown engine: {name}")
      continue

    engine_start = time.time()
    dispatch_hooks(ctx, f"pre_engine:{name}", plugin_handlers)
    ctx.log(f"Running engine: {name}")

    try:
      all_engines[name](ctx)
    except (OSError, ValueError, RuntimeError) as e:
      ctx.log(f"❌ Engine {name} failed: {e}")
      raise RuntimeError(f"Engine {name} failed") from e
    finally:
      engine_time = time.time() - engine_start
      engine_times[name] = engine_time
      ctx.log(f"Engine {name} completed in {engine_time:.2f}s")

    dispatch_hooks(ctx, f"post_engine:{name}", plugin_handlers)

  dispatch_hooks(ctx, "post_pipeline", plugin_handlers)

  total_time = time.time() - start_time
  ctx.log(f"Pipeline finished in {total_time:.2f}s. Final APK: {ctx.current_apk}")

  # Store performance metrics in context
  ctx.metadata["performance"] = {"total_time": total_time, "engine_times": engine_times}

  return ctx
