# pcm-parser

Parse UMC PCM CSV files into long-format CSV or Python records.

## Installation

```bash
pip install -e ".[dev]"
```

## CLI

```bash
# Parse a single file → data/<stem>_parsed.csv
pcm-parser data/some_file.CSV

# Batch-convert all files in data/ → data/all_parsed.csv
python scripts/convert_all.py
```

## Python API

```python
from pcm_parser import parse

data = parse("data/lot.CSV")

print(data.meta["LOT ID"])       # lot-level metadata
print(data.test_names[:3])       # ordered parameter names
print(data.spec_high["VTON10/.18"])  # upper spec limit

records = data.records()         # list[dict] — one entry per (die site × test)
data.write_csv("data/out.csv")   # write long-format CSV, returns row count
```

### Output columns

| LOT | WF# | S# | TEST_NAME | TEST_RESULTS | SPEC_HIGH | SPEC_LOW | *metadata…* |

Metadata column names are normalized: spaces → underscores, uppercased (e.g. `LOT_ID`, `TYPE_NO`).

### Errors

| Exception | When |
|---|---|
| `MissingMetadataError` | Required header field absent or file has < 3 lines |
| `MissingFooterError` | `<SPEC HIGH>` or `<SPEC LOW>` row not found |

Both are importable from `pcm_parser`.

## Input format

UMC PCM files follow a fixed structure:

- **Line 1** — lot metadata: `TYPE NO`, `PCM SPEC`, `LOT ID`, `DATE`
- **Line 2** — wafer metadata: `ITEM`, `TOTAL`, `PASS`, `TRANSFER`
- **Line 3** — column headers: `LOT, WF#, S#, <test_1>, <test_2>, ...`
- **Lines 4+** — die-site rows, aggregate rows (`<MAX>/<MIN>/<AVG>/<STD>`, skipped), and spec rows (`<SPEC HIGH>`, `<SPEC LOW>`)
