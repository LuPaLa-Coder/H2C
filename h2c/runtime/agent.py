"""H2C Agent Runtime.

Implements the agent execution cycle from
docs/architecture/agent-runtime.md section 1:

    Wait → Parse → Validate → Execute → Emit
"""

from typing import List, Optional, Set as SetType

from h2c.parser.ast import Block, Message
from h2c.parser.parser import parse as parse_text
from h2c.validator.validator import Validator
from h2c.state.fsm import StateMachine, Opcode
from h2c.state.opcodes import SideEffectApplier
from h2c.state.memory import GlobalMemory
from h2c.context.manager import ContextManager
from h2c.runtime.dispatcher import Dispatcher
from h2c.runtime.transport import Transport, FileTransport


class Agent:
    """H2C Agent — executes the Wait→Parse→Validate→Execute→Emit cycle."""

    def __init__(
        self,
        role: str = "orchestrator",
        state_machine: Optional[StateMachine] = None,
        context: Optional[ContextManager] = None,
        validator: Optional[Validator] = None,
        transport: Optional[Transport] = None,
    ):
        self.role = role
        self._fsm = state_machine or StateMachine()
        self._ctx = context or ContextManager(memory=self._fsm.memory)
        self._validator = validator or Validator()
        self._transport = transport
        self._dispatcher = Dispatcher(self._fsm, self._ctx)
        self._history: List[Block] = []

    @property
    def state_machine(self) -> StateMachine:
        return self._fsm

    @property
    def context(self) -> ContextManager:
        return self._ctx

    @property
    def history(self) -> List[Block]:
        return self._history

    def run_file(self, filepath: str) -> Message:
        """Process an entire .h2c file through the agent cycle.

        Returns the complete message (all input blocks).
        """
        transport = FileTransport(filepath)
        message = transport.receive_message()
        if message is None:
            return Message()

        return self.run(message)

    def run(self, message: Message) -> Message:
        """Run the agent execution cycle on a pre-parsed Message.

        Returns the input Message (the agent processes but doesn't
        modify — it only tracks state transitions and side effects).
        """
        # Validate the full chain first
        validation = self._validator.validate(message)
        # Identify blocks with structural/syntactic errors
        invalid_indices: set = set()
        for e in validation.errors:
            if e.level == "error" and e.location and "block" in e.location:
                invalid_indices.add(e.location["block"])

        for i, block in enumerate(message.blocks):
            if i in invalid_indices:
                nack = self._build_nack(block, validation)
                if nack:
                    self._history.append(nack)
                continue

            # Execute (dispatch + state transition + side effects)
            response = self._dispatcher.dispatch(block, i)

            # Emit (track in history)
            self._history.append(block)
            if response:
                self._history.append(response)

            # Context management: PRUNE every 5, COMPACT every 20, FREEZE at ~100
            self._manage_context()

        return message

    def _manage_context(self):
        """Emit PRUNE, COMPACT, or FREEZE blocks as needed per SPEC §9.2-9.4."""
        msg_n = self._fsm.memory.msg_counter

        # FREEZE at ~100 messages (SPEC §9.4)
        if self._ctx.should_freeze():
            snapshot = [
                f"{f}~{r}" for f, r in self._fsm.memory.revision_table.items()
            ]
            freeze_block = self._ctx.build_freeze_block(
                snapshot=snapshot if snapshot else ["(empty)"],
                baseline=msg_n,
            )
            self._fsm.transition(freeze_block)
            self._ctx.reset_after_freeze()
            self._history.append(freeze_block)
            return

        # COMPACT every 20 messages (SPEC §9.3)
        if self._ctx.should_compact():
            keep_active = [
                f"{f}~{r}" for f, r in self._fsm.memory.revision_table.items()
            ]
            compact_start = max(0, msg_n - 20)
            compact_block = self._ctx.build_compact_block(
                summary=[f"layer={self._fsm.memory.context_state.get('layer', '?')}"],
                keep_active=keep_active if keep_active else ["(none)"],
                pruned_history=f"msg{compact_start}_to_{msg_n}",
            )
            self._fsm.transition(compact_block)
            self._ctx.reset_after_compact()
            self._history.append(compact_block)
            return

        # PRUNE every 5 messages (SPEC §9.2)
        if self._ctx.should_prune():
            prunable = self._ctx.get_prunable_ids(self._history)
            if prunable:
                keep_ids = _collect_keep_ids(self._history, prunable, max_keep=5)
                prune_block = self._ctx.build_prune_block(
                    keep=keep_ids,
                    pruned=prunable[:10],
                    reason=f"prune_at_msg_{msg_n}",
                )
                self._fsm.transition(prune_block)
                self._ctx.reset_after_prune()
                self._history.append(prune_block)

    def process_message(self, input_text: str) -> str:
        """Process a single H2C text message and return the output.

        This is the single-shot variant of the run cycle.
        """
        message = parse_text(input_text)
        self.run(message)
        # Return the last history block as output
        if self._history:
            last = self._history[-1]
            return f"[{last.type}:{last.subtype}]"
        return ""

    def _build_nack(self, block: Block, result) -> Optional[Block]:
        """Build a BUILD:NACK block for a malformed block."""
        from h2c.parser.ast import Field, StringValue

        errors = [e.message for e in result.errors if e.level == "error"]
        if not errors:
            return None

        ref_id = "(unknown)"
        for f in block.fields:
            if f.key == "id" and hasattr(f.value, 'data'):
                ref_id = f.value.data
                break

        return Block(
            type="BUILD",
            subtype="NACK",
            fields=[
                Field(key="ref_id", value=StringValue(data=ref_id)),
                Field(key="error", value=StringValue(data="; ".join(errors[:3]))),
            ],
        )


def _collect_keep_ids(history: List[Block], prunable: List[str], max_keep: int = 5) -> List[str]:
    """Collect ids to keep during PRUNE per SPEC §5.3 pruning rules.

    Must include: latest ARCH:PLAN, all open BUILD:FIX, latest COMPACT.
    """
    keep: List[str] = []
    for block in history:
        bid = None
        for f in block.fields:
            if f.key == "id" and hasattr(f.value, 'data'):
                bid = str(f.value.data)
                break
        if bid and bid not in prunable and bid not in keep:
            keep.append(bid)
    return keep[:max_keep]


def run_chain(filepath: str) -> dict:
    """Convenience: run an .h2c file through the agent and return stats."""
    agent = Agent()
    message = agent.run_file(filepath)
    fsm = agent.state_machine
    return {
        "blocks_processed": len(message.blocks),
        "final_state": fsm.current_state.value,
        "msg_counter": fsm.memory.msg_counter,
        "revision_table": dict(fsm.memory.revision_table),
        "cycle_registry": dict(fsm.memory.cycle_registry),
        "findings_count": len(fsm.memory.findings),
    }
