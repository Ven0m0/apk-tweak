"""Android string resource cleanup engine for APK optimization."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import NamedTuple

from ..context import Context
from ..utils import require_input_apk

# Pre-compiled regex patterns
# Pattern: <string name="resource_name">value</string>
_STRING_DEF_PATTERN = re.compile(r'<string\s+name="([^"]+)"')
# Pattern 1: R.string.resource_name (Kotlin/Java)
_R_STRING_PATTERN = re.compile(r"R\.string\.([a-zA-Z0-9_]+)")
# Pattern 2: @string/resource_name (XML)
_XML_STRING_PATTERN = re.compile(r"@string/([a-zA-Z0-9_]+)")


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
  Find string resource references in file content (Kotlin or XML).

  Args:
      content: File content to search.

  Returns:
      Set of referenced string names.
  """
  references: set[str] = set()

  references.update(match.group(1) for match in _R_STRING_PATTERN.finditer(content))
  references.update(match.group(1) for match in _XML_STRING_PATTERN.finditer(content))

  return references


def _analyze_apk_strings(
  apk_path: Path, android_path: str, ctx: Context
) -> dict[str, StringUsage]:
  """
  Analyze APK to find unused string resources.

  Args:
      apk_path: Path to APK file.
      android_path: Base Android source path (e.g., src/android/app/src/main).
      ctx: Pipeline context.

  Returns:
      Dictionary mapping string names to usage information.
  """
  ctx.log("string_cleaner: analyzing APK for string usage")

  all_strings: set[str] = set()
  used_strings: set[str] = set()
  string_locations: dict[str, list[str]] = {}

  # Reserved strings that should never be removed
  reserved = {"app_name", "app_name_suffixed"}

  try:
    with zipfile.ZipFile(apk_path, "r") as zf:
      # Find strings.xml files
      strings_files = [name for name in zf.namelist() if name.endswith("strings.xml")]

      # Extract all defined strings
      for strings_file in strings_files:
        try:
          content = zf.read(strings_file).decode("utf-8", errors="ignore")
          file_strings = _extract_string_names(content)
          all_strings.update(file_strings)
          for string_name in file_strings:
            string_locations.setdefault(string_name, []).append(strings_file)
          ctx.log(
            f"string_cleaner: found {len(file_strings)} strings in {strings_file}"
          )
        except (UnicodeDecodeError, Exception) as e:
          ctx.log(f"string_cleaner: error reading {strings_file}: {e}")

      # Find files that might reference strings (XML and Kotlin)
      source_files = [
        name
        for name in zf.namelist()
        if (name.endswith((".xml", ".kt", ".java")) and "drawable" not in name)
        and not name.endswith("strings.xml")
      ]

      ctx.log(f"string_cleaner: scanning {len(source_files)} source files")

      # Find all string references
      for source_file in source_files:
        try:
          content = zf.read(source_file).decode("utf-8", errors="ignore")
          references = _find_string_references(content)
          used_strings.update(references)
        except (UnicodeDecodeError, Exception):
          # Skip files that can't be decoded
          continue

  except (zipfile.BadZipFile, OSError) as e:
    ctx.log(f"string_cleaner: error analyzing APK: {e}")
    return {}

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


def _remove_unused_strings(
  apk_path: Path, usage_map: dict[str, StringUsage], ctx: Context
) -> Path:
  """
  Create new APK with unused strings removed.

  Args:
      apk_path: Path to input APK.
      usage_map: String usage information.
      ctx: Pipeline context.

  Returns:
      Path to cleaned APK.
  """
  unused_strings = {name for name, usage in usage_map.items() if not usage.is_used}

  if not unused_strings:
    ctx.log("string_cleaner: no unused strings to remove")
    return apk_path

  ctx.log(f"string_cleaner: removing {len(unused_strings)} unused strings")

  # Create output APK
  output_apk = ctx.work_dir / "string_cleaner" / f"{apk_path.stem}.cleaned.apk"
  output_apk.parent.mkdir(parents=True, exist_ok=True)

  try:
    with (
      zipfile.ZipFile(apk_path, "r") as zf_in,
      zipfile.ZipFile(output_apk, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf_out,
    ):
      for item in zf_in.namelist():
        data = zf_in.read(item)

        # Process strings.xml files
        if item.endswith("strings.xml"):
          try:
            content = data.decode("utf-8", errors="ignore")
            original_lines = len(content.splitlines())

            # Remove unused string definitions
            for string_name in unused_strings:
              # Pattern to match entire string definition line
              pattern = re.compile(
                rf'^\s*<string\s+name="{re.escape(string_name)}"[^>]*>.*?</string>\s*$',
                re.MULTILINE,
              )
              content = pattern.sub("", content)

            cleaned_lines = len(content.splitlines())
            removed_lines = original_lines - cleaned_lines

            if removed_lines > 0:
              ctx.log(f"string_cleaner: cleaned {item} (removed {removed_lines} lines)")

            data = content.encode("utf-8")
          except (UnicodeDecodeError, Exception) as e:
            ctx.log(f"string_cleaner: error processing {item}: {e}")

        zf_out.writestr(item, data)

    ctx.log(f"string_cleaner: created cleaned APK: {output_apk.name}")
    return output_apk

  except (zipfile.BadZipFile, OSError) as e:
    ctx.log(f"string_cleaner: error creating cleaned APK: {e}")
    return apk_path


def run(ctx: Context) -> None:
  """
  Execute unused string resource cleanup.

  Analyzes APK for unused string resources and optionally removes them.

  Args:
      ctx: Pipeline context.
  """
  # Check if string cleanup is enabled
  clean_strings = ctx.options.get("clean_unused_strings", False)
  if not clean_strings:
    ctx.log("string_cleaner: disabled, skipping")
    return

  # Get Android source path from options
  android_path_opt = ctx.options.get("android_source_path", "src/android/app/src/main")
  android_path = (
    android_path_opt
    if isinstance(android_path_opt, str)
    else "src/android/app/src/main"
  )

  apk = require_input_apk(ctx)
  ctx.log(f"string_cleaner: analyzing {apk.name}")

  # Analyze string usage
  usage_map = _analyze_apk_strings(apk, android_path, ctx)

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
    cleaned_apk = _remove_unused_strings(apk, usage_map, ctx)

    if cleaned_apk != apk:
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
  elif not remove_strings:
    ctx.log(
      "string_cleaner: analysis only mode (set remove_unused_strings=true to remove)"
    )
