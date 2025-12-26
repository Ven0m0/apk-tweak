"""Tests for string_cleaner engine."""

from __future__ import annotations

from rvp.engines.string_cleaner import _extract_string_names
from rvp.engines.string_cleaner import _find_string_references


def test_extract_string_names() -> None:
  """Test extraction of string resource names from XML."""
  xml_content = """
    <resources>
        <string name="app_name">My App</string>
        <string name="welcome_message">Welcome!</string>
        <string name="button_submit">Submit</string>
    </resources>
    """

  names = _extract_string_names(xml_content)

  assert "app_name" in names
  assert "welcome_message" in names
  assert "button_submit" in names
  assert len(names) == 3


def test_extract_string_names_with_attributes() -> None:
  """Test extraction of string names with additional attributes."""
  xml_content = """
    <resources>
        <string name="app_name" translatable="false">My App</string>
        <string name="description" formatted="true">Description: %s</string>
    </resources>
    """

  names = _extract_string_names(xml_content)

  assert "app_name" in names
  assert "description" in names
  assert len(names) == 2


def test_find_string_references_r_string() -> None:
  """Test finding R.string.* references in Kotlin/Java code."""
  kotlin_content = """
    class MainActivity {
        fun onCreate() {
            val title = getString(R.string.app_name)
            val message = getString(R.string.welcome_message)
        }
    }
    """

  references = _find_string_references(kotlin_content)

  assert "app_name" in references
  assert "welcome_message" in references
  assert len(references) == 2


def test_find_string_references_xml() -> None:
  """Test finding @string/* references in XML layouts."""
  xml_content = """
    <LinearLayout>
        <TextView
            android:text="@string/welcome_message"
            android:hint="@string/input_hint" />
        <Button android:text="@string/button_submit" />
    </LinearLayout>
    """

  references = _find_string_references(xml_content)

  assert "welcome_message" in references
  assert "input_hint" in references
  assert "button_submit" in references
  assert len(references) == 3


def test_find_string_references_mixed() -> None:
  """Test finding both R.string and @string references."""
  mixed_content = """
    R.string.app_name
    @string/welcome_message
    R.string.another_string
    """

  references = _find_string_references(mixed_content)

  assert "app_name" in references
  assert "welcome_message" in references
  assert "another_string" in references
  assert len(references) == 3


def test_find_string_references_with_underscores() -> None:
  """Test string references with underscores and numbers."""
  content = """
    R.string.test_string_123
    @string/another_test_456
    R.string.final_test_string_789
    """

  references = _find_string_references(content)

  assert "test_string_123" in references
  assert "another_test_456" in references
  assert "final_test_string_789" in references


def test_extract_string_names_empty() -> None:
  """Test extraction from empty XML."""
  xml_content = "<resources></resources>"

  names = _extract_string_names(xml_content)

  assert len(names) == 0


def test_find_string_references_empty() -> None:
  """Test finding references in content without any."""
  content = "This is just plain text with no references."

  references = _find_string_references(content)

  assert len(references) == 0
