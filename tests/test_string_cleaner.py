from rvp.engines.string_cleaner import _clean_xml_content


def test_clean_xml_content_basic() -> None:
  content = """<resources>
    <string name="used">Value 1</string>
    <string name="unused">Value 2</string>
</resources>"""
  unused = {"unused"}

  # We expect the line containing "unused" to be removed completely, including the newline.
  # So "used" line matches \n at end.
  # "unused" line matches \n at end.
  # Result should be:
  # <resources>\n    <string name="used">Value 1</string>\n</resources>

  expected = """<resources>
    <string name="used">Value 1</string>
</resources>"""

  assert _clean_xml_content(content, unused) == expected


def test_clean_xml_content_consecutive() -> None:
  content = """<resources>
    <string name="u1">v1</string>
    <string name="u2">v2</string>
    <string name="k1">v3</string>
</resources>"""
  unused = {"u1", "u2"}

  expected = """<resources>
    <string name="k1">v3</string>
</resources>"""

  assert _clean_xml_content(content, unused) == expected


def test_clean_xml_content_with_empty_lines() -> None:
  content = """<resources>
    <string name="u1">v1</string>

    <string name="u2">v2</string>
</resources>"""
  unused = {"u1"}

  # Removing u1. u1 line ends with \n.
  # There is an empty line (\n) after u1.
  # Then u2.
  # The regex consumes u1 line and its newline.
  # The empty line remains.

  expected = """<resources>

    <string name="u2">v2</string>
</resources>"""

  assert _clean_xml_content(content, unused) == expected


def test_clean_xml_content_preserves_indentation() -> None:
  content = """<resources>
    <string name="keep">v</string>
</resources>"""
  unused: set[str] = set()

  assert _clean_xml_content(content, unused) == content


def test_clean_xml_content_special_chars() -> None:
  content = """<resources>
    <string name="s_1">Value "quoted"</string>
    <string name="s-2">Value &amp;</string>
</resources>"""
  unused = {"s_1"}

  expected = """<resources>
    <string name="s-2">Value &amp;</string>
</resources>"""

  assert _clean_xml_content(content, unused) == expected


def test_clean_xml_content_multiline_definition() -> None:
  # Note: Our regex assumes <string ...>...</string> is effectively on one line
  # (or rather, the regex uses .*? which doesn't match newlines without DOTALL).
  # If the string definition spans multiple lines, the current implementation (and original)
  # likely FAILS to match it properly if the newline is in the value.
  # But let's verify what happens.

  content = """<resources>
    <string name="multi">
        Line 1
        Line 2
    </string>
</resources>"""
  unused = {"multi"}

  # Original regex: .*? without DOTALL -> does NOT match newline.
  # So it won't match "Line 1\n...".
  # So it won't be removed.
  # This is existing behavior (limitation), we should probably preserve it or document it.
  # Or if the original implementation didn't handle it, we shouldn't worry about it for optimization task.
  # We will assert that it remains unchanged (or partially matched?)

  # Actually, <string ...> matches. .*? matches until newline.
  # If the closing </string> is on a later line, the regex won't find it on the same line.
  # So it fails to match.

  assert _clean_xml_content(content, unused) == content
