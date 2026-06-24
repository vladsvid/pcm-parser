import csv

import pytest

from pcm_parser import MissingFooterError, MissingMetadataError, PCMData, parse


# ---------------------------------------------------------------------------
# parse() — happy path
# ---------------------------------------------------------------------------


def test_parse_returns_pcmdata(valid_csv):
    assert isinstance(parse(valid_csv), PCMData)


def test_parse_meta_merges_both_header_lines(valid_csv):
    meta = parse(valid_csv).meta
    assert meta["TYPE NO"] == "NPO_G1"   # line 1
    assert meta["ITEM"] == "2"           # line 2


def test_parse_test_names(valid_csv):
    assert parse(valid_csv).test_names == ["TEST_A", "TEST_B"]


def test_parse_spec_high(valid_csv):
    assert parse(valid_csv).spec_high == {"TEST_A": "1.5", "TEST_B": "2.5"}


def test_parse_spec_low(valid_csv):
    assert parse(valid_csv).spec_low == {"TEST_A": "0.5", "TEST_B": "1.5"}


def test_parse_skips_aggregate_rows(valid_csv):
    # MAX/MIN/AVG/STD rows must not appear in data_rows
    assert len(parse(valid_csv).data_rows) == 2


# ---------------------------------------------------------------------------
# parse() — error cases
# ---------------------------------------------------------------------------


def test_parse_too_few_lines_raises(tmp_path):
    p = tmp_path / "short.CSV"
    p.write_text("only one line\n", encoding="utf-8")
    with pytest.raises(MissingMetadataError):
        parse(p)


def test_parse_missing_meta1_field_raises(tmp_path):
    p = tmp_path / "bad_meta1.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,DATE:2026-01-01\n"          # LOT ID missing
        "ITEM:1,TOTAL:1 PCS,PASS:1 PCS,TRANSFER:1 PCS\n"
        "LOT,WF#,S#,TEST_A\n",
        encoding="utf-8",
    )
    with pytest.raises(MissingMetadataError, match="LOT ID"):
        parse(p)


def test_parse_missing_meta2_field_raises(tmp_path):
    p = tmp_path / "bad_meta2.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,LOT ID:L,DATE:2026-01-01\n"
        "ITEM:1,TOTAL:1 PCS,PASS:1 PCS\n"                 # TRANSFER missing
        "LOT,WF#,S#,TEST_A\n",
        encoding="utf-8",
    )
    with pytest.raises(MissingMetadataError, match="TRANSFER"):
        parse(p)


def test_parse_missing_spec_high_raises(tmp_path):
    p = tmp_path / "nohigh.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,LOT ID:L,DATE:2026-01-01\n"
        "ITEM:1,TOTAL:1 PCS,PASS:1 PCS,TRANSFER:1 PCS\n"
        "LOT,WF#,S#,TEST_A\n"
        "L,01,T,1.0\n"
        "<SPEC LOW>,,,0.5\n",
        encoding="utf-8",
    )
    with pytest.raises(MissingFooterError, match="SPEC HIGH"):
        parse(p)


def test_parse_missing_spec_low_raises(tmp_path):
    p = tmp_path / "nolow.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,LOT ID:L,DATE:2026-01-01\n"
        "ITEM:1,TOTAL:1 PCS,PASS:1 PCS,TRANSFER:1 PCS\n"
        "LOT,WF#,S#,TEST_A\n"
        "L,01,T,1.0\n"
        "<SPEC HIGH>,,,1.5\n",
        encoding="utf-8",
    )
    with pytest.raises(MissingFooterError, match="SPEC LOW"):
        parse(p)


# ---------------------------------------------------------------------------
# PCMData.records()
# ---------------------------------------------------------------------------


def test_records_count(valid_csv):
    # 2 die-site rows × 2 tests = 4 records
    assert len(parse(valid_csv).records()) == 4


def test_records_leading_keys(valid_csv):
    keys = list(parse(valid_csv).records()[0].keys())
    assert keys[:7] == ["LOT", "WF#", "S#", "TEST_NAME", "TEST_RESULTS", "SPEC_HIGH", "SPEC_LOW"]


def test_records_values(valid_csv):
    rec = parse(valid_csv).records()[0]
    assert rec["LOT"] == "LOT001"
    assert rec["TEST_NAME"] == "TEST_A"
    assert rec["TEST_RESULTS"] == "1.0"
    assert rec["SPEC_HIGH"] == "1.5"
    assert rec["SPEC_LOW"] == "0.5"


def test_records_meta_columns_normalized(valid_csv):
    rec = parse(valid_csv).records()[0]
    assert "TYPE_NO" in rec     # "TYPE NO" → "TYPE_NO"
    assert "PCM_SPEC" in rec    # "PCM SPEC" → "PCM_SPEC"


def test_records_missing_result_cell_defaults_to_empty(tmp_path):
    p = tmp_path / "short_row.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,LOT ID:L,DATE:2026-01-01\n"
        "ITEM:1,TOTAL:1 PCS,PASS:1 PCS,TRANSFER:1 PCS\n"
        "LOT,WF#,S#,TEST_A,TEST_B\n"
        "L,01,T,1.0\n"          # TEST_B value absent
        "<SPEC HIGH>,,,1.5,2.5\n"
        "<SPEC LOW>,,,0.5,1.5\n",
        encoding="utf-8",
    )
    recs = parse(p).records()
    test_b = next(r for r in recs if r["TEST_NAME"] == "TEST_B")
    assert test_b["TEST_RESULTS"] == ""


# ---------------------------------------------------------------------------
# PCMData.write_csv()
# ---------------------------------------------------------------------------


def test_write_csv_returns_row_count(valid_csv, tmp_path):
    count = parse(valid_csv).write_csv(tmp_path / "out.csv")
    assert count == 4


def test_write_csv_creates_parent_directories(valid_csv, tmp_path):
    out = tmp_path / "nested" / "dir" / "result.csv"
    parse(valid_csv).write_csv(out)
    assert out.exists()


def test_write_csv_header(valid_csv, tmp_path):
    out = tmp_path / "out.csv"
    parse(valid_csv).write_csv(out)
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header[:7] == ["LOT", "WF#", "S#", "TEST_NAME", "TEST_RESULTS", "SPEC_HIGH", "SPEC_LOW"]


def test_write_csv_no_data_rows_returns_zero(tmp_path):
    p = tmp_path / "empty.CSV"
    p.write_text(
        "TYPE NO:X,PCM SPEC:S,LOT ID:L,DATE:2026-01-01\n"
        "ITEM:0,TOTAL:0 PCS,PASS:0 PCS,TRANSFER:0 PCS\n"
        "LOT,WF#,S#,TEST_A\n"
        "<SPEC HIGH>,,,1.5\n"
        "<SPEC LOW>,,,0.5\n",
        encoding="utf-8",
    )
    count = parse(p).write_csv(tmp_path / "out.csv")
    assert count == 0
