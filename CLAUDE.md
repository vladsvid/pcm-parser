# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -e ".[dev]"   # includes pytest
```

## Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test
python -m pytest tests/test_core.py::test_parse_returns_pcmdata -v

# Parse a single file (CLI)
pcm-parser data/some_file.CSV

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
- **Lines 4+**: Data rows plus aggregate rows and mandatory spec-limit rows

Files are opened with `utf-8-sig` encoding to silently strip the BOM that Excel-exported CSVs carry.

### Row classification (parser.py)

Every row after line 3 is classified by its first cell value (`row[0].strip()`):

| First cell | Action |
|---|---|
| empty | skip |
| `<MAX>`, `<MIN>`, `<AVG>`, `<STD>` | skip (aggregate summary rows) |
| `<SPEC HIGH>` | capture cells 4+ as upper spec limits |
| `<SPEC LOW>` | capture cells 4+ as lower spec limits |
| anything else | append to `data_rows` as a die-site measurement |

Both `<SPEC HIGH>` and `<SPEC LOW>` must be present or `MissingFooterError` is raised.

## Output format (long-format CSV)

Each die-site row × each test parameter becomes one output row:

| LOT | WF# | S# | TEST_NAME | TEST_RESULTS | SPEC_HIGH | SPEC_LOW | ...metadata cols... |

Metadata column names are normalized via `_col_name()`: trimmed, spaces→underscores, uppercased. `meta` dict keys keep their original form (e.g. `"LOT ID"`); normalization only happens in `records()` when building output column names.

## Architecture

### Dependency order (no circular imports)

```
utils.py → model.py → parser.py → api.py → __init__.py
```

- **`utils.py`** — constants (`_SKIP_PREFIXES`, required field sets) and pure helpers (`_parse_metadata_line`, `_col_name`)
- **`model.py`** — `PCMData` dataclass with `records()` and `write_csv()`; exception classes
- **`parser.py`** — `_parse()`: file I/O, row classification, builds `PCMData`
- **`api.py`** — `parse()`: public thin wrapper around `_parse()` with full docstring
- **`cli.py`** — argparse entry point; calls `parse()` and `write_csv()`

### Tests

`tests/conftest.py` provides the `valid_csv` fixture — a synthetic PCM file written to `tmp_path`. No real data files are needed to run tests.
