"""Tests for the command-line interface."""

from __future__ import annotations

import argparse

import pytest

from rvp.cli import parse_args


def test_parse_args_empty() -> None:
  """Test parsing empty arguments."""
  args = parse_args([])
  assert isinstance(args, argparse.Namespace)
  assert args.apk is None
  assert args.config is None
  assert args.out is None
  assert args.engine is None
  assert args.verbose is False
  assert args.dtlx_analyze is False
  assert args.dtlx_optimize is False
  assert args.patch_ads is False
  assert args.rkpairip_apktool is False
  assert args.discord_keystore is None


def test_parse_args_basic() -> None:
  """Test parsing basic arguments."""
  args = parse_args(
    ["input.apk", "-c", "config.json", "-o", "output_dir", "-e", "revanced", "-v"]
  )
  assert args.apk == "input.apk"
  assert args.config == "config.json"
  assert args.out == "output_dir"
  assert args.engine == ["revanced"]
  assert args.verbose is True


def test_parse_args_flags() -> None:
  """Test parsing various flags."""
  args = parse_args(
    ["--dtlx-analyze", "--dtlx-optimize", "--patch-ads", "--rkpairip-apktool"]
  )
  assert args.dtlx_analyze is True
  assert args.dtlx_optimize is True
  assert args.patch_ads is True
  assert args.rkpairip_apktool is True


def test_parse_args_discord_options() -> None:
  """Test parsing discord specific options."""
  args = parse_args(
    [
      "--discord-keystore",
      "mykeystore.jks",
      "--discord-keystore-pass",
      "mypass",
      "--discord-version",
      "123.4",
      "--discord-patches",
      "patch1",
      "patch2",
    ]
  )
  assert args.discord_keystore == "mykeystore.jks"
  assert args.discord_keystore_pass == "mypass"
  assert args.discord_version == "123.4"
  assert args.discord_patches == ["patch1", "patch2"]


def test_parse_args_invalid_option(capsys: pytest.CaptureFixture[str]) -> None:
  """Test parsing an invalid option."""
  with pytest.raises(SystemExit):
    parse_args(["--invalid-option"])

  captured = capsys.readouterr()
  assert "unrecognized arguments: --invalid-option" in captured.err
