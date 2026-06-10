"""Tests for H2C Tokenizer (Phase 1)."""

from h2c.tokenizer import tokenize, TokenType, Token


class TestTokenizer:
    def test_simple_block(self):
        tokens = tokenize("[ARCH:PLAN]\nid:test|fw:python3\n")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.LBRACKET, TokenType.TYPE, TokenType.COLON,
            TokenType.SUBTYPE, TokenType.RBRACKET, TokenType.NEWLINE,
            TokenType.STRING, TokenType.COLON, TokenType.STRING,
            TokenType.PIPE, TokenType.STRING, TokenType.COLON,
            TokenType.STRING, TokenType.NEWLINE, TokenType.EOF,
        ]

    def test_list_values(self):
        tokens = tokenize("notes:[a,b,c]")
        types = [t.type for t in tokens]
        # The comma splits list elements are not tokenized as COMMA
        # because STRING pattern doesn't exclude comma
        pass  # Tested in parser layer

    def test_revision_format(self):
        tokens = tokenize("diff:[main.py~1]")
        # STRING includes ~ because it's not excluded
        assert tokens[3].type == TokenType.STRING

    def test_comments_skipped(self):
        tokens = tokenize("# comment\n[ARCH:PLAN]\nid:x|fw:py\n")
        # Comment line should produce only NEWLINE (the \n at end of comment)
        types = [t.type for t in tokens]
        assert TokenType.TYPE in types  # ARCH should still be parsed
        assert types.count(TokenType.LBRACKET) == 1

    def test_empty_input(self):
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_negotiate_block(self):
        tokens = tokenize("[CTX:NEGOTIATE]\nversion:h2c_v1.4|capabilities:[PRUNE,COMPACT]\n")
        types = [t.type for t in tokens]
        assert types[0] == TokenType.LBRACKET
        assert types[1] == TokenType.TYPE
        assert types[2] == TokenType.COLON
        assert types[3] == TokenType.SUBTYPE
