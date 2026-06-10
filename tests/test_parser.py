"""Tests for H2C Parser (Phase 2)."""

import json

from h2c.parser import parse
from h2c.parser.ast import (
    Block, Field, IntegerValue, ListValue, Message, RevisionValue,
    SignedIntValue, StringValue,
)


class TestParser:
    def test_parse_negotiate_ack(self, sample_text):
        msg = parse(sample_text)
        assert len(msg.blocks) == 2
        assert msg.blocks[0].type == "CTX"
        assert msg.blocks[0].subtype == "NEGOTIATE"
        assert msg.blocks[1].type == "STATE"
        assert msg.blocks[1].subtype == "ACK"

    def test_parse_arch_plan(self):
        msg = parse("[ARCH:PLAN]\nid:api|fw:python3|lib:fastapi|notes:[caching]\n")
        block = msg.blocks[0]
        assert block.type == "ARCH"
        assert block.subtype == "PLAN"
        assert len(block.fields) == 4
        assert isinstance(block.fields[0].value, StringValue)

    def test_parse_build_done_with_diff(self):
        msg = parse("[BUILD:DONE]\nid:m1|diff:[main.py~1,+15,config.py~2,-5]|rev:1\n")
        block = msg.blocks[0]
        assert block.type == "BUILD"
        assert block.subtype == "DONE"
        diff = [f for f in block.fields if f.key == "diff"][0]
        assert isinstance(diff.value, ListValue)
        assert len(diff.value.data) == 4

    def test_parse_ctx_fields_have_tilde_prefix(self):
        msg = parse("[CTX:PRIMITIVES]\n~task:build_api|~constraint:rest|~goal:complete\n")
        block = msg.blocks[0]
        task_field = [f for f in block.fields if f.key == "~task"][0]
        assert task_field.is_ctx
        assert task_field.key == "~task"

    def test_parse_fix_cycle(self):
        msg = parse(
            "[BUILD:FIX]\nid:f1|target:calc.py|base_rev:1|desc:fix|cycle_id:c1|retry_n:2\n"
        )
        block = msg.blocks[0]
        assert block.type == "BUILD"
        assert block.subtype == "FIX"
        retry = [f for f in block.fields if f.key == "retry_n"][0]
        assert isinstance(retry.value, IntegerValue)
        assert retry.value.data == 2

    def test_parse_orch_end(self):
        msg = parse("[ORCH:END]\nfinal:complete|est_token:42\n")
        block = msg.blocks[0]
        assert block.type == "ORCH"
        assert block.subtype == "END"

    def test_parse_multiple_blocks(self, hello_world_text):
        msg = parse(hello_world_text)
        assert len(msg.blocks) == 8
        types = [(b.type, b.subtype) for b in msg.blocks]
        assert types[0] == ("CTX", "NEGOTIATE")
        assert types[1] == ("STATE", "ACK")
        assert types[-1] == ("ORCH", "END")

    def test_parse_stress_test(self, stress_text):
        msg = parse(stress_text)
        assert len(msg.blocks) == 130

    def test_json_ast_output(self, hello_world_text):
        msg = parse(hello_world_text)
        ast_json = msg.to_json_ast()
        assert "messages" in ast_json
        assert len(ast_json["messages"]) == 8

    def test_comment_lines_ignored(self):
        msg = parse("# comment 1\n# comment 2\n[ARCH:PLAN]\nid:x|fw:py\n")
        assert len(msg.blocks) == 1
