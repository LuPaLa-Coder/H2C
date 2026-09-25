"""Guardia: nessun claim di risparmio token non misurato nel repo.

I numeri misurati vivono solo in conformance/Result.md, generato da
conformance/benchmark.py.
"""

import contextlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

CLAIM_RE = re.compile(
    r"\d{2}\s?%\s*(?:of\s+)?(?:token|saving|saved|risparmi|fewer|meno|reduction)"
    r"|\d{2}\s?%\s*di\s+risparmio"
    r"|token[\s_-]?savings?"
    r"|risparmio\s+token"
    r"|\d+\s*(?:→|->)\s*\d+\s*tokens?"
    r"|\(\s*\d{2}\s?%\s*saved\s*\)"
    r"|~\d+\s*token\s+(?:di|of)\s+(?:linguaggio|natural)"
    r"|(?:reduc\w*|riduzion\w*|risparm\w*|sav\w*)[^.\n]{0,40}token[^.\n]{0,40}\d{2}\s?%"
    r"|token[^.\n]{0,40}(?:reduc\w*|riduzion\w*|risparm\w*|sav\w*)[^.\n]{0,40}\d{2}\s?%"
    r"|riduzione\s+token\s*:\s*\d{2}"
    r"|semantic\s+compression|compressione\s+semantica",
    re.IGNORECASE,
)

SCANNED = [
    "README.md", "SPEC.md", "CLAUDE.md", "AGENTS.md", ".windsurfrules",
    "llms-full.txt", "index.html", "pyproject.toml",
    ".cursor/**/*", ".claude-plugin/*", ".cursor-plugin/*", ".github/**/*",
    "skills/**/*.md", "h2c_compress/*.md", "docs/**/*.md", "examples/**/*",
    "h2c/**/*.py",
]


def _files():
    seen = set()
    for pattern in SCANNED:
        for p in ROOT.glob(pattern):
            if p.is_file() and p not in seen:
                seen.add(p)
                yield p


@pytest.mark.parametrize(
    "text",
    [
        "Save 83–96% of tokens",
        "Savings: 42 → 15 tokens (64%)",
        "→ ~15 tokens (64% saved)",
        "~61% di risparmio",
        "96% token savings",
        "Monitorare il risparmio token",
        "H2C reduces token usage by 75-93% compared to natural language.",
        "Riduzione token: 75-93% vs linguaggio naturale.",
        "H2C Semantic Compression Protocol",
        "Compressione semantica per RAG",
    ],
)
def test_claim_regex_catches_old_claims(text):
    assert CLAIM_RE.search(text)


def test_claim_regex_ignores_measured_table_cells():
    assert not CLAIM_RE.search("| Hello World | 131 | 204 | +56% |")


def test_repo_has_no_token_savings_claims():
    offenders = []
    for path in _files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), 1):
            if CLAIM_RE.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()[:100]}")
    assert not offenders, "Claim non misurati:\n" + "\n".join(offenders)


def test_cli_stats_output_has_no_savings_wording(capsys, monkeypatch, hello_world_text, tmp_path):
    from h2c.cli.main import main
    f = tmp_path / "c.h2c"
    f.write_text(hello_world_text)
    monkeypatch.setattr("sys.argv", ["h2c", "stats", str(f)])
    with contextlib.suppress(SystemExit):
        main()
    out = capsys.readouterr().out.lower()
    assert "saving" not in out
