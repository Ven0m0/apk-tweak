from __future__ import annotations
import argparse
from pathlib import Path
import sys

from .core import run_pipeline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="rvp",
        description="ReVanced / LSPatch / Magisk / DTL-X pipeline",
    )
    p.add_argument("apk", help="Input APK path")
    p.add_argument(
        "-o", "--out",
        default="out",
        help="Output directory (default: out)",
    )
    p.add_argument(
        "-e", "--engine",
        action="append",
        default=[],
        help="Engine to run (revanced, magisk, lspatch, dtlx). Can be given multiple times.",
    )
    p.add_argument(
        "--dtlx-analyze",
        action="store_true",
        help="Enable DTL-X analysis in dtlx engine.",
    )
    p.add_argument(
        "--dtlx-optimize",
        action="store_true",
        help="Enable DTL-X optimization in dtlx engine.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    apk = Path(args.apk)
    if not apk.is_file():
        print(f"Error: APK not found: {apk}", file=sys.stderr)
        return 1

    out_dir = Path(args.out)

    engines = args.engine or ["revanced"]  # default flow

    options = {
        "dtlx_analyze": args.dtlx_analyze,
        "dtlx_optimize": args.dtlx_optimize,
    }

    ctx = run_pipeline(
        input_apk=apk,
        output_dir=out_dir,
        engines=engines,
        options=options,
    )

    print(f"Done. Final APK: {ctx.current_apk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
