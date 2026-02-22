from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rvp.engines import media_optimizer


def setup_test_files(tmp_path):
  # Setup directories and files
  (tmp_path / "img1.png").touch()
  (tmp_path / "img2.jpg").touch()
  (tmp_path / "audio1.mp3").touch()
  (tmp_path / "subdir").mkdir()
  (tmp_path / "subdir/img3.jpeg").touch()
  (tmp_path / "subdir/audio2.ogg").touch()
  (tmp_path / "other.txt").touch()


def test_find_media_files(tmp_path):
  setup_test_files(tmp_path)
  ctx = MagicMock()

  files = media_optimizer._find_media_files(
    ctx, tmp_path, include_images=True, include_audio=True
  )

  png_files = sorted([p.name for p in files["png"]])
  jpg_files = sorted([p.name for p in files["jpg"]])
  audio_files = sorted([p.name for p in files["audio"]])

  assert png_files == ["img1.png"]
  assert jpg_files == ["img2.jpg", "img3.jpeg"]
  assert audio_files == ["audio1.mp3", "audio2.ogg"]


def test_find_media_files_images_only(tmp_path):
  setup_test_files(tmp_path)
  ctx = MagicMock()

  files = media_optimizer._find_media_files(
    ctx, tmp_path, include_images=True, include_audio=False
  )

  assert len(files["png"]) == 1
  assert len(files["jpg"]) == 2
  assert len(files["audio"]) == 0


def test_find_media_files_audio_only(tmp_path):
  setup_test_files(tmp_path)
  ctx = MagicMock()

  files = media_optimizer._find_media_files(
    ctx, tmp_path, include_images=False, include_audio=True
  )

  assert len(files["png"]) == 0
  assert len(files["jpg"]) == 0
  assert len(files["audio"]) == 2


def test_process_images_integration(tmp_path):
  # Verify that updated _process_images works with passed lists
  # Mock dependencies
  ctx = MagicMock()
  ctx.options = {"png_optimizer": "optipng"}
  ctx.log = MagicMock()

  tools = {"pngquant": True, "optipng": True, "jpegoptim": True}

  png_list = [tmp_path / "test.png"]
  jpg_list = [tmp_path / "test.jpg"]

  # Create dummy files
  (tmp_path / "test.png").touch()
  (tmp_path / "test.jpg").touch()

  # Mock subprocess runs to avoid actual execution
  with pytest.MonkeyPatch.context() as m:
    m.setattr("subprocess.run", MagicMock(return_value=MagicMock(returncode=0)))

    # Call with new signature
    stats = media_optimizer._process_images(ctx, png_list, jpg_list, tools)

    assert stats["png"] == 1
    assert stats["jpg"] == 1


def test_process_audio_integration(tmp_path):
  ctx = MagicMock()
  ctx.log = MagicMock()
  tools = {"ffmpeg": True}

  audio_list = [tmp_path / "test.mp3"]
  (tmp_path / "test.mp3").touch()

  with pytest.MonkeyPatch.context() as m:
    # Mock ffmpeg call. Also need to mock shutil.move or ensure tmp file exists
    # _optimize_audio_worker calls ffmpeg to create .tmp file, then shutil.move

    def mock_run(*args, **kwargs):
      # Create the expected output file
      # In _optimize_audio_worker:
      # temp_output = audio_path.with_suffix(audio_path.suffix + ".tmp")
      # ffmpeg ... str(temp_output)

      # The command list is args[0]
      cmd = args[0]
      output_file = cmd[-1]  # the last arg is output file
      Path(output_file).touch()
      return MagicMock(returncode=0)

    m.setattr("subprocess.run", mock_run)

    count = media_optimizer._process_audio(ctx, audio_list, tools)

    assert count == 1
