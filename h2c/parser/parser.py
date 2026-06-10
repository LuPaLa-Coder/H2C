"""H2C Recursive Descent Parser.

Implements the parsing logic from docs/parser/architecture.md sections 3-5.
Follows the PEG parsing order from SPEC.md section 1.1.

Grammar:
    message   → block*
    block     → "[" TYPE ":" SUBTYPE "]" NEWLINE fields
    fields    → field ("|" field)*
    field     → [TILDE] STRING ":" value
    value     → INTEGER | signed_int | revision | list | STRING
"""

import re
from typing import List, Optional

from h2c.tokenizer.scanner import tokenize as _tokenize
from h2c.tokenizer.token import Token, TokenType
from h2c.parser.ast import (
    Block,
    Field,
    IntegerValue,
    ListValue,
    Message,
    RevisionValue,
    SignedIntValue,
    StringValue,
    Value,
)
from h2c.parser.errors import (
    H2CParseError,
    InvalidSubtype,
    InvalidType,
    MalformedBlock,
    UnexpectedToken,
)

_VALID_TYPES = frozenset({"ARCH", "BUILD", "TEST", "CTX", "STATE", "ORCH", "SKILL"})
_VALID_SUBTYPES = frozenset({
    "PLAN", "EXEC", "DONE", "FIX", "REVERT", "NACK",
    "RUN", "PASS", "FAIL",
    "PRIMITIVES", "UPDATE", "PRUNE", "COMPACT", "FREEZE", "NEGOTIATE",
    "FINDINGS", "ACK",
    "END", "PROMPT",
})
_SIGNED_INT_RE = re.compile(r"^[+-][0-9]+$")


