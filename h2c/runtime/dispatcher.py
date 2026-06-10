"""H2C Dispatcher — routes blocks to handlers.

Implements the routing table from docs/architecture/agent-runtime.md section 2.
"""

from typing import Callable, Dict, Optional

from h2c.parser.ast import Block, Message
from h2c.state.fsm import StateMachine
from h2c.state.opcodes import SideEffectApplier
from h2c.state.memory import GlobalMemory
from h2c.context.manager import ContextManager


class Dispatcher:
    """Routes H2C blocks to registered handlers based on type/subtype."""

    def __init__(
        self,
        state_machine: StateMachine,
        context: ContextManager,
    ):
        self._fsm = state_machine
        self._ctx = context
        self._handlers: Dict[str, Callable] = {}
        self._register_defaults()

    def dispatch(self, block: Block, block_index: int = -1) -> Optional[Block]:
        """Route a block to its handler and return any response block.

        Returns None if no response block is generated.
        """
        key = f"{block.type}:{block.subtype}"
        handler = self._handlers.get(key)
        if handler:
            result = handler(block)
        else:
            result = None

        # Apply state transition and side effects
        self._fsm.transition(block)
        opcode = StateMachine.block_to_opcode(block)
        if opcode:
            SideEffectApplier.apply(opcode, block, self._fsm.memory)

        # Track for context management
        self._ctx.track_block(block, block_index)

        return result

    def register(self, type_subtype: str, handler: Callable):
        """Register a custom handler for a block type."""
        self._handlers[type_subtype] = handler

    def _register_defaults(self):
        """Register default handlers that implement the routing table."""
        self._handlers["CTX:NEGOTIATE"] = self._handle_negotiate
        self._handlers["STATE:ACK"] = self._handle_ack
        self._handlers["BUILD:EXEC"] = self._handle_pass_through
        self._handlers["BUILD:DONE"] = self._handle_pass_through
        self._handlers["BUILD:FIX"] = self._handle_pass_through
        self._handlers["BUILD:REVERT"] = self._handle_pass_through
        self._handlers["BUILD:NACK"] = self._handle_nack
        self._handlers["TEST:RUN"] = self._handle_pass_through
        self._handlers["TEST:PASS"] = self._handle_pass_through
        self._handlers["TEST:FAIL"] = self._handle_pass_through
        self._handlers["CTX:PRUNE"] = self._handle_prune
        self._handlers["CTX:COMPACT"] = self._handle_compact
        self._handlers["CTX:FREEZE"] = self._handle_freeze
        self._handlers["STATE:FINDINGS"] = self._handle_pass_through
        self._handlers["ORCH:END"] = self._handle_end

    def _handle_negotiate(self, block: Block) -> Optional[Block]:
        return None

    def _handle_ack(self, block: Block) -> Optional[Block]:
        return None

    def _handle_pass_through(self, block: Block) -> Optional[Block]:
        return None

    def _handle_nack(self, block: Block) -> Optional[Block]:
        return None

    def _handle_prune(self, block: Block) -> Optional[Block]:
        self._ctx.reset_after_prune()
        return None

    def _handle_compact(self, block: Block) -> Optional[Block]:
        self._ctx.reset_after_compact()
        return None

    def _handle_freeze(self, block: Block) -> Optional[Block]:
        self._ctx.reset_after_freeze()
        return None

    def _handle_end(self, block: Block) -> Optional[Block]:
        return None
