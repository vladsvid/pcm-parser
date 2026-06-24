"""Parse every PCM CSV in data/ and combine into a single long-format CSV."""
import csv
import sys
from pathlib import Path

from pcm_parser import MissingFooterError, MissingMetadataError, parse

DATA_DIR = Path("data")
OUTPUT = DATA_DIR / "all_parsed.csv"


def main() -> None:
    files = sorted(
        f for f in DATA_DIR.glob("*.[Cc][Ss][Vv]")
        if not f.stem.endswith("_parsed") and f.stem != "all_parsed"
    )

    if not files:
        sys.exit(f"No CSV files found in {DATA_DIR}/")

    all_records: list[dict[str, str]] = []
    fieldnames: list[str] = []
    seen_fields: set[str] = set()

    for path in files:
        try:
            records = parse(path).records()
        except (MissingMetadataError, MissingFooterError) as exc:
            print(f"WARNING: skipping {path.name} — {exc}", file=sys.stderr)
            continue

        for rec in records:
            rec["SOURCE_FILE"] = path.name

        for key in (records[0] if records else {}).keys():
            if key not in seen_fields:
                fieldnames.append(key)
                seen_fields.add(key)

        all_records.extend(records)
        print(f"  {path.name}: {len(records):,} rows")

    if not all_records:
        sys.exit("No records parsed.")

    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\nOutput: {OUTPUT}  ({len(all_records):,} total rows)")


if __name__ == "__main__":
    main()
