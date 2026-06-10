"""H2C block field schemas and validation rule definitions.

Defines REQUIRED/OPTIONAL/RECOMMENDED fields for every block type
from SPEC.md sections 3-8 and docs/specification/grammar.md section 2.
"""

from typing import Dict, FrozenSet, Set

# ── Block field schemas ──────────────────────────────────────────────────────

# Each entry: (required: frozenset, optional: frozenset, recommended: frozenset)
_BLOCK_SCHEMAS: Dict[str, Dict[str, FrozenSet[str]]] = {}

def _s(type_: str, subtype: str, req: set = None, opt: set = None, rec: set = None):
    _BLOCK_SCHEMAS[f"{type_}:{subtype}"] = {
        "required": frozenset(req or set()),
        "optional": frozenset(opt or set()),
        "recommended": frozenset(rec or set()),
    }

# CTX blocks
_s("CTX", "NEGOTIATE", req={"version", "capabilities"})
_s("CTX", "PRIMITIVES", req={"~task", "~constraint", "~goal"}, opt={"~form"})
_s("CTX", "UPDATE", req={"~progress", "~next"}, opt={"~active_files"})
_s("CTX", "PRUNE", req={"keep", "pruned"}, opt={"reason"})
_s("CTX", "COMPACT", req={"summary", "keep_active", "pruned_history"}, opt={"pass_count", "fail_count"})
_s("CTX", "FREEZE", req={"snapshot", "baseline"})

# ARCH
_s("ARCH", "PLAN", req={"id", "fw"}, opt={"lib", "auth", "pattern", "tools", "struct", "deps", "notes"})

# BUILD
# after: accepts a single string or a list (spec says list, but test files
# use single strings like after:t2.1 — we accept both)
_s("BUILD", "EXEC", req={"id", "target"}, opt={"after", "desc", "cmd"})
_s("BUILD", "DONE", req={"id", "diff"}, opt={"rev", "notes", "cycle_id"})
_s("BUILD", "FIX", req={"id", "target", "base_rev", "desc", "cycle_id"}, opt={"retry_n", "cmd"})
_s("BUILD", "REVERT", req={"id", "target", "to_rev"})
_s("BUILD", "NACK", req={"ref_id", "error"}, opt={"hint"})

# TEST
_s("TEST", "RUN", req={"id", "cmd"})
_s("TEST", "PASS", req={"id"}, opt={"cycle_id", "pass_count"})
_s("TEST", "FAIL", req={"id", "error", "cycle_id"}, opt={"fail_count", "pass_count"})

# STATE
_s("STATE", "FINDINGS", req={"id"}, opt={"risk", "pattern", "components", "note"},
  rec={"cause", "action", "impact"})
_s("STATE", "ACK", req={"protocol"})

# ORCH
_s("ORCH", "END", req={"final"}, opt={"est_token", "fail_count", "pass_count"})

# SKILL
_s("SKILL", "PROMPT", req={"id", "role", "activation"})


class BlockSchema:
    """Lookup for block field schemas."""

    @staticmethod
    def get_required_fields(type_: str, subtype: str) -> FrozenSet[str]:
        entry = _BLOCK_SCHEMAS.get(f"{type_}:{subtype}", {})
        return entry.get("required", frozenset())

    @staticmethod
    def get_optional_fields(type_: str, subtype: str) -> FrozenSet[str]:
        entry = _BLOCK_SCHEMAS.get(f"{type_}:{subtype}", {})
        return entry.get("optional", frozenset())

    @staticmethod
    def get_recommended_fields(type_: str, subtype: str) -> FrozenSet[str]:
        entry = _BLOCK_SCHEMAS.get(f"{type_}:{subtype}", {})
        return entry.get("recommended", frozenset())

    @staticmethod
    def get_all_fields(type_: str, subtype: str) -> FrozenSet[str]:
        """Union of required + optional + recommended."""
        entry = _BLOCK_SCHEMAS.get(f"{type_}:{subtype}", {})
        return (
            entry.get("required", frozenset())
            | entry.get("optional", frozenset())
            | entry.get("recommended", frozenset())
        )

    @staticmethod
    def is_valid_block(type_: str, subtype: str) -> bool:
        return f"{type_}:{subtype}" in _BLOCK_SCHEMAS


# ── Integer fields (expected type: integer) ──────────────────────────────────

_INTEGER_FIELDS: Dict[str, FrozenSet[str]] = {
    "BUILD:DONE": frozenset({"rev"}),
    "BUILD:FIX": frozenset({"base_rev", "retry_n"}),
    "BUILD:REVERT": frozenset({"to_rev"}),
    "TEST:PASS": frozenset({"pass_count"}),
    "TEST:FAIL": frozenset({"fail_count", "pass_count"}),
    "CTX:COMPACT": frozenset({"pass_count", "fail_count"}),
    "CTX:FREEZE": frozenset({"baseline"}),
    "ORCH:END": frozenset({"est_token", "fail_count", "pass_count"}),
}

# ── List fields (expected type: list) ────────────────────────────────────────

_LIST_FIELDS: Dict[str, FrozenSet[str]] = {
    "CTX:NEGOTIATE": frozenset({"capabilities"}),
    "ARCH:PLAN": frozenset({"tools", "struct", "notes"}),
    # BUILD:EXEC after: is OPTIONAL and can be string or list
    # "BUILD:EXEC": after is handled leniently — removed from strict list check
    "BUILD:DONE": frozenset({"diff", "notes"}),
    "CTX:UPDATE": frozenset({"~active_files"}),
    # keep: can be string ("last_N") or list — not strictly a list
    "CTX:PRUNE": frozenset({"pruned"}),
    "CTX:COMPACT": frozenset({"summary", "keep_active"}),
    "CTX:FREEZE": frozenset({"snapshot"}),
    "STATE:FINDINGS": frozenset({"risk", "components"}),
}


def is_integer_field(type_: str, subtype: str, field_name: str) -> bool:
    return field_name in _INTEGER_FIELDS.get(f"{type_}:{subtype}", frozenset())


def is_list_field(type_: str, subtype: str, field_name: str) -> bool:
    return field_name in _LIST_FIELDS.get(f"{type_}:{subtype}", frozenset())
