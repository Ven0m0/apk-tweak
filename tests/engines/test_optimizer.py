import tempfile
from pathlib import Path

from rvp.context import Context
from rvp.engines.optimizer import _remove_debug_symbols


def test_remove_debug_symbols(mock_context: Context) -> None:
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

    # New behavior counts each removed directory as 1
    # 1 for debug/
    # 1 for proguard/
    # 1 for test.log
    # 1 for app.map
    # Total = 4
    assert removed_count == 4
