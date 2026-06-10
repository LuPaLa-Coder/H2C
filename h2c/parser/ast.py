"""H2C Abstract Syntax Tree types.

Implements the AST model from docs/parser/architecture.md section 4
and docs/specification/grammar.md section 3.
"""

from dataclasses import dataclass, field
from enum import Enum, unique
from typing import List, Optional, Union


@unique
class Type(Enum):
    ARCH = "ARCH"
    BUILD = "BUILD"
    TEST = "TEST"
    CTX = "CTX"
    STATE = "STATE"
    ORCH = "ORCH"
    SKILL = "SKILL"


@unique
class Subtype(Enum):
    PLAN = "PLAN"
    EXEC = "EXEC"
    DONE = "DONE"
    FIX = "FIX"
    REVERT = "REVERT"
    NACK = "NACK"
    RUN = "RUN"
    PASS = "PASS"
    FAIL = "FAIL"
    PRIMITIVES = "PRIMITIVES"
    UPDATE = "UPDATE"
    PRUNE = "PRUNE"
    COMPACT = "COMPACT"
    FREEZE = "FREEZE"
    NEGOTIATE = "NEGOTIATE"
    FINDINGS = "FINDINGS"
    ACK = "ACK"
    END = "END"
    PROMPT = "PROMPT"


# ── Value types ──────────────────────────────────────────────────────────────


@dataclass
class StringValue:
    data: str


@dataclass
class ListValue:
    data: List[str]


@dataclass
class RevisionValue:
    file: str
    rev: int


@dataclass
class IntegerValue:
    data: int


@dataclass
class SignedIntValue:
    data: int  # stored as int, positive or negative


Value = Union[StringValue, ListValue, RevisionValue, IntegerValue, SignedIntValue]


# ── Composite types ──────────────────────────────────────────────────────────


@dataclass
class Field:
    key: str
    value: Value
    is_ctx: bool = False  # True when key is prefixed with ~ (CTX blocks)


@dataclass
class Block:
    type: str          # "ARCH" | "BUILD" | ...
    subtype: str       # "PLAN" | "EXEC" | ...
    fields: List[Field] = field(default_factory=list)
    original_text: str = ""  # raw source text for error reporting


@dataclass
class Message:
    blocks: List[Block] = field(default_factory=list)

    def to_json_ast(self) -> dict:
        """Return the JSON AST form from docs/specification/grammar.md section 5."""
        return {
            "messages": [
                {
                    "type": b.type,
                    "subtype": b.subtype,
                    "fields": [
                        _field_to_json(f) for f in b.fields
                    ],
                }
                for b in self.blocks
            ],
        }


def _field_to_json(f: Field) -> dict:
    val = f.value
    if isinstance(val, StringValue):
        vj = {"type": "string", "data": val.data}
    elif isinstance(val, ListValue):
        vj = {"type": "list", "data": val.data}
    elif isinstance(val, RevisionValue):
        vj = {"type": "revision", "data": {"file": val.file, "rev": val.rev}}
    elif isinstance(val, IntegerValue):
        vj = {"type": "integer", "data": val.data}
    elif isinstance(val, SignedIntValue):
        vj = {"type": "signed_int", "data": val.data}
    else:
        vj = {"type": "unknown", "data": str(val)}
    return {"key": f.key, "value": vj}
