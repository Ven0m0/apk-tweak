"""Tests for optimizer utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from rvp.context import Context
from rvp.optimizer import minify_resources


@pytest.fixture
def optimizer_context(tmp_path: Path) -> Context:
    """Create a minimal context for optimizer tests."""
    work_dir = tmp_path / "work"
    output_dir = tmp_path / "output"
    apk = tmp_path / "input.apk"
    apk.write_bytes(b"PK\x03\x04")

    ctx = Context(
        work_dir=work_dir,
        input_apk=apk,
        output_dir=output_dir,
        engines=[],
        options={},
    )
    ctx.set_current_apk(apk)
    return ctx


def test_minify_resources_removes_patterned_files(
    optimizer_context: Context, tmp_path: Path
) -> None:
    """Ensure minify_resources removes files matching configured patterns."""
    decompiled_dir = tmp_path / "decompiled"
    drawable_dir = decompiled_dir / "res" / "drawable-xxxhdpi"
    unused_dir = decompiled_dir / "assets" / "unused"
    keep_dir = decompiled_dir / "res" / "drawable-hdpi"

    drawable_dir.mkdir(parents=True, exist_ok=True)
    unused_dir.mkdir(parents=True, exist_ok=True)
    keep_dir.mkdir(parents=True, exist_ok=True)

    icon_file = drawable_dir / "icon.png"
    unused_file = unused_dir / "data.bin"
    keep_file = keep_dir / "keep.png"

    icon_file.write_bytes(b"icon")
    unused_file.write_bytes(b"data")
    keep_file.write_bytes(b"keep")

    optimizer_context.options["minify_patterns"] = [
        "res/drawable-xxxhdpi/*",
        "assets/unused/*",
    ]

    minify_resources(decompiled_dir, optimizer_context)

    assert not icon_file.exists()
    assert not unused_file.exists()
    assert keep_file.exists()
