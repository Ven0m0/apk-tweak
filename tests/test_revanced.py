from typing import Any
from unittest.mock import patch

import pytest

from rvp.context import Context
from rvp.engines.revanced import _build_revanced_cli_cmd


def test_build_revanced_cli_basic_jar_fallback(mock_context: Context) -> None:
  """Test JAR-based command generation (default fallback)."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  # Mock shutil.which to return None (simulate binary not found)
  with patch("rvp.utils.shutil.which", return_value=None):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  # Check that it falls back to java -jar
  assert cmd[0] == "java"
  assert cmd[1] == "-jar"
  assert cmd[2] == "revanced-cli.jar"  # Default
  assert cmd[3] == "patch"

  # Check input/output args
  assert "-o" in cmd
  assert str(output_apk) in cmd
  assert str(input_apk) in cmd


def test_build_revanced_cli_binary_found(mock_context: Context) -> None:
  """Test binary-based command generation."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  # Mock shutil.which to return a path
  with patch("rvp.utils.shutil.which", return_value="/usr/bin/revanced-cli"):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  # Check that it uses the binary
  assert cmd[0] == "revanced-cli"
  assert cmd[1] == "patch"
  assert "java" not in cmd


def test_build_revanced_cli_custom_jar_path(mock_context: Context) -> None:
  """Test configuring custom JAR path."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  mock_context.options["tools"] = {"revanced_cli": "/custom/path/cli.jar"}

  with patch("rvp.utils.shutil.which", return_value=None):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  assert cmd[2] == "/custom/path/cli.jar"


@pytest.mark.parametrize(
  ("options", "expected_in_cmd", "expected_not_in_cmd"),
  [
    # Empty options
    ({}, [], ["-p", "-e", "--exclusive", "--keystore"]),
    # Patches (string only)
    (
      {"revanced_patches": ["PatchOne", "PatchTwo"]},
      ["-p", "patches/revanced/PatchOne.rvp", "patches/revanced/PatchTwo.rvp"],
      ["-O", "-e", "--exclusive", "--keystore"],
    ),
    # Patches (dict only, with options including bools and strings)
    (
      {
        "revanced_patches": [
          {"name": "PatchOne", "options": {"opt1": "val1", "opt2": True}},
        ]
      },
      ["-p", "patches/revanced/PatchOne.rvp", "-Oopt1=val1", "-Oopt2"],
      ["-e", "--exclusive", "--keystore"],
    ),
    # Patches (mixed string and dict)
    (
      {
        "revanced_patches": [
          "PatchOne",
          {"name": "PatchTwo", "options": {"opt1": "val1"}},
        ]
      },
      [
        "-p",
        "patches/revanced/PatchOne.rvp",
        "patches/revanced/PatchTwo.rvp",
        "-Oopt1=val1",
      ],
      ["-e", "--exclusive", "--keystore"],
    ),
    # Patches (dict with False option, should be omitted)
    (
      {
        "revanced_patches": [
          {"name": "PatchOne", "options": {"opt1": False, "opt2": True}},
        ]
      },
      ["-p", "patches/revanced/PatchOne.rvp", "-Oopt2"],
      ["-Oopt1=False", "-Oopt1"],
    ),
    # Patches (dict with no options)
    (
      {
        "revanced_patches": [
          {"name": "PatchOne"},
        ]
      },
      ["-p", "patches/revanced/PatchOne.rvp"],
      ["-O", "-e", "--exclusive", "--keystore"],
    ),
    # Excludes
    (
      {"revanced_exclude_patches": ["BadPatch", "SlowPatch"]},
      ["-e", "BadPatch", "SlowPatch"],
      ["-p", "--exclusive", "--keystore"],
    ),
    # Exclusive
    (
      {"revanced_exclusive": True},
      ["--exclusive"],
      ["-p", "-e", "--keystore"],
    ),
    # Keystore (with entry_password)
    (
      {
        "revanced_keystore": {
          "path": "/path/to/keystore.jks",
          "alias": "myalias",
          "password": "mypassword",
          "entry_password": "myentrypassword",
        }
      },
      [
        "--keystore",
        "/path/to/keystore.jks",
        "--keystore-entry-alias",
        "myalias",
        "--keystore-password",
        "mypassword",
        "--keystore-entry-password",
        "myentrypassword",
      ],
      ["-p", "-e", "--exclusive"],
    ),
    # Keystore (fallback to password for entry_password)
    (
      {
        "revanced_keystore": {
          "path": "/path/to/keystore.jks",
          "alias": "myalias",
          "password": "mypassword",
        }
      },
      [
        "--keystore",
        "/path/to/keystore.jks",
        "--keystore-entry-alias",
        "myalias",
        "--keystore-password",
        "mypassword",
        "--keystore-entry-password",
        "mypassword",
      ],
      ["-p", "-e", "--exclusive"],
    ),
    # Keystore (with empty dict - edge case, though keystore_opts is truthy but dict might miss keys,
    # the code assumes keys are present so we'll just test the standard case as defined)
    # Complex combination
    (
      {
        "revanced_patches": ["PatchOne"],
        "revanced_exclude_patches": ["BadPatch"],
        "revanced_exclusive": True,
      },
      ["-p", "patches/revanced/PatchOne.rvp", "-e", "BadPatch", "--exclusive"],
      ["--keystore"],
    ),
  ],
  ids=[
    "empty_options",
    "patches_string_only",
    "patches_dict_only",
    "patches_mixed",
    "patches_false_option",
    "patches_no_options",
    "excludes",
    "exclusive",
    "keystore_full",
    "keystore_fallback_entry_pwd",
    "complex_combination",
  ],
)
def test_build_revanced_cli_cmd_parameterized(
  mock_context: Context,
  options: dict[str, Any],
  expected_in_cmd: list[str],
  expected_not_in_cmd: list[str],
) -> None:
  """Test various option combinations for _build_revanced_cli_cmd."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  # Update mock_context options with test options
  mock_context.options.update(options)

  with patch("rvp.utils.shutil.which", return_value="/bin/revanced-cli"):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  # Check that expected arguments are in the command
  for expected in expected_in_cmd:
    assert expected in cmd, f"Expected '{expected}' in command: {cmd}"

  # Check that unexpected arguments are NOT in the command
  for not_expected in expected_not_in_cmd:
    assert not_expected not in cmd, f"Did not expect '{not_expected}' in command: {cmd}"

  # Specific count checks if necessary
  if "-e" in expected_in_cmd:
    exclude_indices = [i for i, x in enumerate(cmd) if x == "-e"]
    assert len(exclude_indices) == len(options.get("revanced_exclude_patches", [])), (
      "Mismatched count of '-e' flags"
    )
