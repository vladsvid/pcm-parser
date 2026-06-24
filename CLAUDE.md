# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -e .
```

## Running the parser

```bash
# CLI (after install)
pcm-parser data/some_file.CSV

# Legacy script shim
python parser.py data/some_file.CSV

# Batch-convert all files in data/ into one CSV
python scripts/convert_all.py
```

Output is written to `data/<input_stem>_parsed.csv`.

## Programmatic API

```python
from pcm_parser import parse

data = parse("data/file.CSV")

data.meta         # dict[str, str] — all metadata fields merged from header lines 1+2
data.test_names   # list[str] — ordered parameter names
data.spec_high    # dict[str, str] — test_name → upper spec limit
data.spec_low     # dict[str, str] — test_name → lower spec limit
data.data_rows    # list[list[str]] — raw die-site rows [lot, wf, site, val0, val1, ...]

records = data.records()         # list[dict] — long-format, one entry per (site × test)
count   = data.write_csv("out.csv")  # writes CSV, returns row count
```

## Input CSV format

PCM files from UMC fab have a fixed 3-line header before data rows:

- **Line 1**: `key:value` pairs — `TYPE NO`, `PCM SPEC`, `LOT ID`, `DATE`
- **Line 2**: `key:value` pairs — `ITEM`, `TOTAL`, `PASS`, `TRANSFER`
- **Line 3**: Column headers — `LOT, WF#, S#, <test_name_1>, <test_name_2>, ...`
- **Lines 4+**: Data rows plus special aggregate rows prefixed with `<MAX>`, `<MIN>`, `<AVG>`, `<STD>`, `<SPEC HIGH>`, `<SPEC LOW>`

The parser skips `<MAX>/<MIN>/<AVG>/<STD>` rows and extracts `<SPEC HIGH>` and `<SPEC LOW>` as spec limit references.

## Output format (long-format CSV)

Each die-site row × each test parameter becomes one output row:

| LOT | WF# | S# | TEST_NAME | TEST_RESULTS | SPEC_HIGH | SPEC_LOW | ...metadata cols... |

Metadata column names are normalized: trimmed, spaces→underscores, uppercased.

## Package structure

```
src/pcm_parser/
    __init__.py    # exports: parse, PCMData, MissingMetadataError, MissingFooterError
    core.py        # PCMData dataclass + parse() function
    cli.py         # argparse CLI (main entry point)
scripts/
    convert_all.py # batch-converts all files in data/ to one CSV
tests/
    __init__.py
pyproject.toml
parser.py          # shim — imports and delegates to pcm_parser.cli:main
```

All parsing logic lives in `src/pcm_parser/core.py`. The two custom exceptions (`MissingMetadataError`, `MissingFooterError`) signal structural problems with the input file and are part of the public API.
