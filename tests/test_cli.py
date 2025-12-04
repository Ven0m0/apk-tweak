"""CLI tests."""

from __future__ import annotations


from rvp.cli import parse_args


def test_parse_args_minimal() -> None:
  """Test minimal argument parsing."""
  args = parse_args(["test.apk"])

  assert args.apk == "test.apk"
  assert not args.verbose


def test_parse_args_full() -> None:
  """Test full argument parsing."""
  args = parse_args(
    [
      "test.apk",
      "-c",
      "config.json",
      "-o",
      "output",
      "-e",
      "revanced",
      "-e",
      "magisk",
      "-v",
      "--dtlx-analyze",
      "--dtlx-optimize",
    ]
  )

  assert args.apk == "test.apk"
  assert args.config == "config.json"
  assert args.out == "output"
  assert args.engine == ["revanced", "magisk"]
  assert args.verbose
  assert args.dtlx_analyze
  assert args.dtlx_optimize
