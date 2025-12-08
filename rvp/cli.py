"""Command-line interface for RVP pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from .config import Config
from .core import run_pipeline

# Type alias for options dictionary
# TODO: Replace with TypedDict for better type safety
Options = dict[str, Any]


def _build_config_options(cfg: Config) -> Options:
  """
  Extract options from configuration object.

  Args:
      cfg: Configuration object to extract options from.

  Returns:
      Dictionary of configuration options.
  """
  return {
    "dtlx_analyze": cfg.dtlx_analyze,
    "dtlx_optimize": cfg.dtlx_optimize,
    "revanced_patch_bundles": cfg.revanced_patch_bundles,
    "revanced_optimize": cfg.revanced_optimize,
    "revanced_debloat": cfg.revanced_debloat,
    "revanced_minify": cfg.revanced_minify,
    "revanced_patch_ads": cfg.revanced_patch_ads,
    "revanced_include_patches": cfg.revanced_include_patches,
    "revanced_exclude_patches": cfg.revanced_exclude_patches,
    "debloat_patterns": cfg.debloat_patterns,
    "minify_patterns": cfg.minify_patterns,
    "apktool_path": cfg.apktool_path,
    "zipalign_path": cfg.zipalign_path,
    "rkpairip": {
      "apktool_mode": cfg.rkpairip_apktool_mode,
      "merge_skip": cfg.rkpairip_merge_skip,
      "dex_repair": cfg.rkpairip_dex_repair,
      "corex_hook": cfg.rkpairip_corex_hook,
      "anti_split": cfg.rkpairip_anti_split,
    },
    "tools": {
      "revanced_cli": cfg.revanced_cli_path,
      "patches": cfg.revanced_patches_path,
      "revanced_integrations": cfg.revanced_integrations_path,
    },
  }


def _build_default_options() -> Options:
  """
  Create default options when no configuration file is provided.

  Returns:
      Dictionary with default option values.
  """
  return {
    "rkpairip": {
      "apktool_mode": False,
      "merge_skip": False,
      "dex_repair": False,
      "corex_hook": False,
      "anti_split": False,
    }
  }


def _apply_flag_overrides(options: Options, args: argparse.Namespace) -> None:
  """
  Apply command-line flag overrides to options dictionary.

  Args:
      options: Options dictionary to modify in-place.
      args: Parsed command-line arguments.
  """
  # DTL-X flag overrides
  if args.dtlx_analyze:
    options["dtlx_analyze"] = True
  if args.dtlx_optimize:
    options["dtlx_optimize"] = True
  if args.patch_ads:
    options["revanced_patch_ads"] = True

  # RKPairip flag overrides
  if args.rkpairip_apktool:
    options.setdefault("rkpairip", {})["apktool_mode"] = True
  if args.rkpairip_merge_skip:
    options.setdefault("rkpairip", {})["merge_skip"] = True
  if args.rkpairip_dex_repair:
    options.setdefault("rkpairip", {})["dex_repair"] = True
  if args.rkpairip_corex:
    options.setdefault("rkpairip", {})["corex_hook"] = True
  if args.rkpairip_anti_split:
    options.setdefault("rkpairip", {})["anti_split"] = True


def setup_logging(verbose: bool) -> None:
  """
  Configure logging for the application.

  Args:
      verbose: Enable debug-level logging if True.
  """
  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
  )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  """
  Parse command-line arguments.

  Args:
      argv: Optional argument list (defaults to sys.argv).

  Returns:
      argparse.Namespace: Parsed arguments.
  """
  p = argparse.ArgumentParser(prog="rvp", description="APK Tweak Pipeline")
  p.add_argument("apk", nargs="?", help="Input APK path")
  p.add_argument("-c", "--config", help="Path to config JSON file")
  p.add_argument("-o", "--out", help="Output directory")
  p.add_argument("-e", "--engine", action="append", help="Engines to run")
  p.add_argument(
    "-v", "--verbose", action="store_true", help="Enable debug logging"
  )
  p.add_argument(
    "--dtlx-analyze", action="store_true", help="Enable DTL-X analysis"
  )
  p.add_argument(
    "--dtlx-optimize", action="store_true", help="Enable DTL-X optimization"
  )
  p.add_argument(
    "--patch-ads", action="store_true", help="Enable regex-based ad patching"
  )

  # RKPairip options
  p.add_argument(
    "--rkpairip-apktool", action="store_true", help="RKPairip: Use ApkTool mode"
  )
  p.add_argument(
    "--rkpairip-merge-skip",
    action="store_true",
    help="RKPairip: Enable merge skip mode",
  )
  p.add_argument(
    "--rkpairip-dex-repair",
    action="store_true",
    help="RKPairip: Enable DEX repair",
  )
  p.add_argument(
    "--rkpairip-corex",
    action="store_true",
    help="RKPairip: Enable CoreX hook (Unity/Flutter)",
  )
  p.add_argument(
    "--rkpairip-anti-split",
    action="store_true",
    help="RKPairip: Enable anti-split merge",
  )

  return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  """
  Main entry point for the CLI.

  Args:
      argv: Optional argument list (defaults to sys.argv).

  Returns:
      int: Exit code (0 for success, 1 for failure).
  """
  args = parse_args(argv)
  setup_logging(args.verbose)
  logger = logging.getLogger("rvp.cli")

  # ⚡ Opt: Load config once
  cfg: Config | None = None
  if args.config:
    try:
      cfg = Config.load_from_file(Path(args.config))
    except (FileNotFoundError, OSError) as e:
      logger.error(f"Config file error: {e}")
      return 1
    except ValueError as e:
      logger.error(f"Invalid config format: {e}")
      return 1

  # Resolve Input: Args > Config
  input_apk_str = args.apk or (cfg.input_apk if cfg else None)

  if not input_apk_str:
    logger.error("Input APK is required via argument or config file.")
    return 1

  input_apk = Path(input_apk_str)
  if not input_apk.exists():
    logger.error(f"Input APK not found: {input_apk}")
    return 1

  # Resolve Output
  output_dir = (
    Path(args.out) if args.out else Path(cfg.output_dir if cfg else "out")
  )

  # Resolve Engines: Args > Config > Default
  engines = args.engine
  if not engines and cfg:
    engines = cfg.engines
  if not engines:
    engines = ["revanced"]  # Default fallback

  # Build options from config or defaults
  options = _build_config_options(cfg) if cfg else _build_default_options()

  # Apply command-line flag overrides
  _apply_flag_overrides(options, args)

  try:
    run_pipeline(input_apk, output_dir, engines, options)
  except (OSError, ValueError, RuntimeError) as e:
    logger.error(f"Pipeline failed: {e}")
    if args.verbose:
      import traceback

      traceback.print_exc()
    return 1

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
