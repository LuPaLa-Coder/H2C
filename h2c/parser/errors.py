"""H2C parser error types.

Implements the error taxonomy from docs/parser/architecture.md section 5.1.
"""


class H2CParseError(Exception):
    """Base class for all H2C parsing errors."""

    def __init__(self, message: str, pos: int = -1, line: int = -1):
        super().__init__(message)
        self.pos = pos
        self.line = line


class UnexpectedToken(H2CParseError):
    """Parser received an unexpected token for the current grammar production."""

    def __init__(self, expected: str, got: str, pos: int = -1, line: int = -1):
        super().__init__(
            f"Expected {expected}, got {got}",
            pos=pos,
            line=line,
        )
        self.expected = expected
        self.got = got


class MalformedBlock(H2CParseError):
    """A block has structural issues (invalid type/subtype, missing bracket)."""

    pass


class InvalidType(H2CParseError):
    """The TYPE token does not match a known H2C type."""

    pass


class InvalidSubtype(H2CParseError):
    """The SUBTYPE token does not match a known H2C subtype."""

    pass


class MissingRequiredField(H2CParseError):
    """A REQUIRED field is absent from the block."""

    pass
