import argparse
import csv
import sys
from pathlib import Path

SKIP_PREFIXES = {"<MAX>", "<MIN>", "<AVG>", "<STD>"}
SPEC_HIGH_PREFIX = "<SPEC HIGH>"
SPEC_LOW_PREFIX = "<SPEC LOW>"
DEFAULT_INPUT = "UMCFAB8C_IME_PCM_0310_NPO-G1-REVC_DP8WJ.1_X.CSV"

META1_REQUIRED = {"TYPE NO", "PCM SPEC", "LOT ID", "DATE"}
META2_REQUIRED = {"ITEM", "TOTAL", "PASS", "TRANSFER"}


class MissingMetadataError(ValueError):
    pass


class MissingFooterError(ValueError):
    pass


def parse_metadata_line(line: str) -> dict:
    """Parse a comma-separated line of key:value pairs (splits on first colon only)."""
    result = {}
    for field in line.strip().split(","):
        if ":" in field:
            key, _, value = field.partition(":")
            result[key.strip()] = value.strip()
    return result


def parse_file(input_path: Path) -> tuple[dict, dict, list[str], list, list, list]:
    with input_path.open(newline="", encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    if len(lines) < 3:
        raise MissingMetadataError(f"{input_path} has fewer than 3 lines")

    meta1 = parse_metadata_line(lines[0])
    meta2 = parse_metadata_line(lines[1])

    missing1 = META1_REQUIRED - meta1.keys()
    missing2 = META2_REQUIRED - meta2.keys()
    if missing1 or missing2:
        missing = missing1 | missing2
        raise MissingMetadataError(f"Required metadata fields not found: {', '.join(sorted(missing))}")

    header = next(csv.reader([lines[2]]))
    test_names = header[3:]

    data_rows = []
    spec_high = []
    spec_low = []

    reader = csv.reader(lines[3:])
    for row in reader:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first in SKIP_PREFIXES:
            continue
        if first == SPEC_HIGH_PREFIX:
            spec_high = row[3:]
        elif first == SPEC_LOW_PREFIX:
            spec_low = row[3:]
        else:
            data_rows.append(row)

    if not spec_high:
        raise MissingFooterError("No <SPEC HIGH> row found in file")
    if not spec_low:
        raise MissingFooterError("No <SPEC LOW> row found in file")

    return meta1, meta2, test_names, data_rows, spec_high, spec_low


def _col_name(key: str) -> str:
    return key.strip().replace(" ", "_").upper()


def write_output(output_path: Path, meta1: dict, meta2: dict, test_names: list[str],
                 data_rows: list, spec_high: list, spec_low: list) -> int:
    n_tests = len(test_names)
    sh = spec_high + [""] * (n_tests - len(spec_high))
    sl = spec_low + [""] * (n_tests - len(spec_low))

    meta_cols = {_col_name(k): v for d in (meta1, meta2) for k, v in d.items()}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["LOT", "WF#", "S#", "TEST_NAME", "TEST_RESULTS", "SPEC_HIGH", "SPEC_LOW"]
            + list(meta_cols.keys())
        )
        meta_values = list(meta_cols.values())
        for row in data_rows:
            lot, wf, s = row[0], row[1], row[2]
            for i, test in enumerate(test_names):
                result = row[3 + i] if 3 + i < len(row) else ""
                writer.writerow([lot, wf, s, test, result, sh[i], sl[i]] + meta_values)
                row_count += 1
    return row_count


def main():
    parser = argparse.ArgumentParser(description="Parse PCM CSV into long format.")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT,
                        help="Input CSV file (default: %(default)s)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: file not found: {input_path}")

    try:

        meta1, meta2, test_names, data_rows, spec_high, spec_low = parse_file(input_path)
    except (MissingMetadataError, MissingFooterError) as exc:
        sys.exit(f"Error: {exc}")

    print("=== Metadata ===")
    for k, v in meta1.items():
        print(f"  {k}: {v}")
    for k, v in meta2.items():
        print(f"  {k}: {v}")
    print(f"  Tests found: {len(test_names)}")
    print(f"  Data rows:   {len(data_rows)}")

    output_path = Path("data") / (input_path.stem + "_parsed.csv")
    row_count = write_output(output_path, meta1, meta2, test_names, data_rows, spec_high, spec_low)
    print(f"\nOutput: {output_path}  ({row_count} rows)")


if __name__ == "__main__":
    main()
