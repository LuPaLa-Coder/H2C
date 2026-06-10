"""H2C Scanner / Tokenizer.

Implements the scanning algorithm from docs/parser/architecture.md section 2.2.
Uses manual scanning with re.match at each position for correct PEG-like
token type resolution: TYPE before KEY, SUBTYPE before KEY, etc.
"""

import re
from typing import Iterator, List

from h2c.tokenizer.token import Token, TokenType

# PEG scanning order (first match wins):
# TYPE → SUBTYPE → INTEGER → STRING → KEY
# TYPE/SUBTYPE before STRING so ARCH/PLAN don't match as STRING.
# INTEGER before STRING so "42" doesn't match as STRING.
# STRING before KEY so "api-meteo" is one token, not KEY:api + STRING:-meteo.
_SINGLE_CHAR: dict[str, TokenType] = {
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ":": TokenType.COLON,
    "|": TokenType.PIPE,
    ",": TokenType.COMMA,
    "~": TokenType.TILDE,
}

_TYPE_RE = re.compile(r"ARCH|BUILD|TEST|CTX|STATE|ORCH|SKILL")
_SUBTYPE_RE = re.compile(
    r"PLAN|EXEC|DONE|FIX|REVERT|NACK|"
    r"RUN|PASS|FAIL|"
    r"PRIMITIVES|UPDATE|PRUNE|COMPACT|FREEZE|NEGOTIATE|"
    r"FINDINGS|ACK|"
    r"END|PROMPT"
)
_KEY_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_INTEGER_RE = re.compile(r"[0-9]+")
_STRING_RE = re.compile(r"[^\[\]\|\n:]+")


class Scanner:
    """Tokenizes H2C source text into a stream of Token objects."""

    def __init__(self, text: str):
        self._text = text
        self._pos = 0
        self._line = 1

    def scan(self) -> Iterator[Token]:
        """Lazily yield tokens from the input text."""
        length = len(self._text)
        while self._pos < length:
            ch = self._text[self._pos]

            # Comment: skip from # to end of line
            if ch == "#":
                while self._pos < length and self._text[self._pos] != "\n":
                    self._pos += 1
                continue

            # Newline
            if ch == "\n":
                yield self._make(TokenType.NEWLINE, "\n")
                self._pos += 1
                self._line += 1
                continue

            # Whitespace (skip, but count lines within it)
            if ch in (" ", "\t", "\r"):
                if ch == "\r":
                    if self._pos + 1 < length and self._text[self._pos + 1] == "\n":
                        self._pos += 2
                        self._line += 1
                        yield self._make(TokenType.NEWLINE, "\n")
                        continue
                self._pos += 1
                continue

            # Single-character tokens
            if ch in _SINGLE_CHAR:
                yield self._make(_SINGLE_CHAR[ch], ch)
                self._pos += 1
                continue

            # Multi-character tokens — try in PEG order
            remaining = self._text[self._pos:]

            m = _TYPE_RE.match(remaining)
            if m:
                yield self._make(TokenType.TYPE, m.group())
                self._pos += len(m.group())
                continue

            m = _SUBTYPE_RE.match(remaining)
            if m:
                yield self._make(TokenType.SUBTYPE, m.group())
                self._pos += len(m.group())
                continue

            m = _INTEGER_RE.match(remaining)
            if m:
                yield self._make(TokenType.INTEGER, m.group())
                self._pos += len(m.group())
                continue

            m = _STRING_RE.match(remaining)
            if m:
                yield self._make(TokenType.STRING, m.group())
                self._pos += len(m.group())
                continue

            m = _KEY_RE.match(remaining)
            if m:
                yield self._make(TokenType.KEY, m.group())
                self._pos += len(m.group())
                continue

            # Should not happen, but skip unrecognized char
            self._pos += 1

        yield Token(TokenType.EOF, "", self._pos, self._line)

    def scan_all(self) -> List[Token]:
        """Return all tokens as a materialized list."""
        return list(self.scan())

    def _make(self, type_: TokenType, value: str) -> Token:
        return Token(type=type_, value=value, pos=self._pos, line=self._line)


def tokenize(text: str) -> List[Token]:
    """Convenience: tokenize text and return list of tokens."""
    return Scanner(text).scan_all()
