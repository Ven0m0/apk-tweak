"""Tests for configuration management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rvp.config import Config


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_initialization(self) -> None:
        """Test Config with default values."""
        cfg = Config()

        assert cfg.input_apk is None
        assert cfg.output_dir == "out"
        assert cfg.engines == ["revanced"]
        assert cfg.dtlx_analyze is False
        assert cfg.dtlx_optimize is False
        assert cfg.revanced_optimize is True

    def test_custom_initialization(self) -> None:
        """Test Config with custom values."""
        cfg = Config(
            input_apk="test.apk",
            output_dir="custom_out",
            engines=["lspatch", "dtlx"],
            dtlx_analyze=True,
        )

        assert cfg.input_apk == "test.apk"
        assert cfg.output_dir == "custom_out"
        assert cfg.engines == ["lspatch", "dtlx"]
        assert cfg.dtlx_analyze is True

    def test_load_from_file_valid(
        self, tmp_path: Path
    ) -> None:
        """Test loading config from valid JSON file."""
        config_data = {
            "input_apk": "input.apk",
            "output_dir": "output",
            "engines": ["revanced"],
            "dtlx_analyze": True,
            "revanced_optimize": False,
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        cfg = Config.load_from_file(config_file)

        assert cfg.input_apk == "input.apk"
        assert cfg.output_dir == "output"
        assert cfg.engines == ["revanced"]
        assert cfg.dtlx_analyze is True
        assert cfg.revanced_optimize is False

    def test_load_from_file_missing(
        self, tmp_path: Path
    ) -> None:
        """Test loading from nonexistent file raises error."""
        missing_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            Config.load_from_file(missing_file)

    def test_load_from_file_invalid_json(
        self, tmp_path: Path
    ) -> None:
        """Test loading from invalid JSON raises error."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            Config.load_from_file(config_file)

    def test_load_from_file_partial_config(
        self, tmp_path: Path
    ) -> None:
        """Test loading partial config uses defaults."""
        config_data = {
            "input_apk": "custom.apk",
            "engines": ["lspatch"],
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        cfg = Config.load_from_file(config_file)

        assert cfg.input_apk == "custom.apk"
        assert cfg.engines == ["lspatch"]
        assert cfg.output_dir == "out"  # Default
        assert cfg.revanced_optimize is True  # Default

    def test_debloat_patterns_default(self) -> None:
        """Test default debloat patterns exist."""
        cfg = Config()

        assert len(cfg.debloat_patterns) > 0
        assert any("admob" in p for p in cfg.debloat_patterns)
        assert any("analytics" in p for p in cfg.debloat_patterns)

    def test_minify_patterns_default(self) -> None:
        """Test default minify patterns exist."""
        cfg = Config()

        assert len(cfg.minify_patterns) > 0
        assert any("xxxhdpi" in p for p in cfg.minify_patterns)
        assert any("raw" in p for p in cfg.minify_patterns)

    def test_rkpairip_options(self) -> None:
        """Test RKPairip configuration options."""
        cfg = Config(
            rkpairip_apktool_mode=True,
            rkpairip_dex_repair=True,
            rkpairip_corex_hook=False,
        )

        assert cfg.rkpairip_apktool_mode is True
        assert cfg.rkpairip_dex_repair is True
        assert cfg.rkpairip_corex_hook is False
        assert cfg.rkpairip_merge_skip is False  # Default
