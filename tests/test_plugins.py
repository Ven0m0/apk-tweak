"""Plugin system tests."""

from __future__ import annotations

from pathlib import Path

from rvp.context import Context
from rvp.core import dispatch_hooks, load_plugins


def test_load_plugins() -> None:
  """Test plugin discovery and loading."""
  handlers = load_plugins()

  # Should load at least the example plugin
  assert len(handlers) >= 1
  assert callable(handlers[0])


def test_dispatch_hooks(tmp_path: Path) -> None:
  """Test hook dispatching to plugins."""
  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=tmp_path / "test.apk",
    output_dir=tmp_path / "out",
    engines=[],
  )
  # Write a dummy APK to satisfy context
  (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

  handlers = load_plugins()

  # Should not raise any exceptions
  dispatch_hooks(ctx, "test_stage", handlers)
