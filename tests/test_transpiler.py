"""Tests for H2C Transpiler modules."""

from h2c.parser import parse
from h2c.transpiler import H2CSerializer, JSONCodegen, MCPCodegen, NLCodegen


class TestNLCodegen:
    def test_arch_plan_to_nl(self):
        msg = parse("[ARCH:PLAN]\nid:myapp|fw:python3|lib:fastapi|auth:jwt|notes:[caching]\n")
        result = NLCodegen().generate(msg)
        assert "myapp" in result
        assert "python3" in result
        assert "fastapi" in result

    def test_build_exec_to_nl(self):
        msg = parse("[BUILD:EXEC]\nid:m1|target:main.py|desc:create_app\n")
        result = NLCodegen().generate(msg)
        assert "m1" in result
        assert "main.py" in result
        assert "create_app" in result

    def test_build_done_to_nl(self):
        msg = parse("[BUILD:DONE]\nid:m1|diff:[main.py~1,+20]|rev:1\n")
        result = NLCodegen().generate(msg)
        assert "completed" in result.lower() or "m1" in result

    def test_test_pass_to_nl(self):
        msg = parse("[TEST:PASS]\nid:t1|pass_count:12\n")
        result = NLCodegen().generate(msg)
        assert "t1" in result
        assert "12" in result

    def test_test_fail_to_nl(self):
        msg = parse("[TEST:FAIL]\nid:t1|error:bug|cycle_id:c1|fail_count:2\n")
        result = NLCodegen().generate(msg)
        assert "t1" in result
        assert "bug" in result
        assert "c1" in result

    def test_negotiate_to_nl(self):
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE,COMPACT]\n")
        result = NLCodegen().generate(msg)
        assert "h2c_v1.4" in result
        assert "PRUNE" in result

    def test_complete_chain(self, hello_world_text):
        msg = parse(hello_world_text)
        result = NLCodegen().generate(msg)
        assert "CTX" in result or "Handshake" in result or "architectural" in result.lower()

    def test_fallback_unknown_block(self):
        msg = parse("[SKILL:PROMPT]\nid:test|role:tester|activation:manual\n")
        result = NLCodegen().generate(msg)
        assert "SKILL:PROMPT" in result


class TestJSONCodegen:
    def test_arch_plan_to_json(self):
        msg = parse("[ARCH:PLAN]\nid:myapp|fw:python3|lib:fastapi\n")
        result = JSONCodegen().generate(msg)
        assert '"protocol"' in result
        assert '"myapp"' in result
        assert '"python3"' in result

    def test_full_chain_json(self, hello_world_text):
        msg = parse(hello_world_text)
        result = JSONCodegen().generate(msg)
        assert '"protocol"' in result
        assert '"h2c_v1.4"' in result
        assert '"messages"' in result

    def test_revision_in_list(self):
        msg = parse("[BUILD:DONE]\nid:m1|diff:[main.py~1,+20]|rev:1\n")
        result = JSONCodegen().generate(msg)
        assert '"file"' in result
        assert '"rev"' in result


class TestMCPCodegen:
    def test_single_block_to_mcp(self):
        msg = parse("[ARCH:PLAN]\nid:myapp|fw:python3\n")
        block = msg.blocks[0]
        result = MCPCodegen().generate(block, request_id=1)
        assert result["jsonrpc"] == "2.0"
        assert result["method"] == "tools/call"
        assert result["params"]["name"] == "h2c_arch_plan"
        assert result["id"] == 1

    def test_batch_to_mcp(self):
        msg = parse(
            "[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n\n"
            "[STATE:ACK]\nprotocol:h2c_v1.4\n"
        )
        result = MCPCodegen().generate_batch(msg)
        assert len(result) == 2
        assert result[0]["params"]["name"] == "h2c_ctx_negotiate"
        assert result[1]["params"]["name"] == "h2c_state_ack"

    def test_mcp_arguments(self):
        msg = parse("[BUILD:FIX]\nid:f1|target:calc.py|base_rev:1|desc:fix|cycle_id:c1|retry_n:2\n")
        block = msg.blocks[0]
        result = MCPCodegen().generate(block)
        args = result["params"]["arguments"]
        assert args["id"] == "f1"
        assert args["target"] == "calc.py"
        assert args["cycle_id"] == "c1"


class TestH2CSerializer:
    def test_roundtrip_simple(self):
        text = "[ARCH:PLAN]\nid:myapp|fw:python3|lib:fastapi\n"
        msg = parse(text)
        result = H2CSerializer().serialize(msg)
        assert "[ARCH:PLAN]" in result
        assert "id:myapp" in result
        assert "fw:python3" in result

    def test_roundtrip_with_list(self):
        text = "[BUILD:DONE]\nid:m1|diff:[main.py~1,+20]|rev:1\n"
        msg = parse(text)
        result = H2CSerializer().serialize(msg)
        assert "[BUILD:DONE]" in result
        assert "[main.py~1,+20]" in result

    def test_roundtrip_with_revision(self):
        text = "[CTX:FREEZE]\nsnapshot:[main.py~3]|baseline:100\n"
        msg = parse(text)
        result = H2CSerializer().serialize(msg)
        assert "snapshot:[main.py~3]" in result
        assert "baseline:100" in result

    def test_roundtrip_complete_chain(self, hello_world_text):
        msg = parse(hello_world_text)
        result = H2CSerializer().serialize(msg)
        # Should contain key blocks
        assert "CTX:NEGOTIATE" in result
        assert "STATE:ACK" in result
        assert "ORCH:END" in result

    def test_serialize_empty_message(self):
        from h2c.parser.ast import Message
        result = H2CSerializer().serialize(Message())
        assert result == ""

    def test_convenience_functions(self):
        from h2c.transpiler import serialize, serialize_block
        msg = parse("[ARCH:PLAN]\nid:x|fw:py\n")
        assert "ARCH:PLAN" in serialize(msg)
        assert "ARCH:PLAN" in serialize_block(msg.blocks[0])
