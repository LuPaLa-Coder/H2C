# Parser Architecture — H2C Protocol

**Version:** 1.0
**Status:** DRAFT
**Scope:** Define the reference parser architecture for the H2C protocol — scanning, parsing, AST construction, and error recovery.

---

## 1. Pipeline

```
Input (text)
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scanner   │───→│   Parser    │───→│   Builder   │───→│   AST       │
│ (tokenizer) │    │ (grammar)   │    │ (semantics) │    │ (output)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                    │
     ▼                   ▼                    ▼
  Token              Parsing              Semantic
  Stream             Errors               Validation
```

## 2. Scanner (Tokenizer)

### 2.1 Token Types

```
Token          Regex                          Example
────────────────────────────────────────────────────────────────────
LBRACKET       \[                            [
RBRACKET       \]                            ]
COLON          :                             :
PIPE           \|                            |
COMMA          ,                             ,
TILDE          ~                             ~
TYPE           ARCH|BUILD|TEST|CTX|STATE|ORCH|SKILL
SUBTYPE        PLAN|EXEC|DONE|FIX|REVERT|RUN|PASS|FAIL|...
KEY            [a-zA-Z_][a-zA-Z0-9_]*
STRING         [^\[\]\|\n]+                  python3.11
INTEGER        [0-9]+                        42
NEWLINE        \n                            \n
EOF            end of input
```

### 2.2 Scanning Algorithm

```
scan(input):
  pos = 0
  tokens = []
  while pos < len(input):
    skip spaces (except newlines)
    if input[pos] == '[': emit(LBRACKET); pos++
    elif input[pos] == ']': emit(RBRACKET); pos++
    elif input[pos] == ':': emit(COLON); pos++
    elif input[pos] == '|': emit(PIPE); pos++
    elif input[pos] == ',': emit(COMMA); pos++
    elif input[pos] == '~': emit(TILDE); pos++
    elif input[pos] == '\n':
      emit(NEWLINE); pos++
    elif match(TYPE):  emit(TYPE);  pos += len(match)
    elif match(SUBTYPE): emit(SUBTYPE); pos += len(match)
    elif match(KEY):  emit(KEY); pos += len(match)
    elif match(INTEGER): emit(INTEGER); pos += len(match)
    else: emit(STRING); pos++
  emit(EOF)
```

## 3. Parser (Grammar-Driven)

### 3.1 Grammar Translation

The EBNF grammar (`docs/specification/grammar.md`) is translated into parser methods:

```
message()    → block()
block()      → LBRACKET type() COLON subtype() RBRACKET NEWLINE fields()
fields()     → field() { PIPE field() }
field()      → key() COLON value()
key()        → KEY | TILDE KEY
value()      → STRING | list() | revision() | INTEGER
list()       → LBRACKET STRING { COMMA STRING } RBRACKET
revision()   → STRING TILDE INTEGER
type()       → TYPE
subtype()    → SUBTYPE
```

### 3.2 Recursive Descent Parser

```
parse_block():
  expect(LBRACKET)
  type = expect(TYPE)
  expect(COLON)
  subtype = expect(SUBTYPE)
  expect(RBRACKET)
  expect(NEWLINE)
  fields = parse_fields()
  return Block(type, subtype, fields)

parse_fields():
  fields = []
  if peek() == EOF: return fields
  while peek() != EOF and peek() != LBRACKET:
    key = expect(KEY) | expect(TILDE) + expect(KEY)
    expect(COLON)
    value = parse_value()
    fields.append(Field(key, value))
    if peek() == PIPE: consume(PIPE)
    elif peek() == NEWLINE: break
  return fields

parse_value():
  if peek() == LBRACKET: return parse_list()
  elif match(PATTERN_REVISION): return parse_revision()
  elif match(INTEGER): return IntegerValue(expect(INTEGER))
  else: return StringValue(expect(STRING))
```

## 4. AST Model

### 4.1 Type Hierarchy

```
Node
  ├── Message
  │    └── blocks: Block[]
  ├── Block
  │    ├── type: Type
  │    ├── subtype: Subtype
  │    └── fields: Field[]
  ├── Field
  │    ├── key: string
  │    ├── is_ctx_field: bool  (prefix ~)
  │    └── value: Value
  ├── Value (abstract)
  │    ├── StringValue: string
  │    ├── ListValue: string[]
  │    ├── RevisionValue: { file: string, rev: int }
  │    └── IntegerValue: int
  ├── Type: enum
  └── Subtype: enum
```

