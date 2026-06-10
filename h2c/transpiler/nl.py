"""H2C-to-Natural-Language codegen.

Implements the NL templates from docs/compiler/pipeline.md section 3.1.
"""

from typing import List

from h2c.parser.ast import (
    Block,
    IntegerValue,
    ListValue,
    Message,
    RevisionValue,
    SignedIntValue,
    StringValue,
)


class NLCodegen:
    """Transpiles H2C AST blocks into human-readable natural language."""

    def generate(self, message: Message) -> str:
        return "\n\n".join(
            self.generate_block(b) for b in message.blocks
        )

    def generate_block(self, block: Block) -> str:
        handler = _TEMPLATES.get(f"{block.type}:{block.subtype}")
        if handler:
            return handler(block)
        return _fallback(block)


def _render_field(block: Block, name: str, default: str = "") -> str:
    for f in block.fields:
        if f.key == name:
            v = f.value
            if isinstance(v, StringValue):
                return v.data
            elif isinstance(v, IntegerValue):
                return str(v.data)
    return default


def _render_list(block: Block, name: str) -> List[str]:
    for f in block.fields:
        if f.key == name and isinstance(f.value, ListValue):
            return f.value.data
    return []


def _render_all_fields(block: Block) -> str:
    parts = []
    for f in block.fields:
        v = f.value
        if isinstance(v, StringValue):
            parts.append(f"{f.key}: {v.data}")
        elif isinstance(v, IntegerValue):
            parts.append(f"{f.key}: {v.data}")
        elif isinstance(v, ListValue):
            parts.append(f"{f.key}: [{', '.join(v.data)}]")
        elif isinstance(v, RevisionValue):
            parts.append(f"{f.key}: {v.file} (rev {v.rev})")
        elif isinstance(v, SignedIntValue):
            parts.append(f"{f.key}: {v.data:+d}")
    return ", ".join(parts)


def _fallback(block: Block) -> str:
    return f"[{block.type}:{block.subtype}]\n{_render_all_fields(block)}"


# ── Templates ────────────────────────────────────────────────────────────────

def _t_arch_plan(block: Block) -> str:
    plan_id = _render_field(block, "id")
    fw = _render_field(block, "fw")
    lib = _render_field(block, "lib")
    auth = _render_field(block, "auth")
    pattern = _render_field(block, "pattern")
    notes = _render_list(block, "notes")

    lines = [f"Architectural plan for {plan_id}."]
    lines.append(f"  Framework: {fw}")
    if lib:
        lines.append(f"  Libraries: {lib}")
    if auth:
        lines.append(f"  Auth: {auth}")
    if pattern:
        lines.append(f"  Pattern: {pattern}")
    if notes:
        lines.append(f"  Notes: {', '.join(notes)}")
    return "\n".join(lines)


def _t_build_exec(block: Block) -> str:
    bid = _render_field(block, "id")
    target = _render_field(block, "target")
    desc = _render_field(block, "desc")
    after = _render_list(block, "after")

    parts = [f"Execute build {bid} on {target}."]
    if desc:
        parts.append(f"  Description: {desc}")
    if after:
        parts.append(f"  After: {', '.join(after)}")
    return "\n".join(parts)


def _t_build_done(block: Block) -> str:
    bid = _render_field(block, "id")
    diff = _render_list(block, "diff")
    rev = _render_field(block, "rev")
    return f"Build {bid} completed. Diff: [{', '.join(diff)}] rev={rev}"


def _t_build_fix(block: Block) -> str:
    target = _render_field(block, "target")
    base_rev = _render_field(block, "base_rev")
    desc = _render_field(block, "desc")
    cid = _render_field(block, "cycle_id")
    retry = _render_field(block, "retry_n")
    return f"Fix {target} (rev {base_rev}): {desc}. cycle_id={cid} retry={retry}"


def _t_build_revert(block: Block) -> str:
    bid = _render_field(block, "id")
    target = _render_field(block, "target")
    to_rev = _render_field(block, "to_rev")
    return f"Revert {bid}: {target} to revision {to_rev}."


def _t_build_nack(block: Block) -> str:
    ref = _render_field(block, "ref_id")
    err = _render_field(block, "error")
    hint = _render_field(block, "hint")
    msg = f"Rejected block {ref}: {err}."
    if hint:
        msg += f" Hint: {hint}"
    return msg


