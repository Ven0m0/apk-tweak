import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from rvp.context import Context
from rvp.engines.optimizer import _remove_debug_symbols
from rvp.engines.optimizer import _strip_native_libraries
from rvp.engines.optimizer import run


@pytest.fixture
def mock_ctx(tmp_path: Path) -> MagicMock:
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


def test_remove_debug_symbols(mock_context: Context) -> None:
  """Test that debug dirs, proguard dirs, and debug/map files are removed."""
  with tempfile.TemporaryDirectory(prefix="safe") as tmp_dir:
    extract_dir = Path(tmp_dir) / "extracted"
    extract_dir.mkdir()

    # Create directories that should be removed
    debug_dir = extract_dir / "debug"
    debug_dir.mkdir()
    (debug_dir / "file1.txt").touch()
    (debug_dir / "file2.txt").touch()

    proguard_dir = extract_dir / "proguard"
    proguard_dir.mkdir()
    (proguard_dir / "mapping.txt").touch()

    # Create files that should be removed
    (extract_dir / "test.log").touch()
    (extract_dir / "app.map").touch()

    # Create files that should NOT be removed
    (extract_dir / "AndroidManifest.xml").touch()
    keep_dir = extract_dir / "keep_me"
    keep_dir.mkdir()
    (keep_dir / "important.txt").touch()

    # Run the function
    removed_count = _remove_debug_symbols(mock_context, extract_dir)

    assert not debug_dir.exists()
    assert not proguard_dir.exists()
    assert not (extract_dir / "test.log").exists()
    assert not (extract_dir / "app.map").exists()

    assert (extract_dir / "AndroidManifest.xml").exists()
    assert keep_dir.exists()

    # Counts each removed directory as 1, plus each removed file as 1:
    # 1 for debug/, 1 for proguard/, 1 for test.log, 1 for app.map = 4
    assert removed_count == 4


def test_remove_debug_symbols_relative_matching(
  mock_ctx: MagicMock, tmp_path: Path
) -> None:
  """Test that path matching is relative (not absolute) to avoid false positives."""
  # Have 'debug' in the tmp_path itself but NOT in the relative path within extract_dir
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

  assert safe_file.exists()
  assert not debug_file.exists()
  assert not test_dir.exists()
  assert removed >= 2  # 1 for tests/ dir + 1 for debug_info.log


def test_strip_native_libraries(mock_ctx: MagicMock, tmp_path: Path) -> None:
  """Test that .so files are stripped using the strip tool."""
  extract_dir = tmp_path / "extract"
  lib_dir = extract_dir / "lib" / "arm64-v8a"
  lib_dir.mkdir(parents=True)

  so_file = lib_dir / "libtest.so"
  so_file.write_text("elf_content")

  with (
    patch("shutil.which", return_value="/usr/bin/strip"),
    patch("rvp.engines.optimizer.run_command") as mock_run,
  ):
    mock_run.return_value.returncode = 0
    count = _strip_native_libraries(mock_ctx, extract_dir)

    assert count == 1
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "strip" in args
    assert "--strip-unneeded" in args
    assert str(so_file) in args


def test_optimizer_run_integration(mock_ctx: MagicMock, tmp_path: Path) -> None:
  """Test the full optimizer engine run with debug removal and manifest minimization."""
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

  def mock_repack(ctx: Context, extract_dir: Path, output_path: Path) -> bool:
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
