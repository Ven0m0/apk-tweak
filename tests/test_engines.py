"""Engine-specific tests."""

from __future__ import annotations

from pathlib import Path

from rvp.context import Context
from rvp.engines import dtlx, magisk, revanced


def test_revanced_engine(tmp_path: Path) -> None:
    """Test ReVanced engine execution."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data", encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["revanced"],
    )

    revanced.run(ctx)

    # Check that output APK was created
    assert ctx.current_apk is not None
    assert ctx.current_apk.exists()
    assert ctx.current_apk.name.endswith(".revanced.apk")


def test_dtlx_engine_skip(tmp_path: Path) -> None:
    """Test DTL-X engine when no options are set (should skip)."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data", encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["dtlx"],
    )

    # Should skip when no options are set
    dtlx.run(ctx)

    # No report should be created
    reports = list(output_dir.glob("*.dtlx-report.txt"))
    assert len(reports) == 0


def test_dtlx_engine_with_analyze(tmp_path: Path) -> None:
    """Test DTL-X engine with analyze option."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data", encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["dtlx"],
        options={"dtlx_analyze": True},
    )

    dtlx.run(ctx)

    # Report should be created
    assert "dtlx" in ctx.metadata
    assert "report" in ctx.metadata["dtlx"]
    report_path = Path(ctx.metadata["dtlx"]["report"])
    assert report_path.exists()
    assert "analyze=True" in report_path.read_text(encoding="utf-8")


def test_magisk_engine(tmp_path: Path) -> None:
    """Test Magisk module packaging."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data", encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["magisk"],
    )

    magisk.run(ctx)

    # Check that module ZIP was created
    assert "magisk_module" in ctx.metadata
    module_path = Path(ctx.metadata["magisk_module"])
    assert module_path.exists()
    assert module_path.name.endswith("-magisk.zip")


def test_revanced_engine_multi_patch(tmp_path: Path) -> None:
    """Test ReVanced engine with multiple patch bundles."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data" * 100, encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    # Create fake patch bundles
    patches1 = tmp_path / "patches1.jar"
    patches2 = tmp_path / "patches2.jar"
    patches1.write_text("fake_patch", encoding="utf-8")
    patches2.write_text("fake_patch", encoding="utf-8")

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["revanced"],
        options={
            "revanced_patch_bundles": [str(patches1), str(patches2)],
            "revanced_optimize": False,  # Disable optimization for stub test
        },
    )

    revanced.run(ctx)

    # Check that output APK was created (stub mode)
    assert ctx.current_apk is not None
    assert ctx.current_apk.exists()
    assert "revanced" in ctx.metadata


def test_revanced_engine_with_optimization_disabled(tmp_path: Path) -> None:
    """Test ReVanced engine with optimization disabled."""
    input_apk = tmp_path / "input.apk"
    input_apk.write_text("fake_apk_data" * 50, encoding="utf-8")
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    ctx = Context(
        work_dir=work_dir,
        input_apk=input_apk,
        output_dir=output_dir,
        engines=["revanced"],
        options={"revanced_optimize": False},
    )

    revanced.run(ctx)

    # Check that output APK was created
    assert ctx.current_apk is not None
    assert ctx.current_apk.exists()
    assert ctx.metadata.get("revanced", {}).get("optimized") is False
