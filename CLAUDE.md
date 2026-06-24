# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -e ".[dev]"   # includes pytest
```

## Commands

```bash
# Run tests
python -m pytest tests/ -v

# Parse a single file (CLI)
pcm-parser data/some_file.CSV

# Legacy script shim (same behaviour)
python parser.py data/some_file.CSV

# Batch-convert all files in data/ into one CSV
python scripts/convert_all.py
```

Single-file output goes to `data/<input_stem>_parsed.csv`. Batch output goes to `data/all_parsed.csv`.

## Programmatic API

```python
from pcm_parser import parse

data = parse("data/file.CSV")

data.meta         # dict[str, str] — all metadata fields merged from header lines 1+2
data.test_names   # list[str] — ordered parameter names
data.spec_high    # dict[str, str] — test_name → upper spec limit
data.spec_low     # dict[str, str] — test_name → lower spec limit
data.data_rows    # list[list[str]] — raw die-site rows [lot, wf, site, val0, val1, ...]

records = data.records()          # list[dict[str, str]] — long-format, one entry per (site × test)
count   = data.write_csv("out.csv")  # writes CSV, returns row count
```

Errors are signalled by `MissingMetadataError` (bad/incomplete header) and `MissingFooterError` (missing `<SPEC HIGH>` or `<SPEC LOW>` row), both importable from `pcm_parser`.

## Input CSV format

PCM files from UMC fab have a fixed 3-line header before data rows:

- **Line 1**: `key:value` pairs — `TYPE NO`, `PCM SPEC`, `LOT ID`, `DATE`
- **Line 2**: `key:value` pairs — `ITEM`, `TOTAL`, `PASS`, `TRANSFER`
- **Line 3**: Column headers — `LOT, WF#, S#, <test_name_1>, <test_name_2>, ...`
- **Lines 4+**: Data rows plus aggregate rows (`<MAX>`, `<MIN>`, `<AVG>`, `<STD>`) and mandatory spec-limit rows (`<SPEC HIGH>`, `<SPEC LOW>`)

Aggregate rows are silently skipped. Spec-limit rows are extracted into `PCMData.spec_high` / `spec_low`.

## Output format (long-format CSV)

Each die-site row × each test parameter becomes one output row:

| LOT | WF# | S# | TEST_NAME | TEST_RESULTS | SPEC_HIGH | SPEC_LOW | ...metadata cols... |

Metadata column names are normalized: trimmed, spaces→underscores, uppercased.

## Package structure

```
src/pcm_parser/
    __init__.py   # re-exports: parse, PCMData, MissingMetadataError, MissingFooterError
    api.py        # parse() public function — thin wrapper, full docstring
    model.py      # PCMData dataclass (records(), write_csv()) + exception classes
    parser.py     # _parse() implementation — file I/O and row classification
    utils.py      # internal helpers: _parse_metadata_line, _col_name, constants
    cli.py        # argparse CLI entry point
scripts/
    convert_all.py
tests/
    conftest.py   # valid_csv fixture (synthetic PCM content, no real files needed)
    test_core.py  # 20 tests covering parse(), records(), write_csv()
pyproject.toml
parser.py         # root shim → pcm_parser.cli:main
```

### Dependency order (no circular imports)

```
utils.py → model.py → parser.py → api.py → __init__.py
```