def _t_test_run(block: Block) -> str:
    tid = _render_field(block, "id")
    cmd = _render_field(block, "cmd")
    return f"Run test {tid}: {cmd}"


def _t_test_pass(block: Block) -> str:
    tid = _render_field(block, "id")
    pc = _render_field(block, "pass_count")
    cid = _render_field(block, "cycle_id")
    msg = f"Test {tid} passed"
    if pc:
        msg += f" ({pc} assertions)"
    if cid:
        msg += f" — cycle {cid} closed"
    return msg + "."


def _t_test_fail(block: Block) -> str:
    tid = _render_field(block, "id")
    err = _render_field(block, "error")
    cid = _render_field(block, "cycle_id")
    fc = _render_field(block, "fail_count")
    return f"Test {tid} failed: {err}. cycle_id={cid} fail_count={fc}"


def _t_ctx_negotiate(block: Block) -> str:
    ver = _render_field(block, "version")
    caps = _render_list(block, "capabilities")
    return f"Handshake: protocol {ver}, capabilities: [{', '.join(caps)}]"


def _t_ctx_primitives(block: Block) -> str:
    return f"Initial state: {_render_all_fields(block)}"


def _t_ctx_update(block: Block) -> str:
    return f"Context update: {_render_all_fields(block)}"


def _t_ctx_prune(block: Block) -> str:
    keep = _render_list(block, "keep")
    pruned = _render_list(block, "pruned")
    reason = _render_field(block, "reason")
    msg = f"Context pruning: kept [{', '.join(keep)}], pruned [{', '.join(pruned)}]"
    if reason:
        msg += f" — {reason}"
    return msg


def _t_ctx_compact(block: Block) -> str:
    summary = _render_list(block, "summary")
    keep = _render_list(block, "keep_active")
    pruned = _render_field(block, "pruned_history")
    return f"Compaction: summary={summary}, keep_active=[{', '.join(keep)}], pruned={pruned}"


def _t_ctx_freeze(block: Block) -> str:
    snap = _render_list(block, "snapshot")
    baseline = _render_field(block, "baseline")
    return f"Context frozen at msg {baseline}. Snapshot: [{', '.join(snap)}]"


def _t_state_findings(block: Block) -> str:
    fid = _render_field(block, "id")
    cause = _render_field(block, "cause")
    action = _render_field(block, "action")
    impact = _render_field(block, "impact")
    risk = _render_list(block, "risk")
    parts = [f"Finding {fid}:"]
    if cause:
        parts.append(f"  Cause: {cause}")
    if action:
        parts.append(f"  Action: {action}")
    if impact:
        parts.append(f"  Impact: {impact}")
    if risk:
        parts.append(f"  Residual risks: {', '.join(risk)}")
    return "\n".join(parts)


def _t_state_ack(block: Block) -> str:
    proto = _render_field(block, "protocol")
    return f"Protocol acknowledged: {proto}"


def _t_orch_end(block: Block) -> str:
    final = _render_field(block, "final")
    est = _render_field(block, "est_token")
    msg = f"Orchestration terminated: {final}"
    if est:
        msg += f" (est. {est} tokens)"
    return msg + "."


# ── Template registry ────────────────────────────────────────────────────────

_TEMPLATES = {
    "ARCH:PLAN": _t_arch_plan,
    "BUILD:EXEC": _t_build_exec,
    "BUILD:DONE": _t_build_done,
    "BUILD:FIX": _t_build_fix,
    "BUILD:REVERT": _t_build_revert,
    "BUILD:NACK": _t_build_nack,
    "TEST:RUN": _t_test_run,
    "TEST:PASS": _t_test_pass,
    "TEST:FAIL": _t_test_fail,
    "CTX:NEGOTIATE": _t_ctx_negotiate,
    "CTX:PRIMITIVES": _t_ctx_primitives,
    "CTX:UPDATE": _t_ctx_update,
    "CTX:PRUNE": _t_ctx_prune,
    "CTX:COMPACT": _t_ctx_compact,
    "CTX:FREEZE": _t_ctx_freeze,
    "STATE:FINDINGS": _t_state_findings,
    "STATE:ACK": _t_state_ack,
    "ORCH:END": _t_orch_end,
}
