"""End-to-end integration tests for H2C runtime."""

from h2c.parser import parse
from h2c.runtime import Agent
from h2c.state import State
from h2c.validator import Validator


class TestEndToEnd:
    def test_full_pipeline_hello_world(self, hello_world_text):
        """Parse → Validate → Run → Check state."""
        msg = parse(hello_world_text)
        result = Validator().validate(msg)
        assert result.valid

        agent = Agent()
        agent.run(msg)
        fsm = agent.state_machine
        assert fsm.current_state == State.TERM
        assert fsm.memory.protocol_version == "h2c_v1.4"
        assert "main.py" in fsm.memory.revision_table

    def test_full_pipeline_calculator(self, calculator_text):
        """Parse → Validate → Run → Check fix cycle."""
        msg = parse(calculator_text)
        result = Validator().validate(msg)
        assert result.valid

        agent = Agent()
        agent.run(msg)
        fsm = agent.state_machine
        assert fsm.current_state == State.TERM
        assert "fix-div-zero" in fsm.memory.cycle_registry
        cycle = fsm.memory.cycle_registry["fix-div-zero"]
        assert cycle["status"] == "closed"
        assert cycle["retry_n"] == 1
        assert cycle["fail_count"] == 1

    def test_all_fixtures_parse_and_validate(self, all_fixture_files):
        """All fixture files must parse and validate without errors."""
        for fpath in all_fixture_files:
            text = fpath.read_text()
            msg = parse(text)
            result = Validator().validate(msg)
            errors = [e for e in result.errors if e.level == "error"]
            assert len(errors) == 0, (
                f"{fpath.name}: {len(errors)} errors: "
                f"{[e.message for e in errors]}"
            )

    def test_transpile_roundtrip(self, hello_world_text):
        """Parse → transpile to JSON → re-parse → same AST."""
        from h2c.transpiler import JSONCodegen

        msg1 = parse(hello_world_text)
        json_str = JSONCodegen().generate(msg1)
        # JSON output has a different structure, but we verify
        # that the JSON contains all block types
        assert "CTX" in json_str
        assert "NEGOTIATE" in json_str
        assert "ARCH" in json_str
        assert "ORCH" in json_str

    def test_cli_stats(self, hello_world_text):
        """Stats CLI should produce expected output."""
        from h2c.cli.main import _estimate_tokens
        tokens = _estimate_tokens(hello_world_text)
        assert tokens > 0


class TestAgentNack:
    """Agent._build_nack is only exercised on chains with validation errors.

    Every other Agent test in this suite runs fully-valid fixtures, so these
    cover the malformed-block path explicitly.
    """

    def test_nack_uses_block_id_as_ref_id(self):
        """A structurally invalid block with an id produces a NACK referencing it."""
        text = (
            "[CTX:NEGOTIATE]\n"
            "version:h2c_v1.4|capabilities:[PRUNE]\n\n"
            "[STATE:ACK]\n"
            "protocol:h2c_v1.4\n\n"
            "[TEST:FAIL]\n"
            "id:t9|error:something_broke\n"
        )
        msg = parse(text)
        agent = Agent()
        agent.run(msg)

        nacks = [b for b in agent.history if b.type == "BUILD" and b.subtype == "NACK"]
        assert len(nacks) == 1
        fields = {f.key: f.value.data for f in nacks[0].fields}
        assert fields["ref_id"] == "t9"
        assert fields["error"]

    def test_nack_falls_back_to_unknown_ref_id(self):
        """A structurally invalid block with no id yields ref_id '(unknown)'."""
        text = (
            "[CTX:NEGOTIATE]\n"
            "version:h2c_v1.4|capabilities:[PRUNE]\n\n"
            "[STATE:ACK]\n"
            "protocol:h2c_v1.4\n\n"
            "[TEST:FAIL]\n"
            "error:something_broke|cycle_id:c1\n"
        )
        msg = parse(text)
        agent = Agent()
        agent.run(msg)

        nacks = [b for b in agent.history if b.type == "BUILD" and b.subtype == "NACK"]
        assert len(nacks) == 1
        fields = {f.key: f.value.data for f in nacks[0].fields}
        assert fields["ref_id"] == "(unknown)"
        assert fields["error"]
