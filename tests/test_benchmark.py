"""Benchmark: token reali con tiktoken, nessun divisore fisso."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "conformance"))

import benchmark  # noqa: E402


def test_count_tokens_uses_real_tokenizer():
    assert benchmark.count_tokens("hello world") == 2


def test_no_fixed_chars_per_token_ratios():
    assert not hasattr(benchmark, "CHARS_PER_TOKEN_NL")
    assert not hasattr(benchmark, "CHARS_PER_TOKEN_H2C")


def test_count_tokens_fails_clearly_without_tiktoken(monkeypatch):
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    monkeypatch.setattr(benchmark, "_ENCODER", None)
    with pytest.raises(RuntimeError, match="pip install tiktoken"):
        benchmark.count_tokens("x")


def test_measure_fixtures_reports_real_delta():
    rows = benchmark.measure_fixtures()
    assert [r["name"] for r in rows] == [
        "Hello World", "Calculator", "Clean Arch", "RAG Pipe",
    ]
    for r in rows:
        assert r["nl_tokens"] > 0 and r["h2c_tokens"] > 0
        expected = round((r["h2c_tokens"] - r["nl_tokens"]) / r["nl_tokens"] * 100)
        assert r["delta_pct"] == expected


def test_render_fixtures_markdown_has_command_and_rows():
    md = benchmark.render_fixtures_markdown(benchmark.measure_fixtures())
    assert "python3 conformance/benchmark.py fixtures" in md
    assert "o200k_base" in md
    assert md.count("\n| ") >= 5  # header + 4 righe
    assert "Stress" not in md  # scenario 5 non confrontabile