### 4.2 AST Example

Input:
```
[ARCH:PLAN]
id:api-meteo|fw:python3.11|notes:[cache_TTL_10min]
```

AST:
```json
{
  "blocks": [{
    "type": "ARCH",
    "subtype": "PLAN",
    "fields": [
      {"key": "id",    "value": {"kind": "string",  "data": "api-meteo"}},
      {"key": "fw",    "value": {"kind": "string",  "data": "python3.11"}},
      {"key": "notes", "value": {"kind": "list",    "data": ["cache_TTL_10min"]}}
    ]
  }]
}
```

## 5. Error Handling

### 5.1 Error Types

| Error | Detection | Recovery |
|-------|-----------|----------|
| Unexpected token | Parser sees invalid token for grammar | Skip to next `[` or EOF |
| Missing REQUIRED field | Validator checks after parsing | Warning + block discarded |
| Invalid type/subtype | Parser validates against enum | Skip block, continue |
| Malformed value | Scanner doesn't recognize any token | Emit as StringValue |
| Unclosed bracket | Scanner: mismatch count | Line-level error |

### 5.2 Recovery Strategy

```
parse_until_next_block():
  while peek() != LBRACKET and peek() != EOF:
    consume()     # skip noise
  if peek() == LBRACKET:
    return parse_block()
  return null
```

## 6. Implementation Paths

| Language | Strategy | Recommended For |
|----------|----------|-----------------|
| Python | `re` + manual recursive descent | Prototyping, CLI |
| Rust | `nom` or `pest` parser combinators | Production parser, WASM |
| TypeScript | Chevrotain or manual | Browser, MCP |
| Go | `text/scanner` + recursive descent | Lightweight embedded |
| C# | Superpower or Sprache | .NET ecosystem |

### Example: Minimal Python Parser (75 lines)

```python
import re

# Tokenizer
TOKEN_SPEC = [
    ('LBRACKET', r'\['), ('RBRACKET', r'\]'),
    ('COLON', r':'), ('PIPE', r'\|'), ('COMMA', r','), ('TILDE', r'~'),
    ('TYPE', r'ARCH|BUILD|TEST|CTX|STATE|ORCH|SKILL'),
    ('SUBTYPE', r'PLAN|EXEC|DONE|FIX|REVERT|RUN|PASS|FAIL|'
                r'PRIMITIVES|UPDATE|PRUNE|COMPACT|FREEZE|'
                r'FINDINGS|ACK|END|PROMPT'),
    ('KEY', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('INTEGER', r'[0-9]+'),
    ('NEWLINE', r'\n'),
    ('STRING', r'[^\[\]\|\n]+'),
]
token_re = '|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_SPEC)

def tokenize(text):
    for m in re.finditer(token_re, text):
        yield m.lastgroup, m.group()

class Block:
    def __init__(self, type_, subtype, fields):
        self.type = type_; self.subtype = subtype; self.fields = fields

class Field:
    def __init__(self, key, value):
        self.key = key; self.value = value

def parse(text):
    tokens = list(tokenize(text)); pos = 0
    def peek(): return tokens[pos] if pos < len(tokens) else ('EOF',)
    def consume(expected=None):
        nonlocal pos
        t = tokens[pos]; pos += 1
        if expected and t[0] != expected:
            raise SyntaxError(f'Atteso {expected}, ricevuto {t[0]}')
        return t

    blocks = []
    while pos < len(tokens):
        if peek()[0] != 'LBRACKET': pos += 1; continue
        consume('LBRACKET')
        type_ = consume('TYPE')[1]
        consume('COLON')
        subtype = consume('SUBTYPE')[1]
        consume('RBRACKET')
        if peek()[0] == 'NEWLINE': consume()
        fields = []
        while pos < len(tokens) and peek()[0] not in ('LBRACKET', 'EOF'):
            if peek()[0] == 'TILDE':
                consume(); key = '~' + consume('KEY')[1]
            else:
                key = consume('KEY')[1]
            consume('COLON')
            val = consume()[1]
            fields.append(Field(key, val))
            if peek()[0] == 'PIPE': consume()
        blocks.append(Block(type_, subtype, fields))
    return blocks
```
