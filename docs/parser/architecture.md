# Architettura del Parser — Protocollo H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Definire l'architettura di riferimento del parser per il protocollo H2C — scanning, parsing, costruzione AST e recovery errori.

---

## 1. Pipeline

```
Input (testo)
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scanner   │───→│   Parser    │───→│   Builder   │───→│   AST       │
│ (tokenizer) │    │ (grammatica)│    │ (semantica) │    │ (output)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                    │
     ▼                   ▼                    ▼
  Flusso             Errori di             Validazione
  Token              Parsing               Semantica
```

## 2. Scanner (Tokenizer)

### 2.1 Tipi di Token

```
Token          Regex                          Esempio
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
STRING         [^\[\]\|\n:,\~]+              python3.11, fastapi
INTEGER        [0-9]+                        42
NEWLINE        \n                            \n
EOF            fine input
```

### 2.2 Algoritmo di Scansione

```
scan(input):
  pos = 0
  tokens = []
  while pos < len(input):
    salta spazi (tranne newline)
    if input[pos] == '[': emetti(LBRACKET); pos++
    elif input[pos] == ']': emetti(RBRACKET); pos++
    elif input[pos] == ':': emetti(COLON); pos++
    elif input[pos] == '|': emetti(PIPE); pos++
    elif input[pos] == ',': emetti(COMMA); pos++
    elif input[pos] == '~': emetti(TILDE); pos++
    elif input[pos] == '\n':
      emetti(NEWLINE); pos++
    elif match(TYPE):  emetti(TYPE);  pos += len(match)
    elif match(SUBTYPE): emetti(SUBTYPE); pos += len(match)
    elif match(KEY):  emetti(KEY); pos += len(match)
    elif match(INTEGER): emetti(INTEGER); pos += len(match)
    else: emetti(STRING); pos++
  emetti(EOF)
```

## 3. Parser (Guidato dalla Grammatica)

### 3.1 Traduzione della Grammatica

La grammatica EBNF (`docs/specification/grammar.md`) si traduce in metodi del parser:

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

### 3.2 Parser Ricorsivo Discendente

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

## 4. Modello AST

### 4.1 Gerarchia dei Tipi

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
  │    ├── is_ctx_field: bool  (prefisso ~)
  │    └── value: Value
  ├── Value (astratto)
  │    ├── StringValue: string
  │    ├── ListValue: string[]
  │    ├── RevisionValue: { file: string, rev: int }
  │    └── IntegerValue: int
  ├── Type: enum
  └── Subtype: enum
```

### 4.2 Esempio di AST

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

## 5. Gestione Errori

### 5.1 Tipi di Errore

| Errore | Rilevamento | Recupero |
|--------|-------------|----------|
| Token inaspettato | Il parser vede token non valido per la grammatica | Salta fino al prossimo `[` o EOF |
| Campo REQUIRED mancante | Il validatore controlla dopo il parsing | Warning + blocco scartato |
| Tipo/sottotipo non valido | Il parser valida contro l'enum | Salta blocco, continua |
| Valore malformato | Lo scanner non riconosce alcun token | Emetti come StringValue |
| Parentesi non chiusa | Scanner: conteggio mismatch | Errore a livello di linea |

### 5.2 Strategia di Recupero

```
parse_until_next_block():
  while peek() != LBRACKET and peek() != EOF:
    consume()     # salta rumore
  if peek() == LBRACKET:
    return parse_block()
  return null
```

## 6. Percorsi Implementativi

| Linguaggio | Strategia | Consigliato Per |
|------------|-----------|----------------|
| Python | `re` + discendente ricorsivo manuale | Prototipazione, CLI |
| Rust | `nom` o `pest` parser combinatori | Parser produzione, WASM |
| TypeScript | Chevrotain o manuale | Browser, MCP |
| Go | `text/scanner` + discendente ricorsivo | Embedded leggero |
| C# | Superpower o Sprache | .NET ecosistema |

### Esempio: Parser Python Minimo (75 linee)

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
    ('STRING', r'[^\[\]\|\n:,\~]+'),
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
