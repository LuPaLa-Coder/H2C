"""Tests for H2C Context Manager, State Machine, and Side Effects."""

import pytest
from h2c.parser import parse
from h2c.state.fsm import StateMachine, State, Opcode
from h2c.state.memory import GlobalMemory
from h2c.state.opcodes import SideEffectApplier
from h2c.context.manager import ContextManager
from h2c.context.rules import PRUNE_INTERVAL, COMPACT_INTERVAL, FREEZE_THRESHOLD


class TestStateMachine:
    def test_initial_state(self):
        fsm = StateMachine()
        assert fsm.current_state == State.INIT

    def test_negotiate_transition(self):
        fsm = StateMachine()
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n")
        fsm.transition(msg.blocks[0])
        assert fsm.current_state == State.HANDSHAKE

    def test_ack_transition(self):
        fsm = StateMachine()
        fsm.transition(parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n").blocks[0])
        fsm.transition(parse("[STATE:ACK]\nprotocol:h2c_v1.4\n").blocks[0])
        assert fsm.current_state == State.ACKED

    def test_full_chain_to_term(self, hello_world_text):
        fsm = StateMachine()
        msg = parse(hello_world_text)
        for block in msg.blocks:
            fsm.transition(block)
        assert fsm.current_state == State.TERM

    def test_build_fix_cycle(self):
        fsm = StateMachine()
        blocks = [
            "[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n",
            "[STATE:ACK]\nprotocol:h2c_v1.4\n",
            "[ARCH:PLAN]\nid:calc|fw:python3\n",
            "[BUILD:EXEC]\nid:m1|target:calc.py\n",
            "[BUILD:DONE]\nid:m1|diff:[calc.py~1,+10]|rev:1\n",
            "[TEST:RUN]\nid:t1|cmd:pytest\n",
            "[TEST:FAIL]\nid:t1|error:bug|cycle_id:c1|fail_count:1\n",
            "[BUILD:FIX]\nid:f1|target:calc.py|base_rev:1|desc:fix|cycle_id:c1|retry_n:1\n",
        ]
        for text in blocks:
            fsm.transition(parse(text).blocks[0])
        assert fsm.current_state == State.FIXING

    def test_opcode_mapping(self):
        msg = parse("[ARCH:PLAN]\nid:x|fw:py\n")
        opcode = StateMachine.block_to_opcode(msg.blocks[0])
        assert opcode == Opcode.ARCH_PLAN

    def test_opcode_mapping_unknown(self):
        from h2c.parser.ast import Block
        block = Block(type="UNKNOWN", subtype="THING", fields=[])
        opcode = StateMachine.block_to_opcode(block)
        assert opcode is None

    def test_is_terminal(self):
        fsm = StateMachine()
        assert not fsm.is_terminal()
        msg = parse("[ORCH:END]\nfinal:complete\n")
        fsm.transition(msg.blocks[0])
        assert fsm.is_terminal()

    def test_reset(self):
        fsm = StateMachine()
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n")
        fsm.transition(msg.blocks[0])
        assert fsm.current_state != State.INIT
        fsm.reset()
        assert fsm.current_state == State.INIT
        assert fsm.memory.msg_counter == 0

    def test_context_management_transitions(self):
        fsm = StateMachine()
        # Setup
        for text in [
            "[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n",
            "[STATE:ACK]\nprotocol:h2c_v1.4\n",
        ]:
            fsm.transition(parse(text).blocks[0])

        # COMPACT
        msg = parse("[CTX:COMPACT]\nsummary:[layer=build]|keep_active:[main.py]|pruned_history:msg1_to_20\n")
        fsm.transition(msg.blocks[0])
        assert fsm.current_state == State.COMPACT

        # FREEZE from COMPACT
        msg = parse("[CTX:FREEZE]\nsnapshot:[main.py~1]|baseline:100\n")
        fsm.transition(msg.blocks[0])
        assert fsm.current_state == State.FROZEN


class TestSideEffectApplier:
    def test_negotiate_side_effect(self):
        memory = GlobalMemory()
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE,COMPACT]\n")
        opcode = Opcode.CTX_NEGOTIATE
        SideEffectApplier.apply(opcode, msg.blocks[0], memory)
        assert memory.protocol_version == "h2c_v1.4"
        assert "PRUNE" in memory.capabilities
        assert "COMPACT" in memory.capabilities

    def test_arch_plan_side_effect(self):
        memory = GlobalMemory()
        msg = parse("[ARCH:PLAN]\nid:myapp|fw:python3\n")
        SideEffectApplier.apply(Opcode.ARCH_PLAN, msg.blocks[0], memory)
        assert memory.context_state["layer"] == "arch"
        assert memory.context_state["plan_id"] == "myapp"

    def test_build_done_registers_revision(self):
        memory = GlobalMemory()
        msg = parse("[BUILD:DONE]\nid:m1|diff:[main.py~3,+20]|rev:3\n")
        SideEffectApplier.apply(Opcode.BUILD_DONE, msg.blocks[0], memory)
        assert "main.py" in memory.revision_table
        assert memory.revision_table["main.py"] == 3

    def test_build_fix_increments_retry(self):
        memory = GlobalMemory()
        msg = parse("[BUILD:FIX]\nid:f1|target:x.py|base_rev:1|desc:fix|cycle_id:c1|retry_n:2\n")
        SideEffectApplier.apply(Opcode.BUILD_FIX, msg.blocks[0], memory)
        assert "c1" in memory.cycle_registry
        assert memory.cycle_registry["c1"]["retry_n"] == 1

    def test_test_fail_increments_fail_count(self):
        memory = GlobalMemory()
        msg = parse("[TEST:FAIL]\nid:t1|error:bug|cycle_id:c1|fail_count:3\n")
        SideEffectApplier.apply(Opcode.TEST_FAIL, msg.blocks[0], memory)
        assert memory.cycle_registry["c1"]["fail_count"] == 1
        assert memory.context_state["status"] == "failed"

    def test_test_pass_closes_cycle(self):
        memory = GlobalMemory()
        # First register and fail
        memory.register_cycle("c1")
        memory.increment_fail("c1")
        msg = parse("[TEST:PASS]\nid:t1|pass_count:10|cycle_id:c1\n")
        SideEffectApplier.apply(Opcode.TEST_PASS, msg.blocks[0], memory)
        assert memory.cycle_registry["c1"]["status"] == "closed"

    def test_state_findings(self):
        memory = GlobalMemory()
        msg = parse("[STATE:FINDINGS]\nid:f1|cause:null_ptr|action:add_check|impact:crash\n")
        SideEffectApplier.apply(Opcode.STATE_FIND, msg.blocks[0], memory)
        assert len(memory.findings) == 1
        assert memory.findings[0]["cause"] == "null_ptr"

    def test_orch_end(self):
        memory = GlobalMemory()
        msg = parse("[ORCH:END]\nfinal:complete\n")
        SideEffectApplier.apply(Opcode.ORCH_END, msg.blocks[0], memory)
        assert memory.context_state["status"] == "complete"

    def test_ctx_prune_resets_counter(self):
        memory = GlobalMemory()
        memory.prune_counter = 10
        msg = parse("[CTX:PRUNE]\nkeep:[a]|pruned:[b]\n")
        SideEffectApplier.apply(Opcode.CTX_PRUNE, msg.blocks[0], memory)
        assert memory.prune_counter == 0

    def test_ctx_compact_resets_counters(self):
        memory = GlobalMemory()
        memory.prune_counter = 10
        memory.compact_counter = 25
        msg = parse("[CTX:COMPACT]\nsummary:[ok]|keep_active:[x.py]|pruned_history:m1_20\n")
        SideEffectApplier.apply(Opcode.CTX_COMPACT, msg.blocks[0], memory)
        assert memory.prune_counter == 0
        assert memory.compact_counter == 0

    def test_ctx_freeze_resets_all(self):
        memory = GlobalMemory()
        memory.prune_counter = 10
        memory.compact_counter = 25
        msg = parse("[CTX:FREEZE]\nsnapshot:[main.py~1]|baseline:100\n")
        SideEffectApplier.apply(Opcode.CTX_FREEZE, msg.blocks[0], memory)
        assert memory.prune_counter == 0
        assert memory.compact_counter == 0

    def test_unknown_opcode_noop(self):
        memory = GlobalMemory()
        # Should not raise
        SideEffectApplier.apply(Opcode.SKILL_PROMPT, None, memory)


