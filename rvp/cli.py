from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

from .core import run_pipeline
from .config import Config

# ... (Keep setup_logging)
def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rvp", description="APK Tweak Pipeline")
    p.add_argument("apk", nargs="?", help="Input APK path")
    p.add_argument("-c", "--config", help="Path to config JSON file")
    p.add_argument("-o", "--out", help="Output directory")
    p.add_argument("-e", "--engine", action="append", help="Engines to run")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("--dtlx-analyze", action="store_true", help="Enable DTL-X analysis")
    p.add_argument("--dtlx-optimize", action="store_true", help="Enable DTL-X optimization")
    return p.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
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
        engines = ["revanced"] # Default fallback

    # Resolve Options
    # Merge cfg options with flag overrides
    options = {}
    
    if cfg:
        options["dtlx_analyze"] = cfg.dtlx_analyze
        options["dtlx_optimize"] = cfg.dtlx_optimize
        # Add other config fields as needed
        
    # Flags override config
    if args.dtlx_analyze:
        options["dtlx_analyze"] = True
    if args.dtlx_optimize:
        options["dtlx_optimize"] = True
        
    # Pass tools config
    if cfg:
        options["tools"] = {
            "revanced_cli": cfg.revanced_cli_path,
            "patches": cfg.revanced_patches_path,
            # ... map others
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
