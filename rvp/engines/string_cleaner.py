"""Android string resource cleanup engine for APK optimization."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from ..context import Context
from ..optimizer import decompile_apk
from ..optimizer import recompile_apk
from ..optimizer import zipalign_apk
from ..utils import require_input_apk

# Pre-compiled regex patterns
# Pattern: <string name="resource_name">value</string>
_STRING_DEF_PATTERN = re.compile(r'<string\s+name="([^"]+)"')
# Pattern 1: R.string.resource_name (Kotlin/Java/Smali)
_R_STRING_PATTERN = re.compile(r"R\.string\.([a-zA-Z0-9_]+)")
# Pattern 2: @string/resource_name (XML)
_XML_STRING_PATTERN = re.compile(r"@string/([a-zA-Z0-9_]+)")

# Pattern to match a string definition line and its trailing whitespace/newline
_XML_CLEANUP_PATTERN = re.compile(
  r'^\s*<string\s+name="([^"]+)"[^>]*>.*?</string>[ \t]*\n?', re.MULTILINE
)


class StringUsage(NamedTuple):
  """String resource usage information."""

  name: str
  is_used: bool
  locations: list[str]


def _extract_string_names(xml_content: str) -> set[str]:
  """
  Extract string resource names from strings.xml content.

  Args:
      xml_content: Content of strings.xml file.

  Returns:
      Set of string resource names.
  """
  return {match.group(1) for match in _STRING_DEF_PATTERN.finditer(xml_content)}


def _find_string_references(content: str) -> set[str]:
  """
  Find string resource references in file content (Smali or XML).

  Args:
      content: File content to search.

  Returns:
      Set of referenced string names.
  """
  references: set[str] = set()

  references.update(match.group(1) for match in _R_STRING_PATTERN.finditer(content))
  references.update(match.group(1) for match in _XML_STRING_PATTERN.finditer(content))

  return references


def _analyze_apk_strings(decompiled_dir: Path, ctx: Context) -> dict[str, StringUsage]:
  """
  Analyze decompiled APK directory to find unused string resources.

  Args:
      decompiled_dir: Directory containing decompiled APK.
      ctx: Pipeline context.

  Returns:
      Dictionary mapping string names to usage information.
  """
  ctx.log("string_cleaner: analyzing decompiled APK for string usage")

  all_strings: set[str] = set()
  used_strings: set[str] = set()
  string_locations: dict[str, list[str]] = {}

  # Reserved strings that should never be removed
  reserved = {"app_name", "app_name_suffixed"}

  # Find strings.xml files
  strings_files = list(decompiled_dir.rglob("strings.xml"))

  # Extract all defined strings
  for strings_file in strings_files:
    try:
      content = strings_file.read_text(encoding="utf-8", errors="ignore")
      file_strings = _extract_string_names(content)
      all_strings.update(file_strings)
      rel_path = str(strings_file.relative_to(decompiled_dir))
      for string_name in file_strings:
        string_locations.setdefault(string_name, []).append(rel_path)
      ctx.log(f"string_cleaner: found {len(file_strings)} strings in {rel_path}")
    except (OSError, UnicodeDecodeError) as e:
      ctx.log(f"string_cleaner: error reading {strings_file.name}: {e}")

  # Find files that might reference strings (XML and smali)
  source_files = [
    path
    for path in decompiled_dir.rglob("*")
    if path.is_file()
    and path.suffix in {".xml", ".smali"}
    and "drawable" not in path.parent.name
    and path.name != "strings.xml"
  ]

  ctx.log(f"string_cleaner: scanning {len(source_files)} source files")

  # Find all string references
  for source_file in source_files:
    try:
      content = source_file.read_text(encoding="utf-8", errors="ignore")
      references = _find_string_references(content)
      used_strings.update(references)
    except (OSError, UnicodeDecodeError):
      continue

  # Mark reserved strings as used
  used_strings.update(reserved)

  # Create usage map
  usage_map = {}
  for string_name in all_strings:
    is_used = string_name in used_strings
    usage_map[string_name] = StringUsage(
      name=string_name,
      is_used=is_used,
      locations=string_locations.get(string_name, []),
    )

  unused_count = sum(1 for usage in usage_map.values() if not usage.is_used)
  ctx.log(
    f"string_cleaner: analysis complete - {len(all_strings)} total, "
    f"{len(used_strings)} used, {unused_count} unused"
  )

  return usage_map


def _clean_xml_content(content: str, unused_strings: set[str]) -> str:
  """
  Remove unused string definitions from XML content.

  Args:
      content: XML content.
      unused_strings: Set of unused string names to remove.

  Returns:
      Cleaned XML content.
  """

  def replacer(match: re.Match[str]) -> str:
    name = match.group(1)
    if name in unused_strings:
      return ""
    return match.group(0)

  return _XML_CLEANUP_PATTERN.sub(replacer, content)


def _remove_unused_strings(
  decompiled_dir: Path, usage_map: dict[str, StringUsage], ctx: Context
) -> None:
  """
  Remove unused strings from XML files in the decompiled directory.

  Args:
      decompiled_dir: Directory containing decompiled APK.
      usage_map: String usage information.
      ctx: Pipeline context.
  """
  unused_strings = {name for name, usage in usage_map.items() if not usage.is_used}

  if not unused_strings:
    ctx.log("string_cleaner: no unused strings to remove")
    return

  ctx.log(f"string_cleaner: removing {len(unused_strings)} unused strings")

  # Find all unique locations where strings are defined
  all_locations = set()
  for string_name in unused_strings:
    all_locations.update(usage_map[string_name].locations)

  for rel_path in all_locations:
    file_path = decompiled_dir / rel_path
    if not file_path.exists():
      continue

    try:
      content = file_path.read_text(encoding="utf-8", errors="ignore")
      original_lines = len(content.splitlines())

      # Remove unused string definitions
      content = _clean_xml_content(content, unused_strings)

      cleaned_lines = len(content.splitlines())
      removed_lines = original_lines - cleaned_lines

      if removed_lines > 0:
        file_path.write_text(content, encoding="utf-8")
        ctx.log(f"string_cleaner: cleaned {rel_path} (removed {removed_lines} lines)")
    except (OSError, UnicodeError) as e:
      ctx.log(f"string_cleaner: error processing {rel_path}: {e}")


def run(ctx: Context) -> None:
  """
  Execute unused string resource cleanup.

  Analyzes APK for unused string resources and optionally removes them.
  Uses apktool to properly decompile and recompile binary AXML.

  Args:
      ctx: Pipeline context.
  """
  # Check if string cleanup is enabled
  clean_strings = ctx.options.get("clean_unused_strings", False)
  if not clean_strings:
    ctx.log("string_cleaner: disabled, skipping")
    return

  apk = require_input_apk(ctx)
  ctx.log(f"string_cleaner: analyzing {apk.name}")

  # Create working directory and decompile
  work_dir = ctx.work_dir / "string_cleaner"
  work_dir.mkdir(parents=True, exist_ok=True)

  # Properly decompile the APK using apktool to get plain XML
  try:
    decompiled_dir = decompile_apk(apk, work_dir, ctx)
  except Exception as e:
    ctx.log(f"string_cleaner: failed to decompile APK: {e}")
    return

  # Analyze string usage
  usage_map = _analyze_apk_strings(decompiled_dir, ctx)

  if not usage_map:
    ctx.log("string_cleaner: no strings found or analysis failed")
    return

  # Store analysis results in metadata
  unused_strings = [name for name, usage in usage_map.items() if not usage.is_used]
  ctx.metadata["string_cleaner"] = {
    "total_strings": len(usage_map),
    "unused_strings": len(unused_strings),
    "unused_names": sorted(unused_strings),
  }

  # Report unused strings
  if unused_strings:
    ctx.log(f"string_cleaner: found {len(unused_strings)} unused strings:")
    for string_name in sorted(unused_strings)[:10]:  # Show first 10
      ctx.log(f"  - {string_name}")
    if len(unused_strings) > 10:
      ctx.log(f"  ... and {len(unused_strings) - 10} more")

  # Remove unused strings if enabled
  remove_strings = ctx.options.get("remove_unused_strings", False)
  if remove_strings and unused_strings:
    _remove_unused_strings(decompiled_dir, usage_map, ctx)

    # Recompile and align
    temp_apk = work_dir / f"{apk.stem}_cleaned_unaligned.apk"
    cleaned_apk = work_dir / f"{apk.stem}.cleaned.apk"

    try:
      recompile_apk(decompiled_dir, temp_apk, ctx)
      zipalign_apk(temp_apk, cleaned_apk, ctx)

      if cleaned_apk.exists():
        # Calculate size reduction
        original_size = apk.stat().st_size
        cleaned_size = cleaned_apk.stat().st_size
        reduction = original_size - cleaned_size
        reduction_pct = (reduction / original_size) * 100 if original_size > 0 else 0

        ctx.log(
          f"string_cleaner: size reduction: {reduction / 1024:.2f} KB "
          f"({reduction_pct:.2f}%)"
        )
        ctx.metadata["string_cleaner"]["size_reduction"] = {
          "bytes": reduction,
          "percentage": reduction_pct,
        }

        # Update current APK
        ctx.set_current_apk(cleaned_apk)
        ctx.log(f"string_cleaner: pipeline will continue with {cleaned_apk.name}")
    except Exception as e:
      ctx.log(f"string_cleaner: failed to recompile/align APK: {e}")

  elif not remove_strings:
    ctx.log(
      "string_cleaner: analysis only mode (set remove_unused_strings=true to remove)"
    )
