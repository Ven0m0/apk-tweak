"""Command-line interface for RVP pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .core import run_pipeline


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
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("--dtlx-analyze", action="store_true", help="Enable DTL-X analysis")
    p.add_argument("--dtlx-optimize", action="store_true", help="Enable DTL-X optimization")
    p.add_argument("--patch-ads", action="store_true", help="Enable regex-based ad patching")
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
        except Exception as e:
            logger.error(f"Config load failed: {e}")
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
    output_dir = Path(args.out) if args.out else Path(cfg.output_dir if cfg else "out")

    # Resolve Engines: Args > Config > Default
    engines = args.engine
    if not engines and cfg:
        engines = cfg.engines
    if not engines:
        engines = ["revanced"]  # Default fallback

    # Resolve Options
    # Merge cfg options with flag overrides
    options: dict[str, object] = {}

    if cfg:
        options["dtlx_analyze"] = cfg.dtlx_analyze
        options["dtlx_optimize"] = cfg.dtlx_optimize

        # ReVanced options
        options["revanced_patch_bundles"] = cfg.revanced_patch_bundles
        options["revanced_optimize"] = cfg.revanced_optimize
        options["revanced_debloat"] = cfg.revanced_debloat
        options["revanced_minify"] = cfg.revanced_minify
        options["revanced_patch_ads"] = cfg.revanced_patch_ads
        options["revanced_include_patches"] = cfg.revanced_include_patches
        options["revanced_exclude_patches"] = cfg.revanced_exclude_patches

        # Optimization options
        options["debloat_patterns"] = cfg.debloat_patterns
        options["minify_patterns"] = cfg.minify_patterns

        # Tool paths
        options["apktool_path"] = cfg.apktool_path
        options["zipalign_path"] = cfg.zipalign_path

    # Flags override config
    if args.dtlx_analyze:
        options["dtlx_analyze"] = True
    if args.dtlx_optimize:
        options["dtlx_optimize"] = True
    if args.patch_ads:
        options["revanced_patch_ads"] = True

    # Pass tools config
    if cfg:
        options["tools"] = {
            "revanced_cli": cfg.revanced_cli_path,
            "patches": cfg.revanced_patches_path,
            "revanced_integrations": cfg.revanced_integrations_path,
        }

    try:
        run_pipeline(input_apk, output_dir, engines, options)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
