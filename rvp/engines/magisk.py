"""Magisk module packaging engine (stub)."""

from __future__ import annotations

from ..context import Context


def run(ctx: Context) -> None:
    """
    Magisk module packaging (disabled).

    This engine has been removed. Use external Magisk module builders instead.

    Args:
        ctx: Pipeline context.
    """
    ctx.log("magisk: Engine disabled (removed)")
    ctx.log("magisk: Use external Magisk module packaging tools")
    ctx.metadata["magisk"] = {"status": "disabled", "reason": "engine removed"}
