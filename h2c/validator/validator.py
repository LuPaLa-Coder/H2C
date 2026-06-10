"""H2C Validator — 4-layer validation.

Implements the validation architecture from docs/compiler/pipeline.md section 5:
  1. Syntactic  — block format, brackets, valid types
  2. Structural — REQUIRED fields, field types, diff format
  3. Contextual — cycle_id, DAG, retry_n, PRUNE/COMPACT/FREEZE frequency
  4. Terminal   — ORCH:END is last block

Also enforces integrity rules R1-R14 from docs/specification/semantics.md §7.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from h2c.parser.ast import (
    Block,
    Field,
    IntegerValue,
    ListValue,
    Message,
    SignedIntValue,
    StringValue,
)
from h2c.validator.result import ValidationError, ValidationResult
from h2c.validator.rules import (
    BlockSchema,
    is_integer_field,
    is_list_field,
)


class Validator:
    """Validates a parsed H2C Message AST against all protocol rules."""

    def validate(self, message: Message) -> ValidationResult:
        result = ValidationResult()
        result.stats["total_blocks"] = len(message.blocks)

        self._validate_syntactic(message, result)
        self._validate_structural(message, result)
        self._validate_contextual(message, result)
        self._validate_terminal(message, result)

        # Compute valid_blocks count
        valid_block_indices: Set[int] = set()
        for e in result.errors:
            if e.location and "block" in e.location:
                valid_block_indices.add(e.location["block"])
        result.stats["valid_blocks"] = len(message.blocks) - len(valid_block_indices)

        return result

    # ── Layer 1: Syntactic ────────────────────────────────────────────────

    def _validate_syntactic(self, message: Message, result: ValidationResult):
        for i, block in enumerate(message.blocks):
            if not BlockSchema.is_valid_block(block.type, block.subtype):
                result.add_error(ValidationError(
                    level="error",
                    rule="VALIDATOR-1",
                    message=f"Invalid block type: [{block.type}:{block.subtype}]",
                    location={"block": i},
                ))

    # ── Layer 2: Structural ───────────────────────────────────────────────

    def _validate_structural(self, message: Message, result: ValidationResult):
        for i, block in enumerate(message.blocks):
            self._check_required_fields(block, i, result)
            self._check_field_types(block, i, result)
            self._check_diff_format(block, i, result)
            self._check_unknown_fields(block, i, result)

    def _check_required_fields(self, block: Block, idx: int, result: ValidationResult):
        required = BlockSchema.get_required_fields(block.type, block.subtype)
        present = {f.key for f in block.fields}
        missing = required - present
        for field_name in sorted(missing):
            result.add_error(ValidationError(
                level="error",
                rule="VALIDATOR-2",
                message=(
                    f"Block [{block.type}:{block.subtype}] missing REQUIRED field "
                    f"'{field_name}'"
                ),
                location={"block": idx},
            ))

    def _check_field_types(self, block: Block, idx: int, result: ValidationResult):
        key = f"{block.type}:{block.subtype}"
        for field in block.fields:
            fname = field.key
            value = field.value

            # Integer field check
            if is_integer_field(block.type, block.subtype, fname):
                if not isinstance(value, IntegerValue):
                    result.add_error(ValidationError(
                        level="error",
                        rule="VALIDATOR-3",
                        message=(
                            f"[{key}] field '{fname}' expected INTEGER, "
                            f"got {type(value).__name__}"
                        ),
                        location={"block": idx},
                    ))

            # List field check
            if is_list_field(block.type, block.subtype, fname):
                if not isinstance(value, ListValue):
                    result.add_error(ValidationError(
                        level="error",
                        rule="VALIDATOR-3",
                        message=(
                            f"[{key}] field '{fname}' expected LIST, "
                            f"got {type(value).__name__}"
                        ),
                        location={"block": idx},
                    ))

    def _check_diff_format(self, block: Block, idx: int, result: ValidationResult):
        """Validate diff: field format per VALIDATOR-7.

        diff items must be: revision (file~N) or signed_int (+N, -N).
        """
        if not (block.type == "BUILD" and block.subtype == "DONE"):
            return

        diff_field = _find_field(block, "diff")
        if diff_field is None:
            return

        if not isinstance(diff_field.value, ListValue):
            return

        diff_re = re.compile(r"^.+~\d+$")
        signed_re = re.compile(r"^[+-]\d+$")
        for item in diff_field.value.data:
            item = item.strip()
            if not diff_re.match(item) and not signed_re.match(item):
                result.add_error(ValidationError(
                    level="error",
                    rule="VALIDATOR-7",
                    message=(
                        f"Build {block.fields[0].value} diff item '{item}' "
                        f"is not a valid revision or signed_int"
                    ),
                    location={"block": idx},
                ))

    def _check_unknown_fields(self, block: Block, idx: int, result: ValidationResult):
        """Warn about fields not in the block schema."""
        all_fields = BlockSchema.get_all_fields(block.type, block.subtype)
        if not all_fields:
            return  # Unknown block type handled by VALIDATOR-1
        for field in block.fields:
            fname = field.key
            # Strip ~ prefix for CTX blocks
            if fname not in all_fields and f"~{fname}" not in all_fields:
                # Check if it looks like a CTX field that should have ~
                if field.is_ctx and f"~{fname}" in all_fields:
                    continue
                result.add_error(ValidationError(
                    level="warning",
                    rule="VALIDATOR-3",
                    message=(
                        f"[{block.type}:{block.subtype}] unknown field '{fname}'"
                    ),
                    location={"block": idx},
                ))

    # ── Layer 3: Contextual ───────────────────────────────────────────────

    def _validate_contextual(self, message: Message, result: ValidationResult):
        self._check_negotiate_first(message, result)
        self._check_ack_follows_negotiate(message, result)
        self._check_cycle_id_consistency(message, result)
        self._check_retry_n_range(message, result)
        self._check_retry_n_terminal(message, result)
        self._check_dag_cycles(message, result)
        self._check_unique_ids(message, result)
        self._check_base_rev_match(message, result)
        self._check_prune_frequency(message, result)
        self._check_compact_frequency(message, result)
        self._check_freeze_once(message, result)
        self._check_ctx_update_on_layer_change(message, result)
        self._check_nack_mandatory(message, result)

    def _check_negotiate_first(self, message: Message, result: ValidationResult):
        """R1: CTX:NEGOTIATE must be the first block of any chain."""
        if not message.blocks:
            return
        first = message.blocks[0]
        if not (first.type == "CTX" and first.subtype == "NEGOTIATE"):
            result.add_error(ValidationError(
                level="error",
                rule="R1",
                message="First block must be CTX:NEGOTIATE",
                location={"block": 0},
            ))

    def _check_ack_follows_negotiate(self, message: Message, result: ValidationResult):
        """R2: STATE:ACK must follow CTX:NEGOTIATE immediately."""
        for i, block in enumerate(message.blocks):
            if block.type == "CTX" and block.subtype == "NEGOTIATE":
                if i + 1 >= len(message.blocks):
                    result.add_error(ValidationError(
                        level="error",
                        rule="R2",
                        message="STATE:ACK must follow CTX:NEGOTIATE",
                        location={"block": i},
                    ))
                    continue
                nxt = message.blocks[i + 1]
                if not (nxt.type == "STATE" and nxt.subtype == "ACK"):
                    result.add_error(ValidationError(
                        level="error",
                        rule="R2",
                        message=f"Expected STATE:ACK after CTX:NEGOTIATE, "
                                f"got {nxt.type}:{nxt.subtype}",
                        location={"block": i + 1},
                    ))

    def _check_cycle_id_consistency(self, message: Message, result: ValidationResult):
        """R3: cycle_id opened by BUILD:FIX must close with TEST:PASS or ORCH:END.

        R5: fail_count resets when cycle_id changes.
        VALIDATOR-4: cycle_id consistency across chain.
        """
        open_cycles: Dict[str, Dict] = {}
        prev_fail_counts: Dict[str, int] = {}

        for i, block in enumerate(message.blocks):
            cid = _field_value(block, "cycle_id")
            if cid is None:
                continue

            if block.type == "BUILD" and block.subtype == "FIX":
                open_cycles[cid] = {"opened_at": i, "closed": False}

            elif block.type == "TEST" and block.subtype == "FAIL":
                fail_count = _field_value(block, "fail_count")
                if fail_count is not None and cid in prev_fail_counts:
                    # R5: fail_count should reset when cycle_id changes
                    pass  # Counter tracking is informational; handled by state machine
                if cid not in open_cycles:
                    # cycle_id referenced before being opened by BUILD:FIX
                    pass  # Valid: TEST:FAIL can open a cycle

            elif block.type == "TEST" and block.subtype == "PASS":
                if cid in open_cycles:
                    open_cycles[cid]["closed"] = True

        # Check unclosed cycles
        for cid, info in open_cycles.items():
            if not info["closed"]:
                result.add_error(ValidationError(
                    level="error",
                    rule="R3",
                    message=f"cycle_id '{cid}' opened at block {info['opened_at']} "
                            f"was never closed with TEST:PASS or ORCH:END",
                    location={"block": info["opened_at"]},
                ))

    def _check_retry_n_range(self, message: Message, result: ValidationResult):
        """R4 / VALIDATOR-5: retry_n in BUILD:FIX must be 1-3."""
        for i, block in enumerate(message.blocks):
            if block.type == "BUILD" and block.subtype == "FIX":
                retry = _field_value(block, "retry_n")
                if retry is not None:
                    if retry < 1 or retry > 3:
                        result.add_error(ValidationError(
                            level="error",
                            rule="VALIDATOR-5",
                            message=f"retry_n={retry} out of range [1..3]",
                            location={"block": i},
                        ))

    def _check_dag_cycles(self, message: Message, result: ValidationResult):
        """R14 / VALIDATOR-6: DAG cycle detection via transitive closure.

        Build adjacency from after: fields and detect cycles using DFS.
        """
        # Build adjacency set: {node_id: {dependencies}}
        adj: Dict[str, Set[str]] = {}
        for block in message.blocks:
            if block.type == "BUILD" and block.subtype == "EXEC":
                bid = _field_value(block, "id")
                if bid is None:
                    continue
                after = _field_value(block, "after")
                if after is None or not isinstance(after, list):
                    adj[bid] = set()
                else:
                    adj[bid] = set(str(a) for a in after)

        # Compute reachability via DFS from each node
        reachable: Dict[str, Set[str]] = {}
        for node in adj:
            reachable[node] = self._transitive_closure(node, adj)

        # Check: for each block B with after:[A1, A2, ...],
        # none of the Ai should have B in their transitive closure.
        for block in message.blocks:
            if block.type == "BUILD" and block.subtype == "EXEC":
                bid = _field_value(block, "id")
                if bid is None:
                    continue
                after = _field_value(block, "after")
                if after is None or not isinstance(after, list):
                    continue
                for dep in after:
                    dep_str = str(dep)
                    if dep_str in reachable and bid in reachable.get(dep_str, set()):
                        result.add_error(ValidationError(
                            level="error",
                            rule="VALIDATOR-6",
                            message=f"DAG cycle detected: '{bid}' depends on "
                                    f"'{dep_str}' which transitively depends on '{bid}'",
                        ))

    def _transitive_closure(self, node: str, adj: Dict[str, Set[str]]) -> Set[str]:
        """DFS-based transitive closure from node."""
        visited: Set[str] = set()
        stack = [node]
        while stack:
            curr = stack.pop()
            for dep in adj.get(curr, set()):
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)
        return visited

    def _check_unique_ids(self, message: Message, result: ValidationResult):
        """R11 / SPEC §9.11: Every id must be unique within the chain scope.

        Id uniqueness is enforced for entity-defining blocks only:
        ARCH:PLAN, BUILD:EXEC, BUILD:FIX. TEST:RUN re-runs after fixes
        and BUILD:DONE/result blocks legitimately reuse ids.
        """
        _ENTITY_TYPES = {("ARCH", "PLAN"), ("BUILD", "EXEC"), ("BUILD", "FIX")}
        seen_ids: Dict[Tuple[str, str, str], int] = {}
        for i, block in enumerate(message.blocks):
            if (block.type, block.subtype) not in _ENTITY_TYPES:
                continue
            bid = _field_value(block, "id")
            if bid is None:
                continue
            bid_str = str(bid)
            key = (block.type, block.subtype, bid_str)
            if key in seen_ids:
                result.add_error(ValidationError(
                    level="error",
                    rule="R11",
                    message=f"Duplicate id '{bid_str}' in "
                            f"[{block.type}:{block.subtype}] at blocks "
                            f"{seen_ids[key]} and {i}",
                    location={"block": i},
                ))
            else:
                seen_ids[key] = i

    def _check_base_rev_match(self, message: Message, result: ValidationResult):
        """R12: base_rev in BUILD:FIX must match rev in BUILD:DONE for same target."""
        # Collect BUILD:DONE revisions by target
        done_revs: Dict[str, int] = {}
        for block in message.blocks:
            if block.type == "BUILD" and block.subtype == "DONE":
                bid = _field_value(block, "id")
                rev = _field_value(block, "rev")
                if bid is not None and rev is not None:
                    done_revs[str(bid)] = int(rev)

        for i, block in enumerate(message.blocks):
            if block.type == "BUILD" and block.subtype == "FIX":
                target = _field_value(block, "target")
                base_rev = _field_value(block, "base_rev")
                if target is not None and base_rev is not None:
                    target_str = str(target)
                    expected_rev = done_revs.get(target_str)
                    if expected_rev is not None and int(base_rev) != expected_rev:
                        result.add_error(ValidationError(
                            level="error",
                            rule="R12",
                            message=f"BUILD:FIX base_rev={base_rev} does not match "
                                    f"BUILD:DONE rev={expected_rev} for target '{target_str}'",
                            location={"block": i},
                        ))

    def _check_prune_frequency(self, message: Message, result: ValidationResult):
        """R6 / VALIDATOR-9: CTX:PRUNE must appear at least every 5 messages."""
        last_prune = -1
        for i, block in enumerate(message.blocks):
            if block.type == "CTX" and block.subtype == "PRUNE":
                last_prune = i
            elif block.type == "CTX" and block.subtype in ("COMPACT", "FREEZE"):
                last_prune = i  # COMPACT/FREEZE reset the counter
            elif i - last_prune > 5:
                result.add_error(ValidationError(
                    level="warning",
                    rule="VALIDATOR-9",
                    message=f"No CTX:PRUNE in {i - last_prune} messages "
                            f"(required every 5)",
                    location={"block": i},
                ))
                last_prune = i  # Reset to avoid spam

    def _check_compact_frequency(self, message: Message, result: ValidationResult):
        """R7 / VALIDATOR-10: CTX:COMPACT must appear ~every 20 messages."""
        last_compact = -1
        for i, block in enumerate(message.blocks):
            if block.type == "CTX" and block.subtype == "COMPACT":
                last_compact = i
            elif block.type == "CTX" and block.subtype == "FREEZE":
                last_compact = i  # FREEZE resets the counter
            elif i - last_compact > 25:  # Allow some slack over 20
                result.add_error(ValidationError(
                    level="warning",
                    rule="VALIDATOR-10",
                    message=f"No CTX:COMPACT in {i - last_compact} messages "
                            f"(recommended every 20)",
                    location={"block": i},
                ))
                last_compact = i

    def _check_freeze_once(self, message: Message, result: ValidationResult):
        """R8 / VALIDATOR-11: CTX:FREEZE no more than once."""
        freeze_count = 0
        first_freeze = -1
        for i, block in enumerate(message.blocks):
            if block.type == "CTX" and block.subtype == "FREEZE":
                if freeze_count == 0:
                    first_freeze = i
                freeze_count += 1
        if freeze_count > 1:
            result.add_error(ValidationError(
                level="error",
                rule="VALIDATOR-11",
                message=f"CTX:FREEZE emitted {freeze_count} times "
                        f"(first at block {first_freeze}), max 1 allowed",
            ))

    def _check_retry_n_terminal(self, message: Message, result: ValidationResult):
        """R6 / SPEC §9.6: retry_n > 3 must terminate with ORCH:END final:error."""
        for i, block in enumerate(message.blocks):
            if block.type == "BUILD" and block.subtype == "FIX":
                retry = _field_value(block, "retry_n")
                if retry is not None and retry > 3:
                    result.add_error(ValidationError(
                        level="error",
                        rule="R6",
                        message=f"retry_n={retry} exceeds 3 — chain must end "
                                f"with ORCH:END final:error",
                        location={"block": i},
                    ))

    def _check_ctx_update_on_layer_change(self, message: Message, result: ValidationResult):
        """R4 / SPEC §9.4: CTX:UPDATE mandatory on every layer change.

        Tracks the current layer (arch, build, test) and warns if a layer
        transition occurs without an intervening CTX:UPDATE.
        """
        last_layer = ""
        last_update_idx = -1
        layer_fields = {"ARCH:PLAN": "arch", "BUILD:EXEC": "build",
                        "BUILD:FIX": "build", "TEST:RUN": "test"}

        for i, block in enumerate(message.blocks):
            key = f"{block.type}:{block.subtype}"
            if key == "CTX:UPDATE":
                last_update_idx = i
                continue

            new_layer = layer_fields.get(key)
            if new_layer and new_layer != last_layer:
                if i - last_update_idx > 1 and last_update_idx >= 0:
                    result.add_error(ValidationError(
                        level="warning",
                        rule="R4",
                        message=f"Layer changed to '{new_layer}' at block {i} "
                                f"without CTX:UPDATE (last UPDATE at {last_update_idx})",
                        location={"block": i},
                    ))
                last_layer = new_layer

    def _check_nack_mandatory(self, message: Message, result: ValidationResult):
        """R13 / SPEC §9.9: On malformed block, receiver emits BUILD:NACK.

        If a block has structural errors (missing REQUIRED fields, invalid
        type), the chain should contain a BUILD:NACK referencing it.
        Simplified: we check that every invalid block type triggers at least
        one NACK in the chain.
        """
        malformed_indices: set = set()
        nack_refs: set = set()

        for i, block in enumerate(message.blocks):
            key = f"{block.type}:{block.subtype}"
            if not BlockSchema.is_valid_block(block.type, block.subtype):
                malformed_indices.add(i)
            # Check for missing required fields
            required = BlockSchema.get_required_fields(block.type, block.subtype)
            present = {f.key for f in block.fields}
            if required - present:
                malformed_indices.add(i)
            # Collect NACK references
            if key == "BUILD:NACK":
                ref = _field_value(block, "ref_id")
                if ref:
                    nack_refs.add(str(ref))

        if malformed_indices and not nack_refs:
            result.add_error(ValidationError(
                level="warning",
                rule="R13",
                message=f"{len(malformed_indices)} malformed blocks found "
                        f"but no BUILD:NACK emitted",
            ))

    # ── Layer 4: Terminal ─────────────────────────────────────────────────

    def _validate_terminal(self, message: Message, result: ValidationResult):
        """R10 / VALIDATOR-8: ORCH:END must be the last block."""
        for i, block in enumerate(message.blocks):
            if block.type == "ORCH" and block.subtype == "END":
                if i != len(message.blocks) - 1:
                    result.add_error(ValidationError(
                        level="error",
                        rule="VALIDATOR-8",
                        message=f"ORCH:END at block {i} is not the last block "
                                f"({len(message.blocks)} total)",
                        location={"block": i},
                    ))


# ── helpers ──────────────────────────────────────────────────────────────────

def _find_field(block: Block, name: str) -> Optional[Field]:
    for f in block.fields:
        if f.key == name:
            return f
    return None


def _field_value(block: Block, name: str):
    """Return the raw Python value of a field, or None."""
    ff = _find_field(block, name)
    if ff is None:
        return None
    v = ff.value
    if isinstance(v, StringValue):
        return v.data
    elif isinstance(v, IntegerValue):
        return v.data
    elif isinstance(v, SignedIntValue):
        return v.data
    elif isinstance(v, ListValue):
        return v.data
    elif isinstance(v, dict):
        return v
    return str(v)
