"""Tests for input validation utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from rvp.validators import (
    ValidationError,
    validate_apk_path,
    validate_engine_names,
    validate_output_dir,
)


class TestValidateApkPath:
    """Tests for validate_apk_path function."""

    def test_valid_apk(self, tmp_path: Path) -> None:
        """Test validation of valid APK file."""
        apk = tmp_path / "test.apk"
        apk.write_bytes(b"PK\x03\x04")  # ZIP signature
        validate_apk_path(apk)  # Should not raise

    def test_nonexistent_apk(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent file."""
        apk = tmp_path / "missing.apk"
        with pytest.raises(
            ValidationError, match="APK file not found"
        ):
            validate_apk_path(apk)

    def test_directory_instead_of_file(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails for directory."""
        apk_dir = tmp_path / "test.apk"
        apk_dir.mkdir()
        with pytest.raises(
            ValidationError, match="APK path is not a file"
        ):
            validate_apk_path(apk_dir)

    def test_wrong_extension(self, tmp_path: Path) -> None:
        """Test validation fails for non-APK extension."""
        wrong_ext = tmp_path / "test.zip"
        wrong_ext.write_bytes(b"PK\x03\x04")
        with pytest.raises(
            ValidationError, match="File is not an APK"
        ):
            validate_apk_path(wrong_ext)

    def test_empty_apk(self, tmp_path: Path) -> None:
        """Test validation fails for empty file."""
        empty_apk = tmp_path / "empty.apk"
        empty_apk.touch()
        with pytest.raises(
            ValidationError, match="APK file is empty"
        ):
            validate_apk_path(empty_apk)


class TestValidateOutputDir:
    """Tests for validate_output_dir function."""

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test validation passes for nonexistent directory."""
        output_dir = tmp_path / "output"
        validate_output_dir(output_dir)  # Should not raise

    def test_existing_dir(self, tmp_path: Path) -> None:
        """Test validation passes for existing directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        validate_output_dir(output_dir)  # Should not raise

    def test_file_instead_of_dir(self, tmp_path: Path) -> None:
        """Test validation fails when path is a file."""
        file_path = tmp_path / "output.txt"
        file_path.write_text("test")
        with pytest.raises(
            ValidationError,
            match="Output path exists but is not a directory",
        ):
            validate_output_dir(file_path)


class TestValidateEngineNames:
    """Tests for validate_engine_names function."""

    def test_all_valid_engines(self) -> None:
        """Test validation with all valid engines."""
        available = {"revanced": None, "lspatch": None}
        unknown = validate_engine_names(
            ["revanced", "lspatch"], available
        )
        assert unknown == []

    def test_some_invalid_engines(self) -> None:
        """Test validation with some invalid engines."""
        available = {"revanced": None, "lspatch": None}
        unknown = validate_engine_names(
            ["revanced", "unknown", "invalid"], available
        )
        assert unknown == ["unknown", "invalid"]

    def test_empty_engine_list(self) -> None:
        """Test validation with empty engine list."""
        available = {"revanced": None}
        unknown = validate_engine_names([], available)
        assert unknown == []

    def test_all_invalid_engines(self) -> None:
        """Test validation with all invalid engines."""
        available = {"revanced": None}
        unknown = validate_engine_names(["foo", "bar"], available)
        assert unknown == ["foo", "bar"]
