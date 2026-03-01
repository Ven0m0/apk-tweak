from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest
from rvp.engines.media_optimizer import _run_optimizer_worker, _process_images
from rvp.context import Context

# Mock Context
@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=Context)
    ctx.options = {}
    ctx.log = MagicMock()
    return ctx

@patch("rvp.engines.media_optimizer.subprocess.run")
def test_run_optimizer_worker_success(mock_run):
    mock_run.return_value.returncode = 0
    path = Path("test.png")
    command = ["echo", "hello"]

    result_path, success = _run_optimizer_worker(path, command)

    assert result_path == path
    assert success is True
    mock_run.assert_called_once_with(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False
    )

@patch("rvp.engines.media_optimizer.subprocess.run")
def test_run_optimizer_worker_failure(mock_run):
    mock_run.return_value.returncode = 1
    path = Path("test.png")
    command = ["echo", "hello"]

    result_path, success = _run_optimizer_worker(path, command)

    assert result_path == path
    assert success is False

@patch("rvp.engines.media_optimizer.subprocess.run")
def test_run_optimizer_worker_timeout(mock_run):
    mock_run.side_effect = TimeoutError
    path = Path("test.png")
    command = ["echo", "hello"]

    result_path, success = _run_optimizer_worker(path, command)

    assert result_path == path
    assert success is False

@patch("rvp.engines.media_optimizer.ProcessPoolExecutor")
@patch("rvp.engines.media_optimizer.as_completed")
def test_process_images_pngquant(mock_as_completed, mock_executor, mock_context):
    # Setup
    extract_dir = Path("/tmp/extract")
    tools = {"pngquant": True, "optipng": False, "jpegoptim": False}
    mock_context.options = {"png_optimizer": "pngquant"}

    # Mock os.walk to return some files
    with patch("os.walk") as mock_walk:
        mock_walk.return_value = [
            (str(extract_dir), [], ["image.png"])
        ]

        # Create a mock future
        mock_future = MagicMock()
        mock_future.result.return_value = (Path("image.png"), True)

        # Configure submit to return this future
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

        # Configure as_completed to yield this future
        mock_as_completed.return_value = [mock_future]

        # Run
        _process_images(mock_context, extract_dir, tools)

        # Verify submit call
        mock_submit = mock_executor.return_value.__enter__.return_value.submit
        args, _ = mock_submit.call_args
        assert args[0] == _run_optimizer_worker
        assert args[1] == Path("/tmp/extract/image.png")
        # Check command for pngquant
        expected_cmd = ["pngquant", "--quality", "65-80", "--ext", ".png", "--force", str(args[1])]
        assert args[2] == expected_cmd
