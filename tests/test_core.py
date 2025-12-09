"""Tests for core pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rvp.context import Context
from rvp.core import (
  dispatch_hooks,
  get_engines,
  load_plugins,
  run_pipeline,
)
from rvp.validators import ValidationError


class TestGetEngines:
  """Tests for engine discovery."""

  def test_engines_discovered(self) -> None:
    """Test that engines are auto-discovered."""
    engines = get_engines()

    assert isinstance(engines, dict)
    assert len(engines) > 0
    # Check common engines exist
    assert "revanced" in engines or "lspatch" in engines

  def test_engines_cached(self) -> None:
    """Test that engines are cached on subsequent calls."""
    engines1 = get_engines()
    engines2 = get_engines()

    # Should return same dict instance (cached)
    assert engines1 is engines2


class TestLoadPlugins:
  """Tests for plugin discovery."""

  def test_plugins_loaded(self) -> None:
    """Test that plugins are discovered."""
    plugins = load_plugins()

    assert isinstance(plugins, list)
    # Plugins list may be empty if no plugins installed

  def test_plugins_cached(self) -> None:
    """Test that plugins are cached on subsequent calls."""
    plugins1 = load_plugins()
    plugins2 = load_plugins()

    # Should return same list instance (cached)
    assert plugins1 is plugins2


class TestDispatchHooks:
  """Tests for hook dispatching."""

  def test_dispatch_single_hook(self, tmp_path: Path) -> None:
    """Test dispatching to single hook handler."""
    from rvp.context import Context

    apk = tmp_path / "test.apk"
    apk.touch()

    ctx = Context(
      work_dir=tmp_path / "work",
      input_apk=apk,
      output_dir=tmp_path / "out",
      engines=[],
    )

    hook_called = []

    def test_hook(context: Context, stage: str) -> None:
      hook_called.append((context, stage))

    dispatch_hooks(ctx, "pre_pipeline", [test_hook])

    assert len(hook_called) == 1
    assert hook_called[0][0] is ctx
    assert hook_called[0][1] == "pre_pipeline"

  def test_dispatch_multiple_hooks(self, tmp_path: Path) -> None:
    """Test dispatching to multiple hook handlers."""
    apk = tmp_path / "test.apk"
    apk.touch()

    ctx = Context(
      work_dir=tmp_path / "work",
      input_apk=apk,
      output_dir=tmp_path / "out",
      engines=[],
    )

    calls = []

    def hook1(context: Context, stage: str) -> None:
      calls.append("hook1")

    def hook2(context: Context, stage: str) -> None:
      calls.append("hook2")

    dispatch_hooks(ctx, "post_pipeline", [hook1, hook2])

    assert calls == ["hook1", "hook2"]

  def test_dispatch_hook_error_handling(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that hook errors are logged but don't crash."""
    apk = tmp_path / "test.apk"
    apk.touch()

    ctx = Context(
      work_dir=tmp_path / "work",
      input_apk=apk,
      output_dir=tmp_path / "out",
      engines=[],
    )

    def failing_hook(context: Context, stage: str) -> None:
      raise ValueError("Hook error")

    # Should not raise, but log error
    dispatch_hooks(ctx, "pre_pipeline", [failing_hook])
    assert "Plugin hook error" in caplog.text


class TestRunPipeline:
  """Tests for pipeline execution."""

  def test_pipeline_invalid_apk(self, tmp_path: Path) -> None:
    """Test pipeline fails with invalid APK."""
    missing_apk = tmp_path / "missing.apk"
    output_dir = tmp_path / "output"

    with pytest.raises(ValidationError):
      run_pipeline(missing_apk, output_dir, ["revanced"])

  def test_pipeline_creates_work_dir(self, sample_apk: Path, tmp_path: Path) -> None:
    """Test pipeline creates work directory."""
    output_dir = tmp_path / "output"

    # Mock engine to prevent actual execution
    with patch("rvp.core.get_engines") as mock_get:
      mock_get.return_value = {}
      ctx = run_pipeline(sample_apk, output_dir, [])

    assert (output_dir / "tmp").exists()
    assert ctx.work_dir.exists()

  def test_pipeline_unknown_engine_skipped(
    self,
    sample_apk: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
  ) -> None:
    """Test unknown engines are skipped with warning."""
    import logging

    output_dir = tmp_path / "output"

    with patch("rvp.core.get_engines") as mock_get:
      mock_get.return_value = {}
      with caplog.at_level(logging.INFO):
        run_pipeline(sample_apk, output_dir, ["unknown_engine"])

    assert "Skipping unknown engine" in caplog.text

  def test_pipeline_engine_execution(self, sample_apk: Path, tmp_path: Path) -> None:
    """Test that engines are executed in order."""
    output_dir = tmp_path / "output"
    calls = []

    def mock_engine1(ctx: Context) -> None:
      calls.append("engine1")

    def mock_engine2(ctx: Context) -> None:
      calls.append("engine2")

    engines = {"engine1": mock_engine1, "engine2": mock_engine2}

    with patch("rvp.core.get_engines", return_value=engines):
      with patch("rvp.core.load_plugins", return_value=[]):
        run_pipeline(
          sample_apk,
          output_dir,
          ["engine1", "engine2"],
        )

    assert calls == ["engine1", "engine2"]

  def test_pipeline_engine_error_propagates(self, sample_apk: Path, tmp_path: Path) -> None:
    """Test that engine errors are propagated."""
    output_dir = tmp_path / "output"

    def failing_engine(ctx: Context) -> None:
      raise RuntimeError("Engine failed")

    engines = {"failing": failing_engine}

    with patch("rvp.core.get_engines", return_value=engines):
      with patch("rvp.core.load_plugins", return_value=[]):
        with pytest.raises(RuntimeError):
          run_pipeline(sample_apk, output_dir, ["failing"])

  def test_pipeline_options_passed(self, sample_apk: Path, tmp_path: Path) -> None:
    """Test that options are passed to context."""
    output_dir = tmp_path / "output"
    options = {"test_option": True, "value": 42}

    ctx_captured = None

    def capture_engine(ctx: Context) -> None:
      nonlocal ctx_captured
      ctx_captured = ctx

    engines = {"capture": capture_engine}

    with patch("rvp.core.get_engines", return_value=engines):
      with patch("rvp.core.load_plugins", return_value=[]):
        run_pipeline(
          sample_apk,
          output_dir,
          ["capture"],
          options,
        )

    assert ctx_captured is not None
    assert ctx_captured.options == options
