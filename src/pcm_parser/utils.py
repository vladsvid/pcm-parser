from __future__ import annotations

_SKIP_PREFIXES = frozenset({"<MAX>", "<MIN>", "<AVG>", "<STD>"})
_SPEC_HIGH_PREFIX = "<SPEC HIGH>"
_SPEC_LOW_PREFIX = "<SPEC LOW>"

_META1_REQUIRED = frozenset({"TYPE NO", "PCM SPEC", "LOT ID", "DATE"})
_META2_REQUIRED = frozenset({"ITEM", "TOTAL", "PASS", "TRANSFER"})


def _parse_metadata_line(line: str) -> dict[str, str]:
    result = {}
    for field in line.strip().split(","):
        if ":" in field:
            key, _, value = field.partition(":")
            result[key.strip()] = value.strip()
    return result


def _col_name(key: str) -> str:
    return key.strip().replace(" ", "_").upper()
