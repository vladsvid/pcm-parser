from __future__ import annotations

import csv
from pathlib import Path

from .model import MissingFooterError, MissingMetadataError, PCMData
from .utils import (
    _META1_REQUIRED,
    _META2_REQUIRED,
    _SKIP_PREFIXES,
    _SPEC_HIGH_PREFIX,
    _SPEC_LOW_PREFIX,
    _norm_spec,
    _parse_metadata_line,
    _strip_pcs,
)


def _parse(input_path: Path) -> PCMData:
    with input_path.open(newline="", encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    if len(lines) < 3:
        raise MissingMetadataError(f"{input_path} has fewer than 3 lines")

    meta1 = _parse_metadata_line(lines[0])
    meta2 = _parse_metadata_line(lines[1])
    for key in ("TOTAL", "PASS", "TRANSFER"):
        if key in meta2:
            meta2[key] = _strip_pcs(meta2[key])

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
    spec_high = {k: _norm_spec(v) for k, v in zip(test_names, spec_high_raw + [""] * (n - len(spec_high_raw)))}
    spec_low = {k: _norm_spec(v) for k, v in zip(test_names, spec_low_raw + [""] * (n - len(spec_low_raw)))}

    return PCMData(
        meta={**meta1, **meta2},
        test_names=test_names,
        spec_high=spec_high,
        spec_low=spec_low,
        data_rows=data_rows,
    )
