from unittest.mock import MagicMock

import pytest

from rvp.context import Context
from rvp.engines.optimizer import _optimize_resources


@pytest.fixture
def mock_context(tmp_path):
  ctx = MagicMock(spec=Context)
  ctx.log = MagicMock()
  return ctx


def test_optimize_resources_no_res_dir(mock_context, tmp_path):
  # Setup: Empty extract_dir (no res folder)
  count = _optimize_resources(mock_context, tmp_path)
  assert count == 0
  mock_context.log.assert_not_called()


def test_optimize_resources_removes_backups(mock_context, tmp_path):
  # Setup
  res_dir = tmp_path / "res"
  res_dir.mkdir()

  # Files to keep
  (res_dir / "valid.xml").touch()
  (res_dir / "layout").mkdir()
  (res_dir / "layout" / "view.xml").touch()

  # Files to remove
  (res_dir / "valid.xml~").touch()
  (res_dir / "temp~").touch()
  (res_dir / "layout" / "old.xml~").touch()

  count = _optimize_resources(mock_context, tmp_path)

  assert count == 3
  assert (res_dir / "valid.xml").exists()
  assert (res_dir / "layout" / "view.xml").exists()
  assert not (res_dir / "valid.xml~").exists()
  assert not (res_dir / "temp~").exists()
  assert not (res_dir / "layout" / "old.xml~").exists()


def test_optimize_resources_removes_ds_store(mock_context, tmp_path):
  # Setup
  res_dir = tmp_path / "res"
  res_dir.mkdir()

  (res_dir / ".DS_Store").touch()
  subdir = res_dir / "values"
  subdir.mkdir()
  (subdir / ".DS_Store").touch()
  (subdir / "strings.xml").touch()

  count = _optimize_resources(mock_context, tmp_path)

  assert count == 2
  assert not (res_dir / ".DS_Store").exists()
  assert not (subdir / ".DS_Store").exists()
  assert (subdir / "strings.xml").exists()


def test_optimize_resources_mixed(mock_context, tmp_path):
  # Setup
  res_dir = tmp_path / "res"
  res_dir.mkdir()

  (res_dir / "file1.xml").touch()
  (res_dir / "file1.xml~").touch()
  (res_dir / ".DS_Store").touch()

  count = _optimize_resources(mock_context, tmp_path)

  assert count == 2
  assert (res_dir / "file1.xml").exists()
  assert not (res_dir / "file1.xml~").exists()
  assert not (res_dir / ".DS_Store").exists()


def test_optimize_resources_handles_os_error_on_unlink(mock_context, tmp_path):
  """Verify that an OSError during unlink is caught and does not crash."""
  res_dir = tmp_path / "res"
  res_dir.mkdir()
  (res_dir / "file.txt~").touch()

  with patch("rvp.engines.optimizer.os.unlink", side_effect=OSError("Permission denied")) as mock_unlink:
    count = _optimize_resources(mock_context, tmp_path)

  # Unlink was called, but it failed and was caught.
  mock_unlink.assert_called_once()
  assert count == 0
  # No success log should be present.
  mock_context.log.assert_not_called()