class TestContextManager:
    def test_should_prune_after_interval(self):
        ctx = ContextManager()
        assert not ctx.should_prune()
        # Simulate 5 messages
        for _ in range(5):
            ctx.memory.increment_message()
        assert ctx.should_prune()

    def test_should_compact_after_interval(self):
        ctx = ContextManager()
        assert not ctx.should_compact()
        for _ in range(COMPACT_INTERVAL):
            ctx.memory.increment_message()
        assert ctx.should_compact()

    def test_should_freeze_after_threshold(self):
        ctx = ContextManager()
        assert not ctx.should_freeze()
        for _ in range(FREEZE_THRESHOLD):
            ctx.memory.increment_message()
        assert ctx.should_freeze()

    def test_track_done_emission(self):
        ctx = ContextManager()
        msg = parse("[BUILD:DONE]\nid:m1|diff:[x.py~1,+10]|rev:1\n")
        block = msg.blocks[0]
        ctx.track_block(block, 0)
        assert "m1" in ctx._done_emitted

    def test_track_test_outcome(self):
        ctx = ContextManager()
        msg = parse("[TEST:PASS]\nid:t1|pass_count:5\n")
        ctx.track_block(msg.blocks[0], 0)
        assert "t1" in ctx._test_outcomes

    def test_track_cycle(self):
        ctx = ContextManager()
        msg = parse("[BUILD:FIX]\nid:f1|target:x|base_rev:1|desc:fix|cycle_id:c1|retry_n:1\n")
        ctx.track_block(msg.blocks[0], 0)
        assert "c1" in ctx._open_cycles

    def test_build_prune_block(self):
        ctx = ContextManager()
        block = ctx.build_prune_block(keep=["a", "b"], pruned=["c", "d"], reason="test")
        assert block.type == "CTX"
        assert block.subtype == "PRUNE"
        assert len(block.fields) >= 2

    def test_build_compact_block(self):
        ctx = ContextManager()
        block = ctx.build_compact_block(
            summary=["layer=build"], keep_active=["main.py"], pruned_history="msg1_to_20"
        )
        assert block.type == "CTX"
        assert block.subtype == "COMPACT"

    def test_build_freeze_block(self):
        ctx = ContextManager()
        block = ctx.build_freeze_block(snapshot=["main.py~3"], baseline=100)
        assert block.type == "CTX"
        assert block.subtype == "FREEZE"

    def test_prunable_ids(self):
        ctx = ContextManager()
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n")
        ids = ctx.get_prunable_ids(msg.blocks)
        assert isinstance(ids, list)

    def test_reset_after_prune(self):
        ctx = ContextManager()
        ctx.memory.prune_counter = 10
        ctx.reset_after_prune()
        assert ctx.memory.prune_counter == 0

    def test_reset_after_compact(self):
        ctx = ContextManager()
        ctx.memory.prune_counter = 10
        ctx.memory.compact_counter = 25
        ctx.reset_after_compact()
        assert ctx.memory.prune_counter == 0
        assert ctx.memory.compact_counter == 0

    def test_reset_after_freeze(self):
        ctx = ContextManager()
        ctx.memory.prune_counter = 10
        ctx.memory.compact_counter = 25
        ctx.reset_after_freeze()
        assert ctx.memory.prune_counter == 0
        assert ctx.memory.compact_counter == 0


