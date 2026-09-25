"""CLI command tests.

Tests for h2c command-line interface, including token counting and transpile diagnostics.
"""

import sys
from pathlib import Path

import pytest

from h2c.cli.main import _count_tokens


class TestCountTokens:
    """Tests for the _count_tokens function."""

    def test_count_tokens_hello_world_with_o200k_base(self):
        """_count_tokens should return (2, True) for 'hello world' using o200k_base."""
        tokens, exact = _count_tokens("hello world")
        assert exact is True, "Expected exact=True when tiktoken is available with o200k_base"
        assert tokens == 2, f"Expected 2 tokens for 'hello world' with o200k_base, got {tokens}"

    def test_count_tokens_returns_tuple(self):
        """_count_tokens should return (token_count, is_exact) tuple."""
        result = _count_tokens("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], bool)

    def test_count_tokens_fallback_on_encoding_download_failure(self, monkeypatch):
        """_count_tokens should fall back to inexact estimate when encoding download fails (OSError)."""
        import tiktoken

        # Simulate encoding download failure (e.g., network error)
        def mock_get_encoding(name):
            raise OSError("Encoding not found or network error")

        monkeypatch.setattr(tiktoken, "get_encoding", mock_get_encoding)

        tokens, exact = _count_tokens("hello world")
        assert exact is False, "Expected exact=False when encoding download fails"
        assert isinstance(tokens, int) and tokens > 0, f"Expected positive int, got {tokens}"


class TestTranspileCommand:
    """Tests for the transpile command."""

    def test_transpile_with_empty_value_exits_nonzero(self, capsys, monkeypatch, tmp_path):
        """Running 'h2c transpile' on input with empty-value block should exit non-zero."""
        from h2c.cli.main import main

        # Create a test file with an empty-value block
        test_file = tmp_path / "test_empty.h2c"
        test_file.write_text("[BUILD:EXEC]\nid:|target:main.py\n")

        # Mock sys.argv to simulate: h2c transpile test_empty.h2c
        monkeypatch.setattr(sys, "argv", ["h2c", "transpile", str(test_file)])

        # The command should exit with non-zero status
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code != 0, "Expected non-zero exit code for empty-value block"

        # Check that diagnostic was printed to stderr
        _, stderr = capsys.readouterr()
        assert "empty-value" in stderr or "ERROR" in stderr, (
            f"Expected diagnostic about empty-value in stderr, got: {stderr}"
        )
