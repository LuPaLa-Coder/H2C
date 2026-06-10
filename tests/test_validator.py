"""Tests for H2C Validator (Phase 3)."""

from h2c.parser import parse
from h2c.validator import Validator


class TestValidator:
    def test_hello_world_passes(self, hello_world_text):
        msg = parse(hello_world_text)
        result = Validator().validate(msg)
        # May have PRUNE frequency warnings on short chains
        errors = [e for e in result.errors if e.level == "error"]
        assert len(errors) == 0

    def test_calculator_passes(self, calculator_text):
        msg = parse(calculator_text)
        result = Validator().validate(msg)
        errors = [e for e in result.errors if e.level == "error"]
        assert len(errors) == 0

    def test_stress_passes(self, stress_text):
        msg = parse(stress_text)
        result = Validator().validate(msg)
        errors = [e for e in result.errors if e.level == "error"]
        assert len(errors) == 0

    def test_missing_negotiate_first(self):
        msg = parse("[ARCH:PLAN]\nid:x|fw:py\n[ORCH:END]\nfinal:complete\n")
        result = Validator().validate(msg)
        assert not result.valid
        assert any("R1" in e.rule for e in result.errors if e.level == "error")

    def test_missing_required_field(self):
        # ARCH:PLAN requires id and fw
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n[STATE:ACK]\nprotocol:h2c_v1.4\n[ARCH:PLAN]\nid:x\n")
        result = Validator().validate(msg)
        # ARCH:PLAN missing fw
        errs = [e for e in result.errors if e.level == "error"]
        assert any("fw" in e.message.lower() for e in errs)

    def test_retry_n_out_of_range(self):
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n[STATE:ACK]\nprotocol:h2c_v1.4\n[BUILD:FIX]\nid:f1|target:x.py|base_rev:1|desc:fix|cycle_id:c1|retry_n:5\n[ORCH:END]\nfinal:complete\n")
        result = Validator().validate(msg)
        errs = [e for e in result.errors if e.level == "error"]
        assert any("retry_n" in e.message.lower() for e in errs)

    def test_orch_end_not_last(self):
        msg = parse("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE]\n[STATE:ACK]\nprotocol:h2c_v1.4\n[ORCH:END]\nfinal:complete\n[ARCH:PLAN]\nid:x|fw:py\n")
        result = Validator().validate(msg)
        assert not result.valid