class TestGlobalMemory:
    def test_increment_message_updates_all_counters(self):
        m = GlobalMemory()
        m.increment_message()
        assert m.msg_counter == 1
        assert m.prune_counter == 1
        assert m.compact_counter == 1

    def test_register_cycle(self):
        m = GlobalMemory()
        m.register_cycle("c1")
        assert "c1" in m.cycle_registry
        assert m.cycle_registry["c1"]["status"] == "open"

    def test_increment_fail(self):
        m = GlobalMemory()
        m.increment_fail("c1")
        assert m.cycle_registry["c1"]["fail_count"] == 1

    def test_close_cycle(self):
        m = GlobalMemory()
        m.register_cycle("c1")
        m.close_cycle("c1")
        assert m.cycle_registry["c1"]["status"] == "closed"

    def test_update_revision(self):
        m = GlobalMemory()
        m.update_revision("main.py", 3)
        assert m.revision_table["main.py"] == 3

    def test_add_finding(self):
        m = GlobalMemory()
        m.add_finding({"cause": "bug", "file": "x.py"})
        assert len(m.findings) == 1

    def test_reset_counters(self):
        m = GlobalMemory()
        m.prune_counter = 10
        m.compact_counter = 25
        m.reset_prune_counter()
        assert m.prune_counter == 0
        assert m.compact_counter == 25
        m.reset_compact_counter()
        assert m.compact_counter == 0
        m.prune_counter = 5
        m.compact_counter = 10
        m.reset_all_counters()
        assert m.prune_counter == 0
        assert m.compact_counter == 0

    def test_default_values(self):
        m = GlobalMemory()
        assert m.protocol_version == ""
        assert m.capabilities == []
        assert m.msg_counter == 0
        assert m.revision_table == {}
        assert m.findings == []
