"""H2C Semantic Opcodes — side effects on GlobalMemory.

Implements the side effect table from docs/specification/semantics.md section 2.
"""

from h2c.parser.ast import Block, IntegerValue, ListValue, StringValue
from h2c.state.fsm import Opcode
from h2c.state.memory import GlobalMemory


class SideEffectApplier:
    """Applies the semantic side effects of each opcode to GlobalMemory."""

    @staticmethod
    def apply(opcode: Opcode, block: Block, memory: GlobalMemory):
        """Dispatch the side effect for the given opcode."""
        handler = _SIDE_EFFECTS.get(opcode)
        if handler:
            handler(block, memory)


def _field_str(block: Block, name: str) -> str:
    """Extract a string field value."""
    for f in block.fields:
        if f.key == name or (name.startswith("~") and f.key == name):
            if isinstance(f.value, StringValue):
                return f.value.data
            elif isinstance(f.value, IntegerValue):
                return str(f.value.data)
    return ""


def _field_int(block: Block, name: str, default: int = 0) -> int:
    """Extract an integer field value."""
    for f in block.fields:
        if f.key == name:
            if isinstance(f.value, IntegerValue):
                return f.value.data
            elif isinstance(f.value, StringValue):
                try:
                    return int(f.value.data)
                except (ValueError, TypeError):
                    return default
    return default


def _field_list(block: Block, name: str) -> list:
    """Extract a list field value."""
    for f in block.fields:
        if f.key == name:
            if isinstance(f.value, ListValue):
                return f.value.data
    return []


# ── Side effect handlers ─────────────────────────────────────────────────────

def _effect_negotiate(block: Block, memory: GlobalMemory):
    memory.protocol_version = _field_str(block, "version")
    memory.capabilities = _field_list(block, "capabilities")


def _effect_arch_plan(block: Block, memory: GlobalMemory):
    plan_id = _field_str(block, "id")
    memory.context_state["layer"] = "arch"
    memory.context_state["status"] = "planned"
    memory.context_state["plan_id"] = plan_id


def _effect_build_exec(block: Block, memory: GlobalMemory):
    target = _field_str(block, "target")
    memory.context_state["layer"] = "build"
    memory.context_state["status"] = "in_progress"
    memory.context_state["active_target"] = target


def _effect_build_done(block: Block, memory: GlobalMemory):
    memory.context_state["status"] = "done"
    # Register diff revisions
    diff = _field_list(block, "diff")
    for item in diff:
        if "~" in item:
            parts = item.rsplit("~", 1)
            if len(parts) == 2:
                try:
                    memory.revision_table[parts[0]] = int(parts[1])
                except ValueError:
                    pass


def _effect_build_fix(block: Block, memory: GlobalMemory):
    cycle_id = _field_str(block, "cycle_id")
    memory.increment_retry(cycle_id)
    target = _field_str(block, "target")
    memory.context_state["active_target"] = target


def _effect_build_revert(block: Block, memory: GlobalMemory):
    target = _field_str(block, "target")
    to_rev = _field_int(block, "to_rev")
    memory.revision_table[target] = to_rev


def _effect_build_nack(block: Block, memory: GlobalMemory):
    memory.add_finding({
        "type": "NACK",
        "ref_id": _field_str(block, "ref_id"),
        "error": _field_str(block, "error"),
    })


def _effect_test_pass(block: Block, memory: GlobalMemory):
    cycle_id = _field_str(block, "cycle_id")
    if cycle_id:
        memory.increment_pass(cycle_id)
        memory.close_cycle(cycle_id)
    memory.context_state["layer"] = "test"
    memory.context_state["status"] = "passed"


def _effect_test_fail(block: Block, memory: GlobalMemory):
    cycle_id = _field_str(block, "cycle_id")
    memory.increment_fail(cycle_id)
    memory.context_state["layer"] = "test"
    memory.context_state["status"] = "failed"


def _effect_ctx_prune(block: Block, memory: GlobalMemory):
    memory.reset_prune_counter()


def _effect_ctx_compact(block: Block, memory: GlobalMemory):
    memory.reset_prune_counter()
    memory.reset_compact_counter()


def _effect_ctx_freeze(block: Block, memory: GlobalMemory):
    memory.reset_all_counters()


def _effect_state_find(block: Block, memory: GlobalMemory):
    finding = {}
    for field in block.fields:
        key = field.key.lstrip("~")
        if isinstance(field.value, StringValue):
            finding[key] = field.value.data
        elif isinstance(field.value, IntegerValue):
            finding[key] = field.value.data
        elif isinstance(field.value, ListValue):
            finding[key] = field.value.data
    memory.add_finding(finding)


def _effect_state_ack(block: Block, memory: GlobalMemory):
    pass  # ACK just confirms — no side effect beyond state transition


def _effect_orch_end(block: Block, memory: GlobalMemory):
    memory.context_state["status"] = _field_str(block, "final")


def _effect_skill_prompt(block: Block, memory: GlobalMemory):
    pass  # SKILL:PROMPT is a definition block — no runtime side effect


# ── Dispatch table ───────────────────────────────────────────────────────────

_SIDE_EFFECTS = {
    Opcode.CTX_NEGOTIATE: _effect_negotiate,
    Opcode.ARCH_PLAN: _effect_arch_plan,
    Opcode.BUILD_EXEC: _effect_build_exec,
    Opcode.BUILD_DONE: _effect_build_done,
    Opcode.BUILD_FIX: _effect_build_fix,
    Opcode.BUILD_REVERT: _effect_build_revert,
    Opcode.BUILD_NACK: _effect_build_nack,
    Opcode.TEST_PASS: _effect_test_pass,
    Opcode.TEST_FAIL: _effect_test_fail,
    Opcode.CTX_PRUNE: _effect_ctx_prune,
    Opcode.CTX_COMPACT: _effect_ctx_compact,
    Opcode.CTX_FREEZE: _effect_ctx_freeze,
    Opcode.STATE_FIND: _effect_state_find,
    Opcode.STATE_ACK: _effect_state_ack,
    Opcode.ORCH_END: _effect_orch_end,
    Opcode.SKILL_PROMPT: _effect_skill_prompt,
}
