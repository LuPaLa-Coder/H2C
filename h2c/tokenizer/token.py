"""H2C token types and Token dataclass.

Implements the 13 token types from docs/parser/architecture.md section 2.1.
"""

from dataclasses import dataclass
from enum import Enum, unique


@unique
class TokenType(Enum):
    LBRACKET = "LBRACKET"    # [
    RBRACKET = "RBRACKET"    # ]
    COLON = "COLON"          # :
    PIPE = "PIPE"            # |
    COMMA = "COMMA"          # ,
    TILDE = "TILDE"          # ~
    TYPE = "TYPE"            # ARCH|BUILD|TEST|CTX|STATE|ORCH|SKILL
    SUBTYPE = "SUBTYPE"      # PLAN|EXEC|DONE|FIX|...
    KEY = "KEY"              # [a-zA-Z_][a-zA-Z0-9_]*
    INTEGER = "INTEGER"      # [0-9]+
    STRING = "STRING"        # [^\[\]\|\n]+
    NEWLINE = "NEWLINE"      # \n
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: int        # character offset in input
    line: int       # 1-based line number
