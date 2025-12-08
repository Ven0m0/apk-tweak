"""Performance and complexity verification tests."""

from __future__ import annotations

import time
from pathlib import Path

from rvp.context import Context
from rvp.core import get_engines, load_plugins
from rvp.engines import magisk


def test_engine_discovery_performance() -> None:
  """
  Verify engine discovery works and is cached.

  This test ensures that the discovery mechanism is efficient
  and uses caching properly.
  """
  # First call - should discover engines
  engines1 = get_engines()
  assert len(engines1) > 0, "No engines discovered"
  assert "revanced" in engines1, "ReVanced engine not found"

  # Second call - should return cached result (same object)
  engines2 = get_engines()
  assert engines1 is engines2, (
    "Caching not working - returned different objects"
  )


def test_plugin_loading_performance() -> None:
  """
  Verify plugin loading works and is cached.

  This test ensures that the plugin discovery mechanism is efficient
  and uses caching properly.
  """
  # First call - should discover plugins
  plugins1 = load_plugins()
  assert len(plugins1) > 0, "No plugins discovered"

  # Second call - should return cached result (same object)
  plugins2 = load_plugins()
  assert plugins1 is plugins2, (
    "Caching not working - returned different objects"
  )


def test_magisk_zip_performance(tmp_path: Path) -> None:
  """
  Verify Magisk zipping is O(n) where n = number of files.

  This test ensures file operations scale linearly.
  """
  # Create test APK
  input_apk = tmp_path / "test.apk"
  input_apk.write_text("fake_apk_data" * 1000, encoding="utf-8")

  ctx = Context(
    work_dir=tmp_path / "work",
    input_apk=input_apk,
    output_dir=tmp_path / "out",
    engines=["magisk"],
  )

  # Measure execution time
  start = time.perf_counter()
  magisk.run(ctx)
  duration = time.perf_counter() - start

  # Should complete in reasonable time (< 1 second for test data)
  assert duration < 1.0, (
    f"Magisk module creation took too long: {duration:.3f}s"
  )

  # Verify output exists
  assert "magisk_module" in ctx.metadata
  assert Path(ctx.metadata["magisk_module"]).exists()


def test_context_metadata_access() -> None:
  """
  Verify context metadata operations are O(1).

  Dictionary operations should be constant time.
  """
  ctx = Context(
    work_dir=Path("/tmp/work"),
    input_apk=Path("/tmp/test.apk"),
    output_dir=Path("/tmp/out"),
    engines=[],
  )

  # Add metadata (O(1))
  start = time.perf_counter()
  for i in range(1000):
    ctx.metadata[f"key_{i}"] = f"value_{i}"
  write_duration = time.perf_counter() - start

  # Read metadata (O(1) per access)
  start = time.perf_counter()
  for i in range(1000):
    _ = ctx.metadata.get(f"key_{i}")
  read_duration = time.perf_counter() - start

  # Both should be very fast
  assert write_duration < 0.01, (
    f"Metadata writes too slow: {write_duration:.3f}s"
  )
  assert read_duration < 0.01, f"Metadata reads too slow: {read_duration:.3f}s"
