"""Core pipeline orchestration and dynamic module discovery."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import (
  engines as engines_pkg,
  plugins as plugins_pkg,
)
from .context import Context
from .validators import validate_apk_path, validate_output_dir

EngineFn = Callable[[Context], None]
PluginHandler = Callable[[Context, str], None]
# Cache for discovered modules
_ENGINES: dict[str, EngineFn] | None = None
_PLUGIN_HANDLERS: list[PluginHandler] | None = None


def get_engines() -> dict[str, EngineFn]:
  """
  Dynamically discover engines in rvp.engines package.

  Returns:
      dict[str, EngineFn]: Mapping of engine names to their run functions.
  """
  global _ENGINES
  if _ENGINES is not None:
    return _ENGINES

  engines: dict[str, EngineFn] = {}

  # ⚡ Perf: Auto-discovery instead of manual registry (O(n) where n = engine count)
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

  _ENGINES = engines
  return engines


def load_plugins() -> list[PluginHandler]:
  """
  Dynamically discover and load plugins from rvp.plugins package.

  Returns:
      list[PluginHandler]: List of plugin hook handler functions.
  """
  global _PLUGIN_HANDLERS
  if _PLUGIN_HANDLERS is not None:
    return _PLUGIN_HANDLERS
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

  _PLUGIN_HANDLERS = hook_funcs
  return hook_funcs


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
  options: dict[str, Any] | None = None,
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
  ctx = Context(
    work_dir=work_dir,
    input_apk=input_apk,
    output_dir=output_dir,
    engines=engines,
    options=options,
  )

  ctx.log(f"Starting pipeline for: {input_apk}")
  ctx.set_current_apk(input_apk)
  all_engines = get_engines()  # Dynamic discovery
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
    except (OSError, ValueError, RuntimeError) as e:
      ctx.log(f"❌ Engine {name} failed: {e}")
      raise RuntimeError(f"Engine {name} failed") from e
    dispatch_hooks(ctx, f"post_engine:{name}", plugin_handlers)
  dispatch_hooks(ctx, "post_pipeline", plugin_handlers)
  ctx.log(f"Pipeline finished. Final APK: {ctx.current_apk}")
  return ctx
