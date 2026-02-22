import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

sys.path.insert(0, os.getcwd())

from rvp.context import Context
from rvp.engines import media_optimizer


class TestMediaOptimizerExecution(unittest.TestCase):
  def setUp(self):
    # Mock Paths
    self.mock_apk = MagicMock(spec=Path)
    self.mock_apk.stem = "input"
    self.mock_apk.stat.return_value.st_size = 1000

    self.mock_output_dir = MagicMock(spec=Path)
    self.mock_output_apk = MagicMock(spec=Path)
    self.mock_output_apk.stat.return_value.st_size = 800
    self.mock_output_dir.__truediv__.return_value = self.mock_output_apk

    self.mock_ctx = MagicMock(spec=Context)
    self.mock_ctx.options = {}
    self.mock_ctx.metadata = {}
    self.mock_ctx.work_dir = Path("/tmp/work")
    self.mock_ctx.output_dir = self.mock_output_dir
    self.mock_ctx.input_apk = self.mock_apk
    self.mock_ctx.log = MagicMock()
    self.mock_ctx.set_current_apk = MagicMock()

    self.patches = []

    p = patch("rvp.engines.media_optimizer.require_input_apk")
    self.mock_require_apk = p.start()
    self.mock_require_apk.return_value = self.mock_apk
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer._extract_apk")
    self.mock_extract = p.start()
    self.mock_extract.return_value = True
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer._repackage_apk")
    self.mock_repackage = p.start()
    self.mock_repackage.return_value = True
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer._get_tool_availability")
    self.mock_tools = p.start()
    self.mock_tools.return_value = {
      "pngquant": True,
      "optipng": True,
      "jpegoptim": True,
      "ffmpeg": True,
    }
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer.os.walk")
    self.mock_walk = p.start()
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer.as_completed")
    self.mock_as_completed = p.start()
    self.patches.append(p)

    p = patch("rvp.engines.media_optimizer.ProcessPoolExecutor")
    self.mock_executor_cls = p.start()
    self.patches.append(p)

  def tearDown(self):
    for p in reversed(self.patches):
      p.stop()

  def test_single_shared_executor(self):
    """Verify optimized behavior: only 1 shared executor created for both tasks."""
    self.mock_ctx.options = {"optimize_images": True, "optimize_audio": True}

    self.mock_walk.return_value = [("/tmp/extract", [], ["image.png", "audio.mp3"])]

    # Mock Futures
    mock_future = MagicMock()
    mock_future.result.return_value = (None, True)
    self.mock_as_completed.return_value = [mock_future]

    # Mock Executor
    mock_executor = self.mock_executor_cls.return_value
    mock_executor.__enter__.return_value = mock_executor
    mock_executor.submit.return_value = mock_future

    media_optimizer.run(self.mock_ctx)

    print(f"EXECUTORS CREATED: {self.mock_executor_cls.call_count}")

    # Optimized expectation: 1 shared executor
    self.assertEqual(
      self.mock_executor_cls.call_count,
      1,
      f"Expected 1 shared executor, but got {self.mock_executor_cls.call_count}",
    )


if __name__ == "__main__":
  unittest.main()
