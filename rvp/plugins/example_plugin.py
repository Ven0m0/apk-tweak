"""Example plugin demonstrating the hook system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from ..context import Context


def handle_hook(ctx: Context, stage: str) -> None:
  """
  Example hook handler that logs plugin stages.

  This is called at various pipeline stages:
  - pre_pipeline / post_pipeline
  - pre_engine:{name} / post_engine:{name}

  Args:
      ctx: Pipeline context.
      stage: Hook stage identifier.
  """
  ctx.log(f"[example_plugin] hook: {stage}")
