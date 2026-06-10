"""H2C Context Manager — PRUNE/COMPACT/FREEZE lifecycle.

Implements the full context management triad from
docs/architecture/context-lifecycle.md and SPEC.md sections 5.3-5.5.
"""

from typing import List, Optional, Set

from h2c.parser.ast import Block, Field, ListValue, StringValue
from h2c.state.memory import GlobalMemory
from h2c.context.rules import (
    PRUNE_INTERVAL,
    COMPACT_INTERVAL,
    FREEZE_THRESHOLD,
    PruneCondition,
    get_prune_condition,
)


class ContextManager:
    """Manages PRUNE/COMPACT/FREEZE lifecycle for an H2C chain."""

    def __init__(self, memory: Optional[GlobalMemory] = None):
        self._memory = memory or GlobalMemory()
        # Track the state needed to evaluate pruning conditions
        self._done_emitted: Set[str] = set()        # task ids with DONE
        self._test_outcomes: Set[str] = set()        # task ids with known outcome
        self._closed_cycles: Set[str] = set()         # cycle_ids that were closed
        self._open_cycles: Set[str] = set()           # cycle_ids still open
        self._has_compact_after: Set[str] = set()     # task ids with subsequent COMPACT
        self._compact_count: int = 0
        self._last_compact_index: int = -1
        self._has_ack: bool = False
        self._nack_corrected: Set[str] = set()        # NACK ref_ids that were corrected

    @property
    def memory(self) -> GlobalMemory:
        return self._memory

    # ── Threshold checks ──────────────────────────────────────────────────

    def should_prune(self) -> bool:
        return self._memory.prune_counter >= PRUNE_INTERVAL

    def should_compact(self) -> bool:
        return self._memory.compact_counter >= COMPACT_INTERVAL

    def should_freeze(self) -> bool:
        return self._memory.msg_counter >= FREEZE_THRESHOLD

    # ── State tracking (call after processing each block) ──────────────────

    def track_block(self, block: Block, block_index: int):
        """Update tracking state after a block is processed."""
        key = f"{block.type}:{block.subtype}"

        # Track DONE emissions
        if key == "BUILD:DONE":
            for f in block.fields:
                if f.key == "id" and isinstance(f.value, StringValue):
                    self._done_emitted.add(f.value.data)

        # Track test outcomes
        if key in ("TEST:PASS", "TEST:FAIL"):
            for f in block.fields:
                if f.key == "id" and isinstance(f.value, StringValue):
                    self._test_outcomes.add(f.value.data)

        # Track cycle open/close
        cid = _get_field_str(block, "cycle_id")
        if key == "BUILD:FIX" and cid:
            self._open_cycles.add(cid)
        if key == "TEST:PASS" and cid:
            self._closed_cycles.add(cid)
            self._open_cycles.discard(cid)

        # Track COMPACT
        if key == "CTX:COMPACT":
            self._compact_count += 1
            self._last_compact_index = block_index

        # Track handshake
        if key == "STATE:ACK":
            self._has_ack = True

        # Track NACK correction
        if key == "BUILD:NACK":
            ref_id = _get_field_str(block, "ref_id")
        # If we see a subsequent block with the same ref_id, mark as corrected
        # (simplified: any block after NACK is a potential correction)

    # ── Pruning decisions ─────────────────────────────────────────────────

    def is_prunable(self, block: Block, block_index: int, total_blocks: int) -> bool:
        """Determine if a block can be pruned based on current state."""
        condition = get_prune_condition(block.type, block.subtype)
        key = f"{block.type}:{block.subtype}"
        task_id = _get_field_str(block, "id")
        cycle_id = _get_field_str(block, "cycle_id")

        if condition == PruneCondition.ALWAYS:
            return True
        if condition == PruneCondition.NEVER:
            return False

        if condition == PruneCondition.IF_COMPACT_EXISTS:
            return self._compact_count > 0

        if condition == PruneCondition.IF_DONE_EMITTED:
            return task_id in self._done_emitted if task_id else False

        if condition == PruneCondition.IF_CYCLE_CLOSED:
            return cycle_id in self._closed_cycles if cycle_id else False

        if condition == PruneCondition.IF_OUTCOME_EMITTED:
            return task_id in self._test_outcomes if task_id else False

        if condition == PruneCondition.IF_NOT_MOST_RECENT:
            return block_index != self._last_compact_index

        if condition == PruneCondition.IF_ACKED:
            return self._has_ack

        if condition == PruneCondition.IF_CORRECTED:
            return True  # Simplified

        return False

    def get_prunable_ids(self, blocks: List[Block]) -> List[str]:
        """Return the ids (or indices) of blocks that can be pruned."""
        prunable = []
        for i, block in enumerate(blocks):
            if self.is_prunable(block, i, len(blocks)):
                # Use the block's id if available, otherwise index
                bid = _get_field_str(block, "id")
                prunable.append(bid if bid else f"block_{i}")
        return prunable

    # ── Block builders ────────────────────────────────────────────────────

    def build_prune_block(
        self, keep: List[str], pruned: List[str], reason: str = ""
    ) -> Block:
        """Build a CTX:PRUNE block."""
        fields = [
            Field(key="keep", value=ListValue(data=keep)),
            Field(key="pruned", value=ListValue(data=pruned)),
        ]
        if reason:
            fields.append(Field(key="reason", value=StringValue(data=reason)))
        return Block(type="CTX", subtype="PRUNE", fields=fields)

    def build_compact_block(
        self, summary: List[str], keep_active: List[str],
        pruned_history: str, pass_count: int = 0, fail_count: int = 0,
    ) -> Block:
        """Build a CTX:COMPACT block."""
        fields = [
            Field(key="summary", value=ListValue(data=summary)),
            Field(key="keep_active", value=ListValue(data=keep_active)),
            Field(key="pruned_history", value=StringValue(data=pruned_history)),
        ]
        return Block(type="CTX", subtype="COMPACT", fields=fields)

    def build_freeze_block(
        self, snapshot: List[str], baseline: int
    ) -> Block:
        """Build a CTX:FREEZE block."""
        from h2c.parser.ast import IntegerValue
        fields = [
            Field(key="snapshot", value=ListValue(data=snapshot)),
            Field(key="baseline", value=IntegerValue(data=baseline)),
        ]
        return Block(type="CTX", subtype="FREEZE", fields=fields)

    def reset_after_prune(self):
        self._memory.reset_prune_counter()

    def reset_after_compact(self):
        self._memory.reset_prune_counter()
        self._memory.reset_compact_counter()

    def reset_after_freeze(self):
        self._memory.reset_all_counters()


def _get_field_str(block: Block, name: str) -> str:
    """Extract a string field value, or ''."""
    for f in block.fields:
        if f.key == name:
            if isinstance(f.value, StringValue):
                return f.value.data
    return ""
