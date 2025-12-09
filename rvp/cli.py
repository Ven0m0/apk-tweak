"""Command-line interface for RVP pipeline."""

from __future__ import annotations

import argparse
import dataclasses
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
    # Convert dataclass to dict and filter out input/output/engines
    all_fields = dataclasses.asdict(cfg)
    excluded = {"input_apk", "output_dir", "engines"}
    options = {k: v for k, v in all_fields.items() if k not in excluded}

    # Reorganize rkpairip options into nested dict
    rkpairip_keys = {
        "rkpairip_apktool_mode": "apktool_mode",
        "rkpairip_merge_skip": "merge_skip",
        "rkpairip_dex_repair": "dex_repair",
        "rkpairip_corex_hook": "corex_hook",
        "rkpairip_anti_split": "anti_split",
    }
    options["rkpairip"] = {
        new_key: options.pop(old_key)
        for old_key, new_key in rkpairip_keys.items()
    }

    # Reorganize tools options into nested dict
    options["tools"] = {
        "revanced_cli": options.pop("revanced_cli_path"),
        "patches": options.pop("revanced_patches_path"),
        "revanced_integrations": options.pop("revanced_integrations_path"),
    }

    return options


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
    # Map command-line flags to option keys
    flag_mapping = {
        "dtlx_analyze": ("dtlx_analyze", None),
        "dtlx_optimize": ("dtlx_optimize", None),
        "patch_ads": ("revanced_patch_ads", None),
    }

    # Apply simple flag overrides
    for arg_name, (opt_key, _) in flag_mapping.items():
        if getattr(args, arg_name, False):
            options[opt_key] = True

    # RKPairip flag overrides (nested dict)
    rkpairip_flags = {
        "rkpairip_apktool": "apktool_mode",
        "rkpairip_merge_skip": "merge_skip",
        "rkpairip_dex_repair": "dex_repair",
        "rkpairip_corex": "corex_hook",
        "rkpairip_anti_split": "anti_split",
    }

    options.setdefault("rkpairip", {})
    for arg_name, opt_key in rkpairip_flags.items():
        if getattr(args, arg_name, False):
            options["rkpairip"][opt_key] = True

    # Discord patcher overrides
    if args.discord_keystore:
        options["discord_keystore"] = args.discord_keystore
    if args.discord_keystore_pass:
        options["discord_keystore_pass"] = args.discord_keystore_pass
    if args.discord_version:
        options["discord_version"] = args.discord_version
    if args.discord_patches:
        options["discord_patches"] = args.discord_patches

    # Luniume overrides
    if args.luniume_method:
        options["luniume_method"] = args.luniume_method
    if args.luniume_patches:
        options["luniume_patches"] = args.luniume_patches
    if args.luniume_modules:
        options["luniume_modules"] = args.luniume_modules
    if args.luniume_exclusive:
        options["luniume_exclusive"] = True

    # WhatsApp patcher overrides
    if hasattr(args, "whatsapp_ab_tests"):
        options["whatsapp_ab_tests"] = args.whatsapp_ab_tests
    if args.whatsapp_timeout:
        options["whatsapp_timeout"] = args.whatsapp_timeout


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
        "--patch-ads",
        action="store_true",
        help="Enable regex-based ad patching",
    )

    # RKPairip options
    p.add_argument(
        "--rkpairip-apktool",
        action="store_true",
        help="RKPairip: Use ApkTool mode",
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

    # Discord patcher options
    p.add_argument(
        "--discord-keystore",
        help="Discord: Path to custom signing keystore",
    )
    p.add_argument(
        "--discord-keystore-pass",
        help="Discord: Keystore password (default: android)",
    )
    p.add_argument(
        "--discord-version",
        help="Discord: Target Discord version (default: auto)",
    )
    p.add_argument(
        "--discord-patches",
        nargs="+",
        help="Discord: Custom patches to apply",
    )

    # Luniume options
    p.add_argument(
        "--luniume-method",
        choices=["revanced", "lspatch"],
        help="Luniume: Patching method (revanced or lspatch)",
    )
    p.add_argument(
        "--luniume-patches",
        nargs="+",
        help="Luniume: Patches to apply (for ReVanced)",
    )
    p.add_argument(
        "--luniume-modules",
        nargs="+",
        help="Luniume: LSPatch modules to embed",
    )
    p.add_argument(
        "--luniume-exclusive",
        action="store_true",
        help="Luniume: Enable exclusive patching mode (ReVanced)",
    )

    # WhatsApp patcher options
    p.add_argument(
        "--whatsapp-ab-tests",
        action="store_true",
        default=True,
        help="WhatsApp: Enable A/B testing features (default: True)",
    )
    p.add_argument(
        "--whatsapp-timeout",
        type=int,
        help="WhatsApp: Patching timeout in seconds (default: 1200)",
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
