"""Core pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

from rvp.config import Config
from rvp.core import run_pipeline


def test_pipeline_basic_flow(tmp_path: Path) -> None:
  """Test that the pipeline initializes and runs stub engines."""
  # Setup
  input_apk = tmp_path / "test.apk"
  input_apk.write_text("pk", encoding="utf-8")
  out_dir = tmp_path / "out"

  # Run with no engines (pass-through)
  ctx = run_pipeline(input_apk=input_apk, output_dir=out_dir, engines=[])

  assert ctx.current_apk == input_apk
  assert ctx.work_dir.exists()


def test_config_loading(tmp_path: Path) -> None:
  """Test config serialization."""
  cfg_file = tmp_path / "config.json"
  data = {"input_apk": "test.apk", "engines": ["revanced"]}
  cfg_file.write_text(json.dumps(data), encoding="utf-8")

  cfg = Config.load_from_file(cfg_file)
  assert cfg.input_apk == "test.apk"
  assert "revanced" in cfg.engines
