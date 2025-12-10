"""Unit tests for validators module."""

from __future__ import annotations

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
        """Test validation of a valid APK file."""
        apk = tmp_path / "test.apk"
        apk.write_bytes(b"PK\x03\x04")  # Minimal APK header
        validate_apk_path(apk)  # Should not raise

    def test_nonexistent_apk(self, tmp_path: Path) -> None:
        """Test validation fails for nonexistent APK."""
        apk = tmp_path / "nonexistent.apk"
        with pytest.raises(ValidationError, match="APK file not found"):
            validate_apk_path(apk)

    def test_apk_is_directory(self, tmp_path: Path) -> None:
        """Test validation fails when APK path is a directory."""
        apk_dir = tmp_path / "test.apk"
        apk_dir.mkdir()
        with pytest.raises(ValidationError, match="is not a file"):
            validate_apk_path(apk_dir)

    def test_wrong_extension(self, tmp_path: Path) -> None:
        """Test validation fails for non-.apk files."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_bytes(b"content")
        with pytest.raises(ValidationError, match="File is not an APK"):
            validate_apk_path(txt_file)

    def test_empty_apk(self, tmp_path: Path) -> None:
        """Test validation fails for empty APK files."""
        apk = tmp_path / "empty.apk"
        apk.touch()  # Create empty file
        with pytest.raises(ValidationError, match="APK file is empty"):
            validate_apk_path(apk)

    def test_case_insensitive_extension(self, tmp_path: Path) -> None:
        """Test validation accepts .APK extension (uppercase)."""
        apk = tmp_path / "test.APK"
        apk.write_bytes(b"PK\x03\x04")
        validate_apk_path(apk)  # Should not raise


class TestValidateOutputDir:
    """Tests for validate_output_dir function."""

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test validation passes for nonexistent directory (will be created)."""
        output_dir = tmp_path / "output"
        validate_output_dir(output_dir)  # Should not raise

    def test_existing_directory(self, tmp_path: Path) -> None:
        """Test validation passes for existing directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        validate_output_dir(output_dir)  # Should not raise

    def test_path_is_file(self, tmp_path: Path) -> None:
        """Test validation fails when output path is an existing file."""
        file_path = tmp_path / "output"
        file_path.write_text("content")
        with pytest.raises(
            ValidationError, match="exists but is not a directory"
        ):
            validate_output_dir(file_path)


class TestValidateEngineNames:
    """Tests for validate_engine_names function."""

    def test_all_engines_valid(self) -> None:
        """Test validation with all known engines."""
        engines = ["revanced", "lspatch"]
        available = {"revanced": object(), "lspatch": object()}
        unknown = validate_engine_names(engines, available)
        assert unknown == []

    def test_some_engines_unknown(self) -> None:
        """Test validation identifies unknown engines."""
        engines = ["revanced", "unknown1", "lspatch", "unknown2"]
        available = {"revanced": object(), "lspatch": object()}
        unknown = validate_engine_names(engines, available)
        assert unknown == ["unknown1", "unknown2"]

    def test_all_engines_unknown(self) -> None:
        """Test validation with all unknown engines."""
        engines = ["unknown1", "unknown2"]
        available = {"revanced": object()}
        unknown = validate_engine_names(engines, available)
        assert unknown == ["unknown1", "unknown2"]

    def test_empty_engine_list(self) -> None:
        """Test validation with empty engine list."""
        engines: list[str] = []
        available = {"revanced": object()}
        unknown = validate_engine_names(engines, available)
        assert unknown == []

    def test_empty_available_engines(self) -> None:
        """Test validation when no engines are available."""
        engines = ["revanced"]
        available: dict[str, object] = {}
        unknown = validate_engine_names(engines, available)
        assert unknown == ["revanced"]
