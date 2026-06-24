"""
Public API for pcm-parser.

Parse UMC PCM CSV files and convert them to long-format records.

Example
-------
    from pcm_parser import parse

    data = parse("data/lot.CSV")

    # Inspect metadata
    print(data.meta["LOT ID"])      # e.g. "DP8WJ.1"
    print(data.test_names[:3])      # e.g. ["VTON10/.18", "IDSN10/.18", ...]

    # Long-format records ready for a DataFrame or CSV export
    records = data.records()
    data.write_csv("data/lot_parsed.csv")
"""

from __future__ import annotations

from pathlib import Path

from .model import MissingFooterError, MissingMetadataError, PCMData
from .parser import _parse

__all__ = ["parse", "PCMData", "MissingMetadataError", "MissingFooterError"]


def parse(input_path: Path | str) -> PCMData:
    """Parse a UMC PCM CSV file and return a :class:`PCMData` object.

    The file is expected to follow the UMC PCM format:

    - **Line 1**: comma-separated ``key:value`` pairs with lot-level metadata
      (``TYPE NO``, ``PCM SPEC``, ``LOT ID``, ``DATE``).
    - **Line 2**: comma-separated ``key:value`` pairs with wafer-level metadata
      (``ITEM``, ``TOTAL``, ``PASS``, ``TRANSFER``).
    - **Line 3**: column header — ``LOT``, ``WF#``, ``S#``, then one column
      per test parameter.
    - **Lines 4+**: die-site data rows, followed by optional aggregate rows
      (``<MAX>``, ``<MIN>``, ``<AVG>``, ``<STD>``) and mandatory spec-limit
      rows (``<SPEC HIGH>``, ``<SPEC LOW>``).

    Aggregate rows are silently skipped.  The spec-limit rows are extracted
    and stored in :attr:`PCMData.spec_high` and :attr:`PCMData.spec_low`.

    Args:
        input_path: Path to the PCM CSV file (str or :class:`pathlib.Path`).
            Files with a UTF-8 BOM are handled transparently.

    Returns:
        A :class:`PCMData` instance containing the parsed metadata, test
        names, spec limits, and raw data rows.

    Raises:
        MissingMetadataError: If the file has fewer than 3 lines, or if any
            required metadata field is absent from lines 1 or 2.
        MissingFooterError: If the ``<SPEC HIGH>`` or ``<SPEC LOW>`` row is
            not found anywhere in the file.

    Example::

        from pcm_parser import parse

        data = parse("data/UMCFAB8C_IME_PCM_0310_DP8WJ.1_X.CSV")
        print(data.meta["LOT ID"])          # "DP8WJ.1"
        print(len(data.test_names))         # 104
        print(data.spec_high["VTON10/.18"]) # "0.58"

        records = data.records()            # list of dicts, one per (site, test)
        data.write_csv("data/out.csv")      # write long-format CSV
    """
    return _parse(Path(input_path))
