#!/usr/bin/env python3
"""Small helper to convert a CSV of recipes into a single text file.

Default behavior mirrors what you were doing manually: it reads
/tmp/recipes.csv and writes a single text file in the repository's
top-level `data/` folder called `kaggle_recipes.txt`.

This script is robust:
- creates output directories if missing
- prefers pandas when available for nicer CSV handling
- falls back to csv module if pandas is missing

Usage (from backend/):
  ./.venv/bin/python convert_recipes.py
  # or
  python3 convert_recipes.py --csv /tmp/recipes.csv --out ../data/kaggle_recipes.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def try_import_pandas():
    try:
        import pandas as pd  # type: ignore

        return pd
    except Exception:
        return None


def convert_with_pandas(csv_path: Path, out_path: Path, encoding: str = "utf-8"):
    pd = try_import_pandas()
    if pd is None:
        raise RuntimeError("pandas is not available")

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    with out_path.open("w", encoding=encoding) as fh:
        for _, row in df.iterrows():
            fh.write(" ".join(row.astype(str).tolist()) + "\n\n")


def convert_with_csv_module(csv_path: Path, out_path: Path, encoding: str = "utf-8"):
    import csv

    # read with csv module, treat each row as list of strings
    with csv_path.open("r", encoding=encoding, newline="") as rf:
        reader = csv.reader(rf)
        with out_path.open("w", encoding=encoding) as wf:
            for row in reader:
                # skip fully-empty rows
                if not any(cell.strip() for cell in row):
                    continue
                wf.write(" ".join(cell for cell in row) + "\n\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert CSV -> single text file (kaggle_recipes.txt)")
    parser.add_argument("--csv", default="/tmp/recipes.csv", help="Path to source CSV file")
    parser.add_argument("--out", default=None, help="Path to output text file (default: ../data/kaggle_recipes.txt)")
    parser.add_argument("--encoding", default="utf-8", help="File encoding")
    parser.add_argument("--force-csv", action="store_true", help="Force using csv module even if pandas is present")

    args = parser.parse_args(argv)

    csv_path = Path(args.csv).expanduser()
    if args.out:
        out_path = Path(args.out).expanduser()
    else:
        # default: repo-root/data/kaggle_recipes.txt
        backend_dir = Path(__file__).resolve().parent
        repo_root = backend_dir.parent
        out_path = repo_root / "data" / "kaggle_recipes.txt"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"Source CSV not found: {csv_path}", file=sys.stderr)
        return 2

    # try pandas first unless forced to csv module
    if not args.force_csv and try_import_pandas() is not None:
        try:
            convert_with_pandas(csv_path, out_path, encoding=args.encoding)
            print(f"Wrote (pandas) -> {out_path}")
            return 0
        except Exception as exc:  # fallback to csv module
            print("pandas conversion failed, falling back to csv module:", exc, file=sys.stderr)

    # fallback
    convert_with_csv_module(csv_path, out_path, encoding=args.encoding)
    print(f"Wrote -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
