"""H2C Context Management rules and thresholds.

Implements the pruning rules table from
docs/architecture/context-lifecycle.md section 3 and
the PRUNE/COMPACT/FREEZE triad from SPEC.md section 5.
"""

from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, FrozenSet, Optional, Tuple

PRUNE_INTERVAL = 5
COMPACT_INTERVAL = 20
FREEZE_THRESHOLD = 100


@unique
class PruneCondition(Enum):
    """Condition under which a block can be pruned."""
    ALWAYS = "always"
    NEVER = "never"
    IF_COMPACT_EXISTS = "if_compact_exists"        # Subsequent COMPACT exists
    IF_DONE_EMITTED = "if_done_emitted"             # Corresponding DONE emitted
    IF_CYCLE_CLOSED = "if_cycle_closed"              # cycle_id closed (TEST:PASS)
    IF_OUTCOME_EMITTED = "if_outcome_emitted"        # TEST outcome known
    IF_NOT_MOST_RECENT = "if_not_most_recent"        # Not the latest COMPACT
    IF_ACKED = "if_acked"                            # After STATE:ACK
    IF_CORRECTED = "if_corrected"                    # After corrected block received


@dataclass(frozen=True)
class PruningRule:
    block_key: str          # "TYPE:SUBTYPE"
    condition: PruneCondition
    description: str


# ── Pruning rules table (18 conditions from context-lifecycle.md §3) ─────────

PRUNING_RULES: Dict[str, PruningRule] = {
    # ARCH:PLAN — prunable only if subsequent COMPACT exists
    "ARCH:PLAN:compact": PruningRule(
        "ARCH:PLAN", PruneCondition.IF_COMPACT_EXISTS,
        "Last ARCH:PLAN with COMPACT: prunable",
    ),
    "ARCH:PLAN:last": PruningRule(
        "ARCH:PLAN", PruneCondition.NEVER,
        "Last ARCH:PLAN without COMPACT: never prune",
    ),

    # BUILD:EXEC — prunable only if corresponding DONE emitted
    "BUILD:EXEC:done": PruningRule(
        "BUILD:EXEC", PruneCondition.IF_DONE_EMITTED,
        "BUILD:DONE emitted: prunable",
    ),
    "BUILD:EXEC:pending": PruningRule(
        "BUILD:EXEC", PruneCondition.NEVER,
        "BUILD:DONE NOT yet emitted: never prune",
    ),

    # BUILD:FIX — prunable only if cycle closed
    "BUILD:FIX:closed": PruningRule(
        "BUILD:FIX", PruneCondition.IF_CYCLE_CLOSED,
        "cycle_id closed: prunable",
    ),
    "BUILD:FIX:open": PruningRule(
        "BUILD:FIX", PruneCondition.NEVER,
        "cycle_id still open: never prune",
    ),

    # BUILD:DONE — prunable if subsequent COMPACT exists
    "BUILD:DONE:compact": PruningRule(
        "BUILD:DONE", PruneCondition.IF_COMPACT_EXISTS,
        "Subsequent COMPACT exists: prunable",
    ),

    # TEST:RUN — prunable if outcome known
    "TEST:RUN:outcome": PruningRule(
        "TEST:RUN", PruneCondition.IF_OUTCOME_EMITTED,
        "Outcome (PASS/FAIL) emitted: prunable",
    ),
    "TEST:RUN:pending": PruningRule(
        "TEST:RUN", PruneCondition.NEVER,
        "Outcome NOT yet emitted: never prune",
    ),

    # TEST:PASS/FAIL — prunable if subsequent COMPACT exists
    "TEST:PASS:compact": PruningRule(
        "TEST:PASS", PruneCondition.IF_COMPACT_EXISTS,
        "Subsequent COMPACT exists: prunable",
    ),
    "TEST:FAIL:compact": PruningRule(
        "TEST:FAIL", PruneCondition.IF_COMPACT_EXISTS,
        "Subsequent COMPACT exists: prunable",
    ),

    # CTX:PRUNE — always prunable after emission
    "CTX:PRUNE": PruningRule(
        "CTX:PRUNE", PruneCondition.ALWAYS,
        "Always prunable after emission",
    ),

    # CTX:COMPACT — only the most recent is kept
    "CTX:COMPACT:recent": PruningRule(
        "CTX:COMPACT", PruneCondition.NEVER,
        "Most recent: never prune",
    ),
    "CTX:COMPACT:old": PruningRule(
        "CTX:COMPACT", PruneCondition.IF_NOT_MOST_RECENT,
        "Previous (not most recent): prunable",
    ),

    # CTX:UPDATE — prunable after subsequent COMPACT
    "CTX:UPDATE": PruningRule(
        "CTX:UPDATE", PruneCondition.IF_COMPACT_EXISTS,
        "After subsequent COMPACT: prunable",
    ),

    # STATE:ACK — prunable after first useful block
    "STATE:ACK": PruningRule(
        "STATE:ACK", PruneCondition.IF_ACKED,
        "After handshake complete: prunable",
    ),

    # STATE:FINDINGS — prunable after subsequent COMPACT
    "STATE:FINDINGS": PruningRule(
        "STATE:FINDINGS", PruneCondition.IF_COMPACT_EXISTS,
        "After subsequent COMPACT: prunable",
    ),

    # CTX:NEGOTIATE — prunable after handshake
    "CTX:NEGOTIATE": PruningRule(
        "CTX:NEGOTIATE", PruneCondition.IF_ACKED,
        "After STATE:ACK: prunable",
    ),

    # BUILD:NACK — prunable after corrected block received
    "BUILD:NACK": PruningRule(
        "BUILD:NACK", PruneCondition.IF_CORRECTED,
        "After corrected block received: prunable",
    ),

    # ORCH:END — never prunable (terminal)
    "ORCH:END": PruningRule(
        "ORCH:END", PruneCondition.NEVER,
        "Never — terminal block",
    ),
}


def get_prune_condition(block_type: str, block_subtype: str) -> PruneCondition:
    """Get the base pruning condition for a block type."""
    key = f"{block_type}:{block_subtype}"
    # Return the most restrictive applicable rule
    for rule_key in PRUNING_RULES:
        if rule_key.startswith(key):
            return PRUNING_RULES[rule_key].condition
    return PruneCondition.ALWAYS  # Unknown blocks: prunable
