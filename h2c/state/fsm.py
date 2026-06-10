"""H2C Finite State Machine — 14 states, 58 transitions.

Implements the state model and transition matrix from
docs/specification/semantics.md section 1.
"""

from enum import Enum, unique
from typing import Dict, Optional, Tuple

from h2c.parser.ast import Block
from h2c.state.memory import GlobalMemory


@unique
class State(Enum):
    INIT = "INIT"
    HANDSHAKE = "HANDSHAKE"
    ACKED = "ACKED"
    PLANNED = "PLANNED"
    BUILDING = "BUILDING"
    BUILT = "BUILT"
    TESTING = "TESTING"
    TEST_PASS = "TEST_PASS"
    TEST_FAIL = "TEST_FAIL"
    FIXING = "FIXING"
    REJECTING = "REJECTING"
    COMPACT = "COMPACT"
    FROZEN = "FROZEN"
    TERM = "TERM"


@unique
class Opcode(Enum):
    CTX_NEGOTIATE = ("◈N", "Version handshake, capability negotiation")
    ARCH_PLAN = ("↻", "Initialize context, define plan")
    BUILD_EXEC = ("→", "Start execution on target")
    BUILD_DONE = ("✓", "Register completion and diff")
    BUILD_FIX = ("✗→", "Request correction on revision")
    BUILD_REVERT = ("↩", "Return to previous revision")
    BUILD_NACK = ("✗N", "Reject malformed block with error")
    TEST_RUN = ("⚡", "Execute test suite")
    TEST_PASS = ("✔", "Test passed, increment counter")
    TEST_FAIL = ("✘", "Test failed, open fix cycle")
    CTX_PRIM = ("◈", "Initial state snapshot")
    CTX_UPD = ("◈→", "Update current layer")
    CTX_PRUNE = ("✂", "Prune unnecessary messages")
    CTX_COMPACT = ("⊞", "Compact cumulative history")
    CTX_FREEZE = ("⊟", "Freeze baseline, reset counters")
    STATE_FIND = ("◆", "Emit analysis result")
    STATE_ACK = ("◀", "Acknowledge protocol")
    ORCH_END = ("■", "Terminate orchestration")
    SKILL_PROMPT = ("⚙", "Agent definition block")

    def __init__(self, symbol: str, description: str):
        self.symbol = symbol
        self.description = description


# ── Transition table ─────────────────────────────────────────────────────────

# Key: (current_state, "TYPE:SUBTYPE") → new_state
# Built from semantics.md §1 transition matrix (58 entries).
# ANY states are expanded for all applicable states.

_TRANSITIONS: Dict[Tuple[State, str], State] = {}

def _t(state: State, block_type: str, new_state: State):
    """Register a transition."""
    _TRANSITIONS[(state, block_type)] = new_state

def _t_any(states: Tuple[State, ...], block_type: str, new_state: State):
    """Register the same transition for multiple source states."""
    for s in states:
        _TRANSITIONS[(s, block_type)] = new_state

_ALL_EXCEPT_TERM = (
    State.INIT, State.HANDSHAKE, State.ACKED, State.PLANNED,
    State.BUILDING, State.BUILT, State.TESTING, State.TEST_PASS,
    State.TEST_FAIL, State.FIXING, State.REJECTING,
    State.COMPACT, State.FROZEN,
)

# From the transition matrix:
_t(State.INIT, "CTX:NEGOTIATE", State.HANDSHAKE)
_t(State.HANDSHAKE, "STATE:ACK", State.ACKED)
_t(State.ACKED, "ARCH:PLAN", State.PLANNED)
_t(State.PLANNED, "BUILD:EXEC", State.BUILDING)
_t(State.PLANNED, "TEST:RUN", State.TESTING)
_t(State.BUILDING, "BUILD:DONE", State.BUILT)
_t(State.BUILT, "TEST:RUN", State.TESTING)
_t(State.BUILT, "BUILD:EXEC", State.BUILDING)
_t(State.TESTING, "TEST:PASS", State.TEST_PASS)
_t(State.TESTING, "TEST:FAIL", State.TEST_FAIL)
_t(State.TEST_FAIL, "BUILD:FIX", State.FIXING)
_t(State.TEST_FAIL, "BUILD:REVERT", State.BUILT)
_t(State.FIXING, "BUILD:DONE", State.BUILT)

# From BUILT or TEST_PASS, next BUILD:EXEC starts building again
_t(State.BUILT, "BUILD:EXEC", State.BUILDING)
_t(State.TEST_PASS, "BUILD:EXEC", State.BUILDING)

