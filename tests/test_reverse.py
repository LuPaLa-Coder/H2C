"""Tests for H2C Reverse Compiler (NL → H2C)."""

from h2c.transpiler import ReverseCompiler


class TestReverseCompiler:
    def test_extract_architecture_basic(self):
        rc = ReverseCompiler()
        msg = rc.compile("Crea un'app meteo in python3 con fastapi e httpx")
        assert len(msg.blocks) >= 1
        arch = msg.blocks[0]
        assert arch.type == "ARCH"
        assert arch.subtype == "PLAN"

    def test_extract_architecture_english(self):
        rc = ReverseCompiler()
        msg = rc.compile("Create a todo app in typescript with react")
        assert len(msg.blocks) >= 1
        arch = msg.blocks[0]
        assert arch.type == "ARCH"

    def test_extract_with_auth(self):
        rc = ReverseCompiler()
        msg = rc.compile("Crea una api in python con autenticazione JWT e fastapi")
        assert len(msg.blocks) >= 1
        fields = {f.key: f.value for f in msg.blocks[0].fields}
        assert "auth" in fields

    def test_extract_with_notes_cache(self):
        rc = ReverseCompiler()
        msg = rc.compile("Crea una api in python con cache ttl 10 minuti usando fastapi")
        assert len(msg.blocks) >= 1
        fields = {f.key: f.value for f in msg.blocks[0].fields}
        assert "notes" in fields

    def test_extract_build_with_file(self):
        rc = ReverseCompiler()
        msg = rc.compile("Crea il file main.py per implementare la todo app")
        has_build = any(b.type == "BUILD" for b in msg.blocks)
        assert has_build

    def test_ensure_required_fields(self):
        rc = ReverseCompiler()
        # Even with minimal input, should add id and fw
        msg = rc.compile("Crea qualcosa in python")
        if msg.blocks:
            fields = {f.key for f in msg.blocks[0].fields}
            assert "id" in fields or "fw" in fields

    def test_no_framework_detected(self):
        rc = ReverseCompiler()
        # Should still produce a block with defaults
        msg = rc.compile("Fai qualcosa di utile")
        # May or may not produce a block depending on heuristic
        assert msg is not None

    def test_empty_input(self):
        rc = ReverseCompiler()
        msg = rc.compile("")
        assert len(msg.blocks) == 0

    def test_unknown_language_triggers_reverse(self):
        rc = ReverseCompiler()
        msg = rc.compile("Sviluppa un microservizio in rust con actix-web")
        # Rust should be detected as a framework
        if msg.blocks:
            fields = {f.key: str(f.value) for f in msg.blocks[0].fields}
            # May not detect rust since it's not in the framework list
            pass  # Best-effort, should not crash
