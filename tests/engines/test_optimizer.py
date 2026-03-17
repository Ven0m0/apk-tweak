import zipfile
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from rvp.context import Context
from rvp.engines.optimizer import _remove_debug_symbols
from rvp.engines.optimizer import _strip_native_libraries
from rvp.engines.optimizer import run


@pytest.fixture
def mock_ctx(tmp_path):
  ctx = MagicMock(spec=Context)
  ctx.work_dir = tmp_path / "work"
  ctx.output_dir = tmp_path / "output"
  ctx.work_dir.mkdir()
  ctx.output_dir.mkdir()
  ctx.options = {}
  ctx.metadata = {}
  ctx.current_apk = None
  ctx.log = MagicMock()
  return ctx


def test_remove_debug_symbols_relative_matching(mock_ctx, tmp_path):
  # Setup extraction dir
  extract_dir = tmp_path / "extract"
  extract_dir.mkdir()

  # Create a file that should NOT be removed even if absolute path contains 'debug'
  # We simulate this by having 'debug' in the tmp_path but NOT in the relative path
  debug_path = tmp_path / "debug_workspace"
  debug_path.mkdir()
  extract_dir = debug_path / "extract"
  extract_dir.mkdir()

  safe_file = extract_dir / "assets" / "safe.txt"
  safe_file.parent.mkdir()
  safe_file.write_text("safe")

  # Create a file that SHOULD be removed
  debug_file = extract_dir / "assets" / "debug_info.log"
  debug_file.write_text("debug")

  # Create a directory that SHOULD be removed
  test_dir = extract_dir / "tests"
  test_dir.mkdir()
  (test_dir / "test_file.txt").write_text("test")

  removed = _remove_debug_symbols(mock_ctx, extract_dir)

  # Should have removed debug_info.log and everything in tests/

  assert safe_file.exists()
  assert not debug_file.exists()
  assert not test_dir.exists()
  assert removed >= 2  # 1 file + 1 file inside test_dir


def test_strip_native_libraries(mock_ctx, tmp_path):
  extract_dir = tmp_path / "extract"
  lib_dir = extract_dir / "lib" / "arm64-v8a"
  lib_dir.mkdir(parents=True)

  so_file = lib_dir / "libtest.so"
  so_file.write_text("elf_content")

  with (
    patch("shutil.which", return_value="/usr/bin/strip"),
    patch("rvp.utils.run_command") as mock_run,
  ):
    count = _strip_native_libraries(mock_ctx, extract_dir)

    assert count == 1
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "strip" in args
    assert "--strip-unneeded" in args
    assert str(so_file) in args


def test_optimizer_run_integration(mock_ctx, tmp_path):
  # Create a dummy APK
  apk_path = tmp_path / "test.apk"
  with zipfile.ZipFile(apk_path, "w") as zf:
    zf.writestr("AndroidManifest.xml", "<manifest><!-- comment --></manifest>")
    zf.writestr("assets/debug.log", "debug")
    zf.writestr("lib/arm64-v8a/libtest.so", "so")

  mock_ctx.input_apk = apk_path
  mock_ctx.current_apk = apk_path
  mock_ctx.options = {
    "remove_debug_symbols": True,
    "minimize_manifest": True,
    "optimize_resources": False,
    "keep_locales": [],
  }

  def mock_repack(ctx, extract_dir, output_path):
    output_path.write_text("mock apk content")
    return True

  with (
    patch("rvp.engines.optimizer.repack_apk", side_effect=mock_repack),
    patch("shutil.which", return_value="/usr/bin/strip"),
    patch("rvp.utils.run_command"),
  ):
    run(mock_ctx)

    assert "optimizer" in mock_ctx.metadata
    ops = mock_ctx.metadata["optimizer"]["operations_performed"]
    op_types = [op["type"] for op in ops]
    assert "debug_symbol_removal" in op_types
    assert "manifest_minimization" in op_types
