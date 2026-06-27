from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .utils import _col_name


class MissingMetadataError(ValueError):
    """Raised when a required metadata field is absent from the file header.

    PCM files must contain the following fields:
    - Line 1: ``TYPE NO``, ``PCM SPEC``, ``LOT ID``, ``DATE``
    - Line 2: ``ITEM``, ``TOTAL``, ``PASS``, ``TRANSFER``
    """
    pass


class MissingFooterError(ValueError):
    """Raised when the ``<SPEC HIGH>`` or ``<SPEC LOW>`` footer row is not found.

    Both rows must appear after the data rows at the bottom of the file.
    """
    pass


@dataclass
class PCMData:
    """Parsed contents of a single PCM CSV file.

    Attributes:
        meta: Combined metadata from header lines 1 and 2, keyed by the
            original field names (e.g. ``"LOT ID"``, ``"TYPE NO"``).
        test_names: Ordered list of test parameter names as they appear in
            the column header (line 3), e.g. ``["VTON10/.18", "IDSN10/.18"]``.
        spec_high: Upper specification limits mapped by test name.
            Tests with no limit value in the file are mapped to ``None``.
        spec_low: Lower specification limits mapped by test name.
            Tests with no limit value in the file are mapped to ``None``.
        data_rows: Raw die-site rows from the file. Each row is a list of
            strings: ``[lot, wafer, site, val_0, val_1, ...]``.
            Aggregate rows (``<MAX>``, ``<MIN>``, ``<AVG>``, ``<STD>``) are
            excluded.
    """

    meta: dict[str, str]
    test_names: list[str]
    spec_high: dict[str, str | None]
    spec_low: dict[str, str | None]
    data_rows: list[list[str]]

    def records(self) -> list[dict[str, str]]:
        """Return all measurements in long format — one dict per (die site, test).

        The wide table (one row per die site, one column per test) is pivoted
        so that each test measurement becomes its own row.  Metadata fields are
        appended as extra columns with normalised names (spaces replaced by
        underscores, uppercased).

        Returns:
            List of dicts with the following keys (in order):

            ``LOT``, ``WF#``, ``S#`` — lot ID, wafer number, and site
            identifier from the original row.

            ``TEST_NAME`` — name of the test parameter.

            ``TEST_RESULTS`` — measured value as a string (``""`` when the
            cell is missing from the source row).

            ``SPEC_HIGH``, ``SPEC_LOW`` — specification limits for this test
            (``""`` when not specified in the file).

            *metadata columns* — one column per field from ``self.meta``, e.g.
            ``TYPE_NO``, ``LOT_ID``, ``DATE``, ``ITEM``, etc.

        Example::

            [
                {
                    "LOT": "DP8WJ.1", "WF#": "01", "S#": "T",
                    "TEST_NAME": "VTON10/.18", "TEST_RESULTS": "0.5187",
                    "SPEC_HIGH": "0.58", "SPEC_LOW": "0.44",
                    "TYPE_NO": "NPO_G1_REVC", "LOT_ID": "DP8WJ.1", ...
                },
                ...
            ]
        """
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
        """Write long-format records to a CSV file.

        Calls :meth:`records` and writes the result as a UTF-8 CSV.  Parent
        directories are created automatically if they do not exist.  When there
        are no data rows the file is not created and 0 is returned.

        Args:
            output_path: Destination file path (str or :class:`pathlib.Path`).

        Returns:
            Number of data rows written (excluding the header).

        Example::

            count = data.write_csv("data/lot_parsed.csv")
            print(f"Wrote {count} rows")
        """
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
