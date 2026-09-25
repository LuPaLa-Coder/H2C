"""Regression tests for the parser fixes from "Analisi critica H2C v1.4".

Covers the silent data-loss cases (section 2 of the analysis) and the new
diagnostics channel. Deterministic — no hypothesis dependency.
"""

from pathlib import Path

import pytest

from h2c.parser import parse, parse_with_diagnostics
from h2c.transpiler.serializer import serialize

FIXTURES = Path(__file__).parent / "fixtures"


# ── section 2: tokenizer must not steal data out of values ────────────────────

@pytest.mark.parametrize(
    "src, key, expected",
    [
        # keyword prefix outside brackets stays intact
        ("[BUILD:EXEC]\nid:x|desc:ARCHive_old_files\n", "desc", "ARCHive_old_files"),
        ("[BUILD:FIX]\nid:x|desc:FIXture_setup\n", "desc", "FIXture_setup"),
        ("[ARCH:PLAN]\nid:x|fw:py|notes:PLANNED_work\n", "notes", "PLANNED_work"),
        # digit prefix of an identifier is not split into INTEGER + rest
        ("[CTX:PRIMITIVES]\n~goal:4_layers_clean_separation\n",
         "~goal", "4_layers_clean_separation"),
        ("[ARCH:PLAN]\nid:x|fw:py|notes:3d_rendering\n", "notes", "3d_rendering"),
    ],
)
def test_value_not_truncated(src, key, expected):
    msg = parse(src)
    field = next(f for f in msg.blocks[0].fields if f.key == key)
    assert getattr(field.value, "data", None) == expected


def test_plain_integer_value_still_parses_as_integer():
    from h2c.parser.ast import IntegerValue

    msg = parse("[BUILD:FIX]\nid:x|target:a.py|base_rev:1|desc:d|cycle_id:c|retry_n:2\n")
    retry = next(f for f in msg.blocks[0].fields if f.key == "retry_n")
    assert isinstance(retry.value, IntegerValue)
    assert retry.value.data == 2


def test_capabilities_list_keywords_preserved():
    msg = parse(
        "[CTX:NEGOTIATE]\n"
        "version:h2c_v1.4|capabilities:[PRUNE,COMPACT,FREEZE,NEGOTIATE,NACK]\n"
    )
    caps = next(f for f in msg.blocks[0].fields if f.key == "capabilities")
    assert caps.value.data == ["PRUNE", "COMPACT", "FREEZE", "NEGOTIATE", "NACK"]


# ── section 2: no silent discard ─────────────────────────────────────────────

def test_empty_value_keeps_block_and_reports():
    result = parse_with_diagnostics("[BUILD:EXEC]\nid:|target:main.py\n")
    assert len(result.message.blocks) == 1
    keys = [f.key for f in result.message.blocks[0].fields]
    assert keys == ["id", "target"]
    assert any(d.code == "empty-value" and d.level == "error" for d in result.diagnostics)
    assert not result.ok


def test_duplicate_keys_reported():
    result = parse_with_diagnostics("[ARCH:PLAN]\nid:a|id:b|fw:py\n")
    assert any(d.code == "duplicate-key" for d in result.diagnostics)


def test_stray_text_reported_not_dropped_silently():
    result = parse_with_diagnostics("free prose here\n[ARCH:PLAN]\nid:a|fw:py\n")
    assert len(result.message.blocks) == 1
    assert any(d.code == "stray-text" for d in result.diagnostics)


def test_strict_mode_raises_on_error():
    from h2c.parser import H2CParseError

    with pytest.raises(H2CParseError):
        parse("[BUILD:EXEC]\nid:|target:x\n", strict=True)


def test_clean_input_has_no_diagnostics():
    result = parse_with_diagnostics(
        "[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[NACK]\n\n"
        "[STATE:ACK]\nprotocol:h2c_v1.4\n"
    )
    assert result.diagnostics == []
    assert result.ok


# ── property: serialize ∘ parse is idempotent on the official corpus ──────────

@pytest.mark.parametrize(
    "fixture", sorted(FIXTURES.glob("test*.h2c")), ids=lambda p: p.name
)
def test_roundtrip_idempotent(fixture):
    src = fixture.read_text()
    once = parse(src)
    twice = parse(serialize(once))
    assert once.to_json_ast() == twice.to_json_ast()
