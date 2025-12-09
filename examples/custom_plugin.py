"""Example custom plugin for the RVP pipeline.

This plugin demonstrates how to:
1. Hook into various pipeline stages
2. Access and modify context
3. Perform custom operations
4. Log information

To use: Copy this file to rvp/plugins/ and it will be auto-discovered.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from rvp.context import Context


def handle_hook(ctx: Context, stage: str) -> None:
  """
  Handle pipeline hooks at various stages.

  Args:
      ctx: Pipeline execution context.
      stage: Hook stage identifier.
  """
  # Example: Log all stages
  ctx.log(f"[custom_plugin] Stage: {stage}")

  # Example: Perform actions at specific stages
  if stage == "pre_pipeline":
    ctx.log("[custom_plugin] Pipeline starting - initializing custom data")
    ctx.metadata["custom_plugin"] = {"started_at": "now"}

  elif stage == "post_pipeline":
    ctx.log("[custom_plugin] Pipeline complete - cleaning up")
    if ctx.current_apk:
      size = ctx.current_apk.stat().st_size
      ctx.log(f"[custom_plugin] Final APK size: {size} bytes")

  elif stage.startswith("pre_engine:"):
    engine_name = stage.split(":", 1)[1]
    ctx.log(f"[custom_plugin] About to run engine: {engine_name}")

  elif stage.startswith("post_engine:"):
    engine_name = stage.split(":", 1)[1]
    ctx.log(f"[custom_plugin] Finished running engine: {engine_name}")

  # Example: Add metadata
  if "plugin_hooks_called" not in ctx.metadata:
    ctx.metadata["plugin_hooks_called"] = []
  ctx.metadata["plugin_hooks_called"].append(stage)
