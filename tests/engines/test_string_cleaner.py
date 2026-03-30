from pathlib import Path

from rvp.context import Context
from rvp.engines.string_cleaner import StringUsage
from rvp.engines.string_cleaner import _analyze_apk_strings
from rvp.engines.string_cleaner import _remove_unused_strings


def test_analyze_apk_strings(mock_context: Context, tmp_path: Path):
  # Setup mock decompiled directory
  decompiled_dir = tmp_path / "decompiled"
  decompiled_dir.mkdir()

  res_dir = decompiled_dir / "res" / "values"
  res_dir.mkdir(parents=True)

  strings_xml = res_dir / "strings.xml"
  strings_xml.write_text("""
    <resources>
        <string name="app_name">My App</string>
        <string name="used_string">Used</string>
        <string name="unused_string">Unused</string>
    </resources>
    """)

  smali_dir = decompiled_dir / "smali"
  smali_dir.mkdir()
  (smali_dir / "Test.smali").write_text('const-string v0, "R.string.used_string"')

  # Add a drawable directory to test pruning
  drawable_dir = decompiled_dir / "res" / "drawable"
  drawable_dir.mkdir(parents=True)
  (drawable_dir / "icon.xml").write_text("<vector/>")

  usage_map = _analyze_apk_strings(decompiled_dir, mock_context)

  assert "app_name" in usage_map
  assert usage_map["app_name"].is_used is True  # Reserved

  assert "used_string" in usage_map
  assert usage_map["used_string"].is_used is True

  assert "unused_string" in usage_map
  assert usage_map["unused_string"].is_used is False


def test_remove_unused_strings(mock_context: Context, tmp_path: Path):
  decompiled_dir = tmp_path / "decompiled_remove"
  decompiled_dir.mkdir()

  res_dir = decompiled_dir / "res" / "values"
  res_dir.mkdir(parents=True)

  strings_xml = res_dir / "strings.xml"
  content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="used">Keep</string>
    <string name="unused">Remove</string>
</resources>"""
  strings_xml.write_text(content)

  usage_map = {
    "used": StringUsage(
      name="used", is_used=True, locations=["res/values/strings.xml"]
    ),
    "unused": StringUsage(
      name="unused", is_used=False, locations=["res/values/strings.xml"]
    ),
  }

  _remove_unused_strings(decompiled_dir, usage_map, mock_context)

  new_content = strings_xml.read_text()
  assert 'name="used"' in new_content
  assert 'name="unused"' not in new_content