# Context management transitions (ANY → state)
_t_any(_ALL_EXCEPT_TERM, "CTX:PRUNE", None)  # None = state unchanged
_t_any(_ALL_EXCEPT_TERM, "CTX:COMPACT", State.COMPACT)
_t_any(_ALL_EXCEPT_TERM, "CTX:FREEZE", State.FROZEN)

# After COMPACT, next step
_t(State.COMPACT, "BUILD:EXEC", State.BUILDING)
_t(State.COMPACT, "TEST:RUN", State.TESTING)
_t(State.COMPACT, "CTX:FREEZE", State.FROZEN)

# After FREEZE, next step
_t(State.FROZEN, "BUILD:EXEC", State.BUILDING)
_t(State.FROZEN, "TEST:RUN", State.TESTING)
_t(State.FROZEN, "CTX:PRUNE", State.FROZEN)
_t(State.FROZEN, "STATE:FINDINGS", State.FROZEN)

# NACK (ANY except TERM → REJECTING)
_t_any(_ALL_EXCEPT_TERM, "BUILD:NACK", State.REJECTING)
# REJECTING → (corrected block) → appropriate state — handled by caller

# Terminal transitions
_t(State.TEST_PASS, "ORCH:END", State.TERM)
_t(State.FROZEN, "ORCH:END", State.TERM)
_t_any(_ALL_EXCEPT_TERM, "ORCH:END", State.TERM)

# SKILL:PROMPT is a definition block, doesn't change state
_t_any(_ALL_EXCEPT_TERM, "SKILL:PROMPT", None)

# STATE:FINDINGS doesn't change state (documented as ANY → state unchanged)
_t_any(_ALL_EXCEPT_TERM, "STATE:FINDINGS", None)

# CTX:PRIMITIVES and CTX:UPDATE don't change state
_t_any(_ALL_EXCEPT_TERM, "CTX:PRIMITIVES", None)
_t_any(_ALL_EXCEPT_TERM, "CTX:UPDATE", None)


class StateMachine:
    """Manages the FSM for an H2C chain execution."""

    def __init__(self, memory: Optional[GlobalMemory] = None):
        self._state = State.INIT
        self._memory = memory or GlobalMemory()

    @property
    def current_state(self) -> State:
        return self._state

    @property
    def memory(self) -> GlobalMemory:
        return self._memory

    def reset(self):
        """Reset to initial state with clean memory."""
        self._state = State.INIT
        self._memory = GlobalMemory()

    def transition(self, block: Block) -> State:
        """Apply a block to the state machine and return the new state.

        Returns None if the block type doesn't cause a state change
        (e.g., CTX:PRUNE).
        """
        block_key = f"{block.type}:{block.subtype}"
        key = (self._state, block_key)
        new_state = _TRANSITIONS.get(key)

        if new_state is None:
            # Check ANY-state wildcards (keyed with the current state)
            pass  # Already handled by _t_any which pre-registers per-state

        if new_state is not None:
            self._state = new_state

        self._memory.increment_message()
        return new_state

    @staticmethod
    def block_to_opcode(block: Block) -> Optional[Opcode]:
        """Map a block to its semantic opcode."""
        mapping = {
            "CTX:NEGOTIATE": Opcode.CTX_NEGOTIATE,
            "ARCH:PLAN": Opcode.ARCH_PLAN,
            "BUILD:EXEC": Opcode.BUILD_EXEC,
            "BUILD:DONE": Opcode.BUILD_DONE,
            "BUILD:FIX": Opcode.BUILD_FIX,
            "BUILD:REVERT": Opcode.BUILD_REVERT,
            "BUILD:NACK": Opcode.BUILD_NACK,
            "TEST:RUN": Opcode.TEST_RUN,
            "TEST:PASS": Opcode.TEST_PASS,
            "TEST:FAIL": Opcode.TEST_FAIL,
            "CTX:PRIMITIVES": Opcode.CTX_PRIM,
            "CTX:UPDATE": Opcode.CTX_UPD,
            "CTX:PRUNE": Opcode.CTX_PRUNE,
            "CTX:COMPACT": Opcode.CTX_COMPACT,
            "CTX:FREEZE": Opcode.CTX_FREEZE,
            "STATE:FINDINGS": Opcode.STATE_FIND,
            "STATE:ACK": Opcode.STATE_ACK,
            "ORCH:END": Opcode.ORCH_END,
            "SKILL:PROMPT": Opcode.SKILL_PROMPT,
        }
        return mapping.get(f"{block.type}:{block.subtype}")

    def is_terminal(self) -> bool:
        return self._state == State.TERM
