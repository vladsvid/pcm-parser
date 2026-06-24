from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_SKIP_PREFIXES = frozenset({"<MAX>", "<MIN>", "<AVG>", "<STD>"})
_SPEC_HIGH_PREFIX = "<SPEC HIGH>"
_SPEC_LOW_PREFIX = "<SPEC LOW>"

_META1_REQUIRED = frozenset({"TYPE NO", "PCM SPEC", "LOT ID", "DATE"})
_META2_REQUIRED = frozenset({"ITEM", "TOTAL", "PASS", "TRANSFER"})


class MissingMetadataError(ValueError):
    pass


class MissingFooterError(ValueError):
    pass


def _parse_metadata_line(line: str) -> dict[str, str]:
    result = {}
    for field in line.strip().split(","):
        if ":" in field:
            key, _, value = field.partition(":")
            result[key.strip()] = value.strip()
    return result


def _col_name(key: str) -> str:
    return key.strip().replace(" ", "_").upper()


@dataclass
class PCMData:
    """Parsed contents of a single PCM CSV file."""

    meta: dict[str, str]
    test_names: list[str]
    spec_high: dict[str, str]
    spec_low: dict[str, str]
    data_rows: list[list[str]]

    def records(self) -> list[dict[str, str]]:
        """Return long-format records — one dict per (die site, test parameter)."""
        meta_cols = {_col_name(k): v for k, v in self.meta.items()}
        rows: list[dict[str, str]] = []
        for row in self.data_rows:
            lot, wf, site = row[0], row[1], row[2]
            for i, test in enumerate(self.test_names):
                result = row[3 + i] if 3 + i < len(row) else ""
                rows.append({
                    "LOT": lot,
                    "WF#": wf,
                    "S#": site,
                    "TEST_NAME": test,
                    "TEST_RESULTS": result,
                    "SPEC_HIGH": self.spec_high.get(test, ""),
                    "SPEC_LOW": self.spec_low.get(test, ""),
                    **meta_cols,
                })
        return rows

    def write_csv(self, output_path: Path | str) -> int:
        """Write long-format CSV to *output_path*. Returns number of data rows written."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        recs = self.records()
        if not recs:
            return 0
        with output_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            writer.writeheader()
            writer.writerows(recs)
        return len(recs)


def parse(input_path: Path | str) -> PCMData:
    """Parse a PCM CSV file and return a :class:`PCMData` object."""
    input_path = Path(input_path)
    with input_path.open(newline="", encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    if len(lines) < 3:
        raise MissingMetadataError(f"{input_path} has fewer than 3 lines")

    meta1 = _parse_metadata_line(lines[0])
    meta2 = _parse_metadata_line(lines[1])

    missing = (_META1_REQUIRED - meta1.keys()) | (_META2_REQUIRED - meta2.keys())
    if missing:
        raise MissingMetadataError(
            f"Required metadata fields not found: {', '.join(sorted(missing))}"
        )

    test_names: list[str] = next(csv.reader([lines[2]]))[3:]

    data_rows: list[list[str]] = []
    spec_high_raw: list[str] = []
    spec_low_raw: list[str] = []

    for row in csv.reader(lines[3:]):
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first in _SKIP_PREFIXES:
            continue
        if first == _SPEC_HIGH_PREFIX:
            spec_high_raw = row[3:]
        elif first == _SPEC_LOW_PREFIX:
            spec_low_raw = row[3:]
        else:
            data_rows.append(row)

    if not spec_high_raw:
        raise MissingFooterError("No <SPEC HIGH> row found in file")
    if not spec_low_raw:
        raise MissingFooterError("No <SPEC LOW> row found in file")

    n = len(test_names)
    spec_high = dict(zip(test_names, spec_high_raw + [""] * (n - len(spec_high_raw))))
    spec_low = dict(zip(test_names, spec_low_raw + [""] * (n - len(spec_low_raw))))

    return PCMData(
        meta={**meta1, **meta2},
        test_names=test_names,
        spec_high=spec_high,
        spec_low=spec_low,
        data_rows=data_rows,
    )