class Parser:
    """Recursive-descent parser for H2C text.

    Consumes a pre-tokenized list and produces a Message AST.
    Implements error recovery per docs/parser/architecture.md section 5.2:
    on unexpected tokens, skips forward to the next '[' or EOF.
    """

    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    # ── public API ───────────────────────────────────────────────────────

    def parse(self) -> Message:
        """Parse all blocks until EOF. On error, skip to next block boundary."""
        blocks: List[Block] = []
        while self._pos < len(self._tokens):
            if self._peek_type() == TokenType.EOF:
                break
            try:
                block = self._parse_block()
                if block is not None:
                    blocks.append(block)
            except H2CParseError:
                self._recover()
        return Message(blocks=blocks)

    # ── block parsing ────────────────────────────────────────────────────

    def _parse_block(self) -> Optional[Block]:
        """block → '[' TYPE ':' SUBTYPE ']' NEWLINE? fields"""
        self._expect(TokenType.LBRACKET)

        type_tok = self._expect(TokenType.TYPE)
        type_val = type_tok.value
        if type_val not in _VALID_TYPES:
            raise InvalidType(
                f"Invalid H2C type: {type_val}",
                pos=type_tok.pos,
                line=type_tok.line,
            )

        self._expect(TokenType.COLON)

        subtype_tok = self._expect(TokenType.SUBTYPE)
        subtype_val = subtype_tok.value
        if subtype_val not in _VALID_SUBTYPES:
            raise InvalidSubtype(
                f"Invalid H2C subtype: {subtype_val}",
                pos=subtype_tok.pos,
                line=subtype_tok.line,
            )

        self._expect(TokenType.RBRACKET)

        # Optional trailing newline after header
        if self._peek_type() == TokenType.NEWLINE:
            self._consume()

        fields = self._parse_fields()

        return Block(type=type_val, subtype=subtype_val, fields=fields)

    # ── field parsing ────────────────────────────────────────────────────

    def _parse_fields(self) -> List[Field]:
        """fields → field ('|' field)*"""
        fields: List[Field] = []
        # Parse first field (a block must have at least one field)
        if self._peek_type() in (
            TokenType.STRING, TokenType.TILDE, TokenType.KEY,
            TokenType.TYPE, TokenType.SUBTYPE,
        ):
            fields.append(self._parse_field())
        else:
            return fields  # empty fields list (e.g., standalone header)

        while self._peek_type() == TokenType.PIPE:
            self._consume()  # skip |
            # After PIPE, expect another field. Skip trailing |
            if self._peek_type() in (
                TokenType.STRING, TokenType.TILDE, TokenType.KEY,
                TokenType.TYPE, TokenType.SUBTYPE,
            ):
                fields.append(self._parse_field())

        # Consume optional trailing newline
        if self._peek_type() == TokenType.NEWLINE:
            self._consume()

        return fields

    def _parse_field(self) -> Field:
        """field → [TILDE] (STRING | KEY | TYPE | SUBTYPE) ':' value

        TYPE and SUBTYPE tokens accepted as keys because in field context
        they function as plain identifiers (tokenizer cannot distinguish context).

        CTX fields preserve the ~ prefix in the key (e.g. ~task).
        """
        is_ctx = False

        if self._peek_type() == TokenType.TILDE:
            self._consume()
            is_ctx = True

        # Key: STRING, KEY, TYPE, or SUBTYPE tokens are all valid key names
        key_tok = self._consume_any(
            TokenType.STRING, TokenType.KEY, TokenType.TYPE, TokenType.SUBTYPE
        )
        key = f"~{key_tok.value}" if is_ctx else key_tok.value

        self._expect(TokenType.COLON)

        value = self._parse_value()

        return Field(key=key, value=value, is_ctx=is_ctx)

    # ── value parsing (PEG order) ────────────────────────────────────────

    def _parse_value(self) -> Value:
        """value → INTEGER | signed_int | revision | list | STRING

        PEG order from SPEC.md section 1.1:
        1. INTEGER
        2. signed_int  ([+-][0-9]+)
        3. revision    (STRING '~' INTEGER)
        4. list        ('[' value {',' value} ']')
        5. string      (fallback)
        """
        tok = self._peek()

        # 1. INTEGER → IntegerValue
        if tok.type == TokenType.INTEGER:
            tok = self._consume()
            return IntegerValue(data=int(tok.value))

        # 2. STRING matching [+-][0-9]+ → SignedIntValue
        if tok.type == TokenType.STRING and _SIGNED_INT_RE.match(tok.value):
            tok = self._consume()
            return SignedIntValue(data=int(tok.value))

        # 3. Revision: STRING '~' INTEGER (3-token lookahead)
        if tok.type == TokenType.STRING:
            if self._peek_ahead_type(1) == TokenType.TILDE and \
               self._peek_ahead_type(2) == TokenType.INTEGER:
                file_tok = self._consume()          # STRING
                self._consume()                      # TILDE
                rev_tok = self._consume()            # INTEGER
                return RevisionValue(
                    file=file_tok.value,
                    rev=int(rev_tok.value),
                )
            # Not a revision — fall through to string

        # 4. LBRACKET → list
        if tok.type == TokenType.LBRACKET:
            return self._parse_list()

        # 5. STRING → StringValue (fallback)
        if tok.type == TokenType.STRING:
            tok = self._consume()
            return StringValue(data=tok.value)

        # Also accept KEY, TYPE, SUBTYPE tokens as fallback string values.
        # TYPE/SUBTYPE keywords inside lists (e.g. [PRUNE,COMPACT]) are
        # tokenized as SUBTYPE tokens but represent string values in context.
        if tok.type in (TokenType.KEY, TokenType.TYPE, TokenType.SUBTYPE):
            tok = self._consume()
            return StringValue(data=tok.value)

        raise UnexpectedToken(
            expected="value (INTEGER, STRING, or LBRACKET)",
            got=tok.type.value,
            pos=tok.pos,
            line=tok.line,
        )

    def _parse_list(self) -> ListValue:
        """list → '[' <item> {',' <item>} ']'

        Because commas are not excluded from the STRING token pattern
        (per the spec), list content between brackets is consumed as raw
        tokens, joined, split on commas, and each element is re-parsed
        through parse_value().  This handles mixed element types: revision,
        signed_int, and plain string.
        """
        self._expect(TokenType.LBRACKET)

        # Collect all raw tokens between [ and ]
        raw_parts: List[str] = []
        depth = 1
        while depth > 0 and self._peek_type() != TokenType.EOF:
            t = self._peek()
            if t.type == TokenType.LBRACKET:
                depth += 1
            elif t.type == TokenType.RBRACKET:
                depth -= 1
                if depth == 0:
                    self._consume()  # consume ]
                    break
            raw_parts.append(t.value)
            self._consume()

        # Join, split on commas, re-parse each element
        joined = "".join(raw_parts)
        if not joined.strip():
            return ListValue(data=[])

        elements = joined.split(",")
        items: List[str] = []
        for elem in elements:
            elem = elem.strip()
            if not elem:
                continue
            elem_tokens = _tokenize(elem)
            # Remove trailing EOF
            elem_tokens = [t for t in elem_tokens if t.type != TokenType.EOF]
            if not elem_tokens:
                items.append(elem)
                continue
            try:
                sub_parser = Parser(elem_tokens)
                val = sub_parser._parse_value()
                items.append(_value_to_string(val))
            except H2CParseError:
                items.append(elem)

        return ListValue(data=items)

    # ── helpers ───────────────────────────────────────────────────────────

    def _peek(self) -> Token:
        """Return current token without consuming it."""
        if self._pos >= len(self._tokens):
            return Token(TokenType.EOF, "", -1, -1)
        return self._tokens[self._pos]

    def _peek_type(self) -> TokenType:
        return self._peek().type

    def _peek_ahead(self, n: int) -> Token:
        """Peek n tokens ahead (0 = current)."""
        idx = self._pos + n
        if idx >= len(self._tokens):
            return Token(TokenType.EOF, "", -1, -1)
        return self._tokens[idx]

    def _peek_ahead_type(self, n: int) -> TokenType:
        return self._peek_ahead(n).type

    def _consume(self) -> Token:
        """Consume and return the current token."""
        tok = self._peek()
        self._pos += 1
        return tok

    def _expect(self, expected: TokenType) -> Token:
        """Consume a token, raising if it's not the expected type."""
        tok = self._peek()
        if tok.type != expected:
            raise UnexpectedToken(
                expected=expected.value,
                got=tok.type.value,
                pos=tok.pos,
                line=tok.line,
            )
        return self._consume()

    def _consume_any(self, *types: TokenType) -> Token:
        """Consume a token, raising if it doesn't match any of the given types."""
        tok = self._peek()
        if tok.type not in types:
            expected = " | ".join(t.value for t in types)
            raise UnexpectedToken(
                expected=expected,
                got=tok.type.value,
                pos=tok.pos,
                line=tok.line,
            )
        return self._consume()

    def _recover(self):
        """Skip tokens until next LBRACKET or EOF (per §5.2)."""
        while self._pos < len(self._tokens):
            if self._peek_type() in (TokenType.LBRACKET, TokenType.EOF):
                return
            self._pos += 1


def _value_to_string(v: Value) -> str:
    """Flatten a parsed value back to its string representation."""
    if isinstance(v, StringValue):
        return v.data
    elif isinstance(v, IntegerValue):
        return str(v.data)
    elif isinstance(v, SignedIntValue):
        return f"+{v.data}" if v.data >= 0 else str(v.data)
    elif isinstance(v, RevisionValue):
        return f"{v.file}~{v.rev}"
    elif isinstance(v, ListValue):
        return "[" + ",".join(v.data) + "]"
    return str(v)


def parse(text: str) -> Message:
    """Convenience: tokenize + parse H2C text into a Message AST."""
    from h2c.tokenizer.scanner import tokenize
    tokens = tokenize(text)
    return Parser(tokens).parse()
