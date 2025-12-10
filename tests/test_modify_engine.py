"""Unit tests for modify engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rvp.context import Context
from rvp.engines.modify import (
    _decompile_apk,
    _modify_icon,
    _recompile_apk,
    _replace_server_url,
    _sign_apk,
    run,
)


@pytest.fixture
def mock_context(tmp_path: Path) -> Context:
    """Create a mock context for testing."""
    work_dir = tmp_path / "work"
    output_dir = tmp_path / "output"
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    apk = tmp_path / "test.apk"
    apk.write_bytes(b"PK\x03\x04")  # Minimal APK header

    ctx = Context(
        work_dir=work_dir,
        input_apk=apk,
        output_dir=output_dir,
        engines=["modify"],
        options={},
    )
    ctx.set_current_apk(apk)
    return ctx


class TestModifyIcon:
    """Tests for _modify_icon function."""

    def test_modify_icon_no_icon_path(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test icon modification with no icon specified."""
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()

        result = _modify_icon(mock_context, decompiled_dir, None)
        assert result is False

    def test_modify_icon_nonexistent_icon(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test icon modification with nonexistent icon file."""
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()
        icon_path = tmp_path / "nonexistent.png"

        result = _modify_icon(mock_context, decompiled_dir, icon_path)
        assert result is False

    @patch("shutil.which")
    def test_modify_icon_no_imagemagick(
        self,
        mock_which: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test icon modification without ImageMagick."""
        mock_which.return_value = None

        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()
        icon_path = tmp_path / "icon.png"
        icon_path.write_bytes(b"PNG_DATA")

        result = _modify_icon(mock_context, decompiled_dir, icon_path)
        assert result is False

    def test_modify_icon_no_res_directory(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test icon modification when res directory is missing."""
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()
        icon_path = tmp_path / "icon.png"
        icon_path.write_bytes(b"PNG_DATA")

        with patch("shutil.which", return_value="/usr/bin/magick"):
            result = _modify_icon(mock_context, decompiled_dir, icon_path)
            assert result is False


class TestReplaceServerUrl:
    """Tests for _replace_server_url function."""

    def test_replace_url_no_smali_dirs(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test URL replacement when no smali directories exist."""
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()

        result = _replace_server_url(
            mock_context,
            decompiled_dir,
            "https://old.com",
            "https://new.com",
        )
        assert result is False

    def test_replace_url_success(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test successful URL replacement in Smali files."""
        decompiled_dir = tmp_path / "decompiled"
        smali_dir = decompiled_dir / "smali"
        smali_dir.mkdir(parents=True)

        # Create a test Smali file with URL
        test_smali = smali_dir / "TestClass.smali"
        test_smali.write_text(
            'const-string v0, "https://old.com/api"\n'
            "invoke-virtual {v0}, Ljava/net/URL;-><init>(Ljava/lang/String;)V",
            encoding="utf-8",
        )

        result = _replace_server_url(
            mock_context,
            decompiled_dir,
            "https://old.com",
            "https://new.com",
        )
        assert result is True

        # Verify replacement
        modified_content = test_smali.read_text(encoding="utf-8")
        assert "https://new.com" in modified_content
        assert "https://old.com" not in modified_content

    def test_replace_url_multiple_files(
        self, mock_context: Context, tmp_path: Path
    ) -> None:
        """Test URL replacement across multiple Smali files."""
        decompiled_dir = tmp_path / "decompiled"
        smali_dir = decompiled_dir / "smali"
        smali_dir.mkdir(parents=True)

        # Create multiple test files
        for i in range(3):
            test_smali = smali_dir / f"Class{i}.smali"
            test_smali.write_text(
                f'const-string v{i}, "https://old.com/endpoint{i}"',
                encoding="utf-8",
            )

        result = _replace_server_url(
            mock_context,
            decompiled_dir,
            "https://old.com",
            "https://new.com",
        )
        assert result is True


class TestDecompileApk:
    """Tests for _decompile_apk function."""

    @patch("rvp.engines.modify.run_command")
    def test_decompile_success(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test successful APK decompilation."""
        output_dir = tmp_path / "decompiled"

        # Simulate successful decompilation by creating the directory
        def create_output(*args: object, **kwargs: object) -> None:
            output_dir.mkdir(parents=True, exist_ok=True)

        mock_run.side_effect = create_output

        result = _decompile_apk(
            mock_context, mock_context.input_apk, output_dir
        )
        assert result is True
        assert mock_run.called

    @patch("rvp.engines.modify.run_command")
    def test_decompile_failure(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test APK decompilation failure."""
        mock_run.side_effect = RuntimeError("apktool failed")
        output_dir = tmp_path / "decompiled"

        result = _decompile_apk(
            mock_context, mock_context.input_apk, output_dir
        )
        assert result is False


class TestRecompileApk:
    """Tests for _recompile_apk function."""

    @patch("rvp.engines.modify.run_command")
    def test_recompile_success(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test successful APK recompilation."""
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()
        output_apk = tmp_path / "output.apk"

        # Simulate successful recompilation
        def create_apk(*args: object, **kwargs: object) -> None:
            output_apk.write_bytes(b"PK\x03\x04")

        mock_run.side_effect = create_apk

        result = _recompile_apk(mock_context, decompiled_dir, output_apk)
        assert result is True
        assert mock_run.called

    @patch("rvp.engines.modify.run_command")
    def test_recompile_failure(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test APK recompilation failure."""
        mock_run.side_effect = RuntimeError("apktool build failed")
        decompiled_dir = tmp_path / "decompiled"
        decompiled_dir.mkdir()
        output_apk = tmp_path / "output.apk"

        result = _recompile_apk(mock_context, decompiled_dir, output_apk)
        assert result is False


class TestSignApk:
    """Tests for _sign_apk function."""

    @patch("rvp.engines.modify.run_command")
    def test_sign_creates_keystore(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test APK signing creates keystore if missing."""
        unsigned_apk = tmp_path / "unsigned.apk"
        unsigned_apk.write_bytes(b"PK\x03\x04")
        signed_apk = tmp_path / "signed.apk"

        # Simulate successful signing
        def create_signed(*args: object, **kwargs: object) -> None:
            signed_apk.write_bytes(b"PK\x03\x04SIGNED")

        mock_run.side_effect = create_signed

        result = _sign_apk(mock_context, unsigned_apk, signed_apk)
        assert result is True
        # Should call run_command twice: keytool + apksigner
        assert mock_run.call_count == 2

    @patch("rvp.engines.modify.run_command")
    def test_sign_uses_existing_keystore(
        self,
        mock_run: Mock,
        mock_context: Context,
        tmp_path: Path,
    ) -> None:
        """Test APK signing uses existing keystore."""
        # Create existing keystore
        keystore = mock_context.work_dir / "keystore.jks"
        keystore.write_bytes(b"KEYSTORE_DATA")

        unsigned_apk = tmp_path / "unsigned.apk"
        unsigned_apk.write_bytes(b"PK\x03\x04")
        signed_apk = tmp_path / "signed.apk"

        # Simulate successful signing
        def create_signed(*args: object, **kwargs: object) -> None:
            signed_apk.write_bytes(b"PK\x03\x04SIGNED")

        mock_run.side_effect = create_signed

        result = _sign_apk(mock_context, unsigned_apk, signed_apk)
        assert result is True
        # Should only call apksigner (keystore exists)
        assert mock_run.call_count == 1


class TestModifyRun:
    """Tests for main run function."""

    @patch("rvp.engines.modify.check_dependencies")
    def test_run_no_input_apk(self, mock_check: Mock, tmp_path: Path) -> None:
        """Test run fails with no input APK."""
        # Mock dependencies to pass the check
        mock_check.return_value = (True, [])

        # Create a fake APK for initialization
        fake_apk = tmp_path / "test.apk"
        fake_apk.write_bytes(b"PK\x03\x04")

        ctx = Context(
            work_dir=tmp_path / "work",
            input_apk=fake_apk,
            output_dir=tmp_path / "output",
            engines=["modify"],
            options={},
        )
        # Clear both APKs to simulate no input (set to None, not a path)
        ctx.current_apk = None
        ctx.input_apk = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="No input APK found"):
            run(ctx)

    @patch("rvp.engines.modify.check_dependencies")
    def test_run_missing_dependencies(
        self, mock_check: Mock, mock_context: Context
    ) -> None:
        """Test run fails with missing dependencies."""
        mock_check.return_value = (False, ["apktool", "apksigner"])

        with pytest.raises(RuntimeError, match="Missing dependencies"):
            run(mock_context)

    @patch("rvp.engines.modify._sign_apk")
    @patch("rvp.engines.modify._recompile_apk")
    @patch("rvp.engines.modify._decompile_apk")
    @patch("rvp.engines.modify.check_dependencies")
    def test_run_success(
        self,
        mock_check: Mock,
        mock_decompile: Mock,
        mock_recompile: Mock,
        mock_sign: Mock,
        mock_context: Context,
    ) -> None:
        """Test successful modify engine execution."""
        mock_check.return_value = (True, [])
        mock_decompile.return_value = True
        mock_recompile.return_value = True

        # Make mock_sign create the signed APK file
        def create_signed_apk(
            ctx: Context, unsigned: Path, signed: Path
        ) -> bool:
            signed.write_bytes(b"PK\x03\x04SIGNED")
            return True

        mock_sign.side_effect = create_signed_apk

        run(mock_context)

        assert mock_decompile.called
        assert mock_recompile.called
        assert mock_sign.called
        assert mock_context.current_apk is not None
        assert "modify" in mock_context.metadata

    @patch("rvp.engines.modify._decompile_apk")
    @patch("rvp.engines.modify.check_dependencies")
    def test_run_decompile_failure(
        self,
        mock_check: Mock,
        mock_decompile: Mock,
        mock_context: Context,
    ) -> None:
        """Test run fails when decompilation fails."""
        mock_check.return_value = (True, [])
        mock_decompile.return_value = False

        with pytest.raises(RuntimeError, match="Decompilation failed"):
            run(mock_context)
