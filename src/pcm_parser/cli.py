from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import MissingFooterError, MissingMetadataError, parse

_DEFAULT_INPUT = "UMCFAB8C_IME_PCM_0310_NPO-G1-REVC_DP8WJ.1_X.CSV"


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse PCM CSV into long format.")
    ap.add_argument(
        "input",
        nargs="?",
        default=_DEFAULT_INPUT,
        help="Input CSV file (default: %(default)s)",
    )
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: file not found: {input_path}")

    try:
        data = parse(input_path)
    except (MissingMetadataError, MissingFooterError) as exc:
        sys.exit(f"Error: {exc}")

    print("=== Metadata ===")
    for k, v in data.meta.items():
        print(f"  {k}: {v}")
    print(f"  Tests found: {len(data.test_names)}")
    print(f"  Data rows:   {len(data.data_rows)}")

    output_path = Path("data") / (input_path.stem + "_parsed.csv")
    row_count = data.write_csv(output_path)
    print(f"\nOutput: {output_path}  ({row_count} rows)")
