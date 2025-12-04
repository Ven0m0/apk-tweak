from __future__ import annotations
import argparse
from pathlib import Path
import sys

from .core import run_pipeline
from .config import Config

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="rvp",
        description="ReVanced / LSPatch / Magisk / DTL-X pipeline",
    )
    p.add_argument("apk", nargs="?", help="Input APK path")
    p.add_argument("-c", "--config", help="Path to config JSON file")
    p.add_argument("-o", "--out", help="Output directory")
    p.add_argument("-e", "--engine", action="append", help="Engines to run")
    p.add_argument("--dtlx-analyze", action="store_true", help="Enable DTL-X analysis")
    p.add_argument("--dtlx-optimize", action="store_true", help="Enable DTL-X optimization")
    return p.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # 1. Load defaults or config file
    cfg = Config()
    if args.config:
        try:
            cfg = Config.load_from_file(Path(args.config))
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 1

    # 2. Override with CLI args
    if args.apk: cfg.input_apk = args.apk
    if args.out: cfg.output_dir = args.out
    if args.engine: cfg.engines = args.engine
    if args.dtlx_analyze: cfg.dtlx_analyze = True
    if args.dtlx_optimize: cfg.dtlx_optimize = True

    # 3. Validation
    if not cfg.input_apk:
        print("Error: Input APK is required (via CLI or config)", file=sys.stderr)
        return 1
        
    apk_path = Path(cfg.input_apk).resolve()
    if not apk_path.is_file():
        print(f"Error: APK not found: {apk_path}", file=sys.stderr)
        return 1

    out_dir = Path(cfg.output_dir).resolve()

    # 4. Map Config to Context Options
    options = {
        "dtlx_analyze": cfg.dtlx_analyze,
        "dtlx_optimize": cfg.dtlx_optimize,
        "tools": {
            "revanced_cli": cfg.revanced_cli_path,
            "patches": cfg.revanced_patches_path,
            "integrations": cfg.revanced_integrations_path
        }
    }

    try:
        ctx = run_pipeline(
            input_apk=apk_path,
            output_dir=out_dir,
            engines=cfg.engines,
            options=options,
        )
        print(f"Done. Final APK: {ctx.current_apk}")
        return 0
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
