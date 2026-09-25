"""Gli esempi ufficiali devono passare parser e validator del repo."""

from pathlib import Path

import pytest

from h2c.parser import parse_with_diagnostics
from h2c.validator.validator import Validator

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
EXAMPLES = sorted(EXAMPLES_DIR.glob("*.h2c"))


def test_every_markdown_example_has_a_chain_file():
    assert len(EXAMPLES) == len(list(EXAMPLES_DIR.glob("*.md"))) == 3


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_parses_without_errors(path):
    result = parse_with_diagnostics(path.read_text())
    assert result.ok, [str(d) for d in result.diagnostics]
    assert all(d.level != "warning" for d in result.diagnostics), \
        "un file .h2c non deve contenere testo fuori dai blocchi"


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_passes_validator(path):
    result = Validator().validate(parse_with_diagnostics(path.read_text()).message)
    assert result.valid, [e.message for e in result.errors]
