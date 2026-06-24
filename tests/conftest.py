import pytest

VALID_CSV = (
    "TYPE NO:NPO_G1,PCM SPEC:SPEC1,LOT ID:LOT001,DATE:2026-01-01\n"
    "ITEM:2,TOTAL:2 PCS,PASS:2 PCS,TRANSFER:2 PCS\n"
    "LOT,WF#,S#,TEST_A,TEST_B\n"
    "LOT001,01,T,1.0,2.0\n"
    "LOT001,01,B,1.1,2.1\n"
    "<MAX>,,,1.1,2.1\n"
    "<MIN>,,,1.0,2.0\n"
    "<AVG>,,,1.05,2.05\n"
    "<STD>,,,0.05,0.05\n"
    "<SPEC HIGH>,,,1.5,2.5\n"
    "<SPEC LOW>,,,0.5,1.5\n"
)


@pytest.fixture
def valid_csv(tmp_path):
    p = tmp_path / "test.CSV"
    p.write_text(VALID_CSV, encoding="utf-8")
    return p
