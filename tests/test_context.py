"""Tests for pipeline context management."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rvp.context import Context


class TestContext:
    """Tests for Context dataclass."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test basic context initialization."""
        work_dir = tmp_path / "work"
        input_apk = tmp_path / "test.apk"
        input_apk.touch()
        output_dir = tmp_path / "output"
        engines = ["revanced", "lspatch"]

        ctx = Context(
            work_dir=work_dir,
            input_apk=input_apk,
            output_dir=output_dir,
            engines=engines,
        )

        assert ctx.work_dir == work_dir
        assert ctx.input_apk == input_apk
        assert ctx.output_dir == output_dir
        assert ctx.engines == engines
        assert ctx.current_apk == input_apk
        assert ctx.options == {}
        assert ctx.metadata == {}

    def test_directories_created(self, tmp_path: Path) -> None:
        """Test that work_dir and output_dir are created."""
        work_dir = tmp_path / "work"
        output_dir = tmp_path / "output"
        input_apk = tmp_path / "test.apk"
        input_apk.touch()

        ctx = Context(
            work_dir=work_dir,
            input_apk=input_apk,
            output_dir=output_dir,
            engines=[],
        )

        assert work_dir.exists()
        assert work_dir.is_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_set_current_apk_valid(
        self, tmp_path: Path
    ) -> None:
        """Test setting current APK to valid path."""
        input_apk = tmp_path / "input.apk"
        input_apk.touch()
        new_apk = tmp_path / "output.apk"
        new_apk.touch()

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=input_apk,
            output_dir=tmp_path / "out",
            engines=[],
        )

        ctx.set_current_apk(new_apk)
        assert ctx.current_apk == new_apk

    def test_set_current_apk_missing(
        self, tmp_path: Path
    ) -> None:
        """Test setting current APK to nonexistent path."""
        input_apk = tmp_path / "input.apk"
        input_apk.touch()
        missing_apk = tmp_path / "missing.apk"

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=input_apk,
            output_dir=tmp_path / "out",
            engines=[],
        )

        with pytest.raises(FileNotFoundError):
            ctx.set_current_apk(missing_apk)

    def test_log_method(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging functionality."""
        input_apk = tmp_path / "test.apk"
        input_apk.touch()

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=input_apk,
            output_dir=tmp_path / "out",
            engines=[],
        )

        with caplog.at_level(logging.INFO):
            ctx.log("Test message")
            assert "Test message" in caplog.text

    def test_options_persistence(self, tmp_path: Path) -> None:
        """Test that options are properly stored."""
        input_apk = tmp_path / "test.apk"
        input_apk.touch()

        options = {
            "revanced_optimize": True,
            "dtlx_analyze": False,
        }

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=input_apk,
            output_dir=tmp_path / "out",
            engines=[],
            options=options,
        )

        assert ctx.options == options
        assert ctx.options["revanced_optimize"] is True

    def test_metadata_storage(self, tmp_path: Path) -> None:
        """Test metadata dictionary functionality."""
        input_apk = tmp_path / "test.apk"
        input_apk.touch()

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=input_apk,
            output_dir=tmp_path / "out",
            engines=[],
        )

        ctx.metadata["engine1"] = {"status": "completed"}
        ctx.metadata["engine2"] = {"files_processed": 42}

        assert ctx.metadata["engine1"]["status"] == "completed"
        assert ctx.metadata["engine2"]["files_processed"] == 42
