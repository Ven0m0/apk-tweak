"""Optimizer module tests."""

from __future__ import annotations

from pathlib import Path

from rvp.context import Context
from rvp.optimizer import debloat_apk, minify_resources


def test_debloat_apk(tmp_path: Path) -> None:
    """Test APK debloating functionality."""
    # Create fake decompiled APK structure
    decompiled_dir = tmp_path / "decompiled"
    decompiled_dir.mkdir()

    # Create bloatware files
    ads_dir = decompiled_dir / "com" / "google" / "ads"
    ads_dir.mkdir(parents=True)
    (ads_dir / "AdService.class").write_text("fake_class", encoding="utf-8")

    analytics_dir = decompiled_dir / "analytics"
    analytics_dir.mkdir(parents=True)
    (analytics_dir / "tracker.class").write_text("fake_class", encoding="utf-8")

    # Create context
    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
        options={"debloat_patterns": ["**/ads", "analytics"]},
    )
    # Create dummy APK
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Run debloat
    debloat_apk(decompiled_dir, ctx)

    # Verify bloatware removed
    assert not ads_dir.exists()
    assert not analytics_dir.exists()


def test_minify_resources(tmp_path: Path) -> None:
    """Test resource minification functionality."""
    # Create fake decompiled APK structure
    decompiled_dir = tmp_path / "decompiled"
    res_dir = decompiled_dir / "res" / "drawable-xxxhdpi"
    res_dir.mkdir(parents=True)

    # Create high-DPI resources
    (res_dir / "icon1.png").write_text("fake_png_data", encoding="utf-8")
    (res_dir / "icon2.png").write_text("fake_png_data", encoding="utf-8")

    # Create context
    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
        options={"minify_patterns": ["res/drawable-xxxhdpi/*"]},
    )
    # Create dummy APK
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Run minification
    minify_resources(decompiled_dir, ctx)

    # Verify resources removed
    assert not (res_dir / "icon1.png").exists()
    assert not (res_dir / "icon2.png").exists()


def test_debloat_no_patterns(tmp_path: Path) -> None:
    """Test debloat with no patterns specified."""
    decompiled_dir = tmp_path / "decompiled"
    decompiled_dir.mkdir()

    # Create some files
    (decompiled_dir / "test.txt").write_text("data", encoding="utf-8")

    ctx = Context(
        work_dir=tmp_path / "work",
        input_apk=tmp_path / "test.apk",
        output_dir=tmp_path / "out",
        engines=[],
        options={},  # No debloat_patterns
    )
    # Create dummy APK
    (tmp_path / "test.apk").write_text("fake", encoding="utf-8")

    # Should skip without error
    debloat_apk(decompiled_dir, ctx)

    # File should still exist
    assert (decompiled_dir / "test.txt").exists()
