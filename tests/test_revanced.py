from unittest.mock import patch

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


def test_build_revanced_cli_patches(mock_context: Context) -> None:
  """Test patch arguments (string and dict)."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  mock_context.options["revanced_patches"] = [
    "PatchOne",
    {"name": "PatchTwo", "options": {"option1": "value1", "enable_feature": True}},
  ]

  with patch("rvp.utils.shutil.which", return_value="/bin/revanced-cli"):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  # Verify patches
  assert "-p" in cmd
  assert "patches/revanced/PatchOne.rvp" in cmd
  assert "patches/revanced/PatchTwo.rvp" in cmd

  # Verify options
  assert "-Ooption1=value1" in cmd
  assert "-Oenable_feature" in cmd


def test_build_revanced_cli_excludes_and_exclusive(mock_context: Context) -> None:
  """Test exclude patches and exclusive mode."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  mock_context.options["revanced_exclude_patches"] = ["BadPatch", "SlowPatch"]
  mock_context.options["revanced_exclusive"] = True

  with patch("rvp.utils.shutil.which", return_value="/bin/revanced-cli"):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  assert "-e" in cmd
  # We can check specific occurrences if we want, but verifying they are in the list is good start.
  # Since cmd is a list, we can iterate or use indices.

  exclude_indices = [i for i, x in enumerate(cmd) if x == "-e"]
  assert len(exclude_indices) == 2
  assert "BadPatch" in cmd
  assert "SlowPatch" in cmd
  assert "--exclusive" in cmd


def test_build_revanced_cli_keystore(mock_context: Context) -> None:
  """Test keystore arguments."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  mock_context.options["revanced_keystore"] = {
    "path": "/path/to/keystore.jks",
    "alias": "myalias",
    "password": "mypassword",
  }

  with patch("rvp.utils.shutil.which", return_value="/bin/revanced-cli"):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  assert "--keystore" in cmd
  assert "/path/to/keystore.jks" in cmd
  assert "--keystore-entry-alias" in cmd
  assert "myalias" in cmd
  assert "--keystore-password" in cmd
  assert "mypassword" in cmd
  assert "--keystore-entry-password" in cmd
  # Default entry password is same as password
  assert cmd[cmd.index("--keystore-entry-password") + 1] == "mypassword"


def test_build_revanced_cli_custom_jar_path(mock_context: Context) -> None:
  """Test configuring custom JAR path."""
  input_apk = mock_context.input_apk
  output_apk = mock_context.output_dir / "output.apk"

  mock_context.options["tools"] = {"revanced_cli": "/custom/path/cli.jar"}

  with patch("rvp.utils.shutil.which", return_value=None):
    cmd = _build_revanced_cli_cmd(mock_context, input_apk, output_apk)

  assert cmd[2] == "/custom/path/cli.jar"
