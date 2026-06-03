# Compiler Pipeline — H2C Protocol

**Version:** 1.0
**Status:** RESEARCH
**Scope:** Define the architecture of the H2C compiler/transpiler — from H2C to other formats and vice versa.

---

## 1. Vision

The H2C compiler transforms H2C blocks into other formats (natural language, JSON, MCP, YAML) and vice versa. It serves as a bridge between the H2C protocol and existing tools/frameworks.

```
┌──────────┐    ┌──────────────┐    ┌──────────┐
│  H2C     │───→│  Compiler    │───→│  Output  │
│ (input)  │    │  H2C v1.3    │    │ formats  │
└──────────┘    └──────────────┘    └──────────┘
                      │
                      ├──→ Natural Language
                      ├──→ JSON / JSON-RPC
                      ├──→ YAML
                      ├──→ MCP Tool Call
                      └──→ Complete LLM Prompt
```

## 2. Compilation Pipeline

```
H2C Input
   │
   ▼
┌──────────────┐
│   Parsing    │  → AST (docs/parser/architecture.md)
└──────────────┘
   │
   ▼
┌──────────────┐
│  Validation  │  → Check REQUIRED fields, types, constraints
└──────────────┘
   │
   ▼
┌──────────────┐
│  Semantic    │  → Reference resolution (cycle_id, after)
│  Analysis    │  → State and context reconstruction
└──────────────┘
   │
   ▼
┌──────────────┐
│  Codegen     │  → Generate output in target format
└──────────────┘
   │
   ▼
Output
```

## 3. Codegen Backends

### 3.1 H2C → Natural Language

Converts H2C blocks into human-readable prompts. Useful for debugging, logging, and documentation.

```
Input:
[ARCH:PLAN]
id:api|fw:python|lib:fastapi,redis|notes:[auth_JWT,cache_10min]

Output:
=== ARCH:PLAN ===
ID: api
Framework: python
Libraries: fastapi, redis
Notes: JWT authentication, 10 min cache
```

**Template for each block:**

| Block | NL Template |
|-------|-------------|
| `ARCH:PLAN` | `Architectural plan for {id}. Framework: {fw}. Libraries: {lib}. Notes: {notes}` |
| `BUILD:EXEC` | `Execute build {id} on {target}. Description: {desc}` |
| `BUILD:DONE` | `Build {id} completed on {diff}` |
| `BUILD:FIX` | `Fix {target} (rev {base_rev}): {desc}` |
| `TEST:RUN` | `Run test {id}: {cmd}` |
| `TEST:PASS` | `Test {id} passed` |
| `TEST:FAIL` | `Test {id} failed: {error}` |
| `CTX:PRUNE` | `Context pruning: kept {keep}, pruned {pruned}` |
| `CTX:COMPACT` | `Compaction: {summary}` |
| `ORCH:END` | `Orchestration terminated: {final}` |

### 3.2 H2C → JSON

Converts H2C blocks into structured JSON for integration with REST APIs and messaging systems.

```
Input:
[BUILD:DONE]
id:m1|diff:[main.py~1,+15]|rev:1

Output:
{
  "type": "BUILD",
  "subtype": "DONE",
  "fields": {
    "id": "m1",
    "diff": [{"file": "main.py", "rev": 1, "lines": "+15"}],
    "rev": 1
  }
}
```

### 3.3 H2C → MCP Tool Call

Converts H2C blocks into MCP tool calls. Enables H2C to be transported over MCP.

```
Input:
[BUILD:EXEC]
id:m2|target:models/user.py|desc:create_user_model

Output:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "h2c_build_exec",
    "arguments": {
      "id": "m2",
      "target": "models/user.py",
      "desc": "create_user_model"
    }
  },
  "id": 1
}
```

### 3.4 H2C → YAML

```
build_exec:
  id: m2
  target: models/user.py
  desc: create_user_model
```

## 4. Reverse Compiler (NL → H2C)

The reverse compiler analyzes natural language text and produces H2C blocks. Useful for:
- Gradual migration from NL prompts to H2C
- Hybrid interfaces (human writes NL, system converts to H2C)
- Onboarding tooling

```
Input NL:
"Crea un'API meteo in Python con FastAPI.
Usa httpx per le chiamate HTTP.
Richiede autenticazione con API key.
Cache TTL 10 minuti."

Output:
[ARCH:PLAN]
id:api|fw:python3.11|lib:fastapi,httpx,cachetools|auth:APIKey|notes:[cache_TTL_10min]
```

**Strategy:** Uses pattern matching on typical prompt engineering structures:
- "Crea un ... in ..." → `id` + `fw`
- "Usa ... per ..." → `lib`
- "Richiede ..." → `auth`
- Technical notes in parentheses → `notes`

## 5. Validator

### 5.1 Validation Rules

```
VALIDATOR-1:  Every block must have valid type and subtype (against enum §1)
VALIDATOR-2:  REQUIRED fields must be present
VALIDATOR-3:  Fields must have correct type (string/list/int/enum)
VALIDATOR-4:  cycle_id must be consistent across the chain
VALIDATOR-5:  retry_n in range [1..3]
VALIDATOR-6:  after: must reference existing ids (DAG integrity, cycles detected → invalid block)
VALIDATOR-7:  diff: correct format [file~N,+M,file~N,-K]
VALIDATOR-8:  ORCH:END is terminal — no blocks after
VALIDATOR-9:  CTX:PRUNE every 5 messages (temporal check)
VALIDATOR-10: CTX:COMPACT every 20 messages
VALIDATOR-11: CTX:FREEZE no more than once
VALIDATOR-12: No text outside fields
```

### 5.2 Validator Architecture

```
┌──────────────┐
│  H2C         │
│  Validator   │
└──────┬───────┘
       │
       ├── Syntactic Validator
       │     ├── Block format check [TYPE:SUBTYPE]
       │     ├── Separator check : and |
       │     └── Bracket check []
       │
       ├── Structural Validator
       │     ├── REQUIRED fields present
       │     ├── Field types correct
       │     └── Format constraints
       │
       ├── Contextual Validator
       │     ├── cycle_id consistency
       │     ├── DAG after: integrity
       │     ├── retry_n range
       │     └── PRUNE/COMPACT/FREEZE frequency
       │
       └── Terminal Validator
             ├── ORCH:END is last
             └── No blocks after END
```

### 5.3 Validation Output

```json
{
  "valid": false,
  "errors": [
    {
      "level": "error",
      "rule": "VALIDATOR-1",
      "message": "Blocco [INVALID:FOO] ha tipo non valido",
      "location": {"line": 3, "block": 2}
    },
    {
      "level": "warning",
      "rule": "VALIDATOR-9",
      "message": "CTX:PRUNE non emesso da 6 messaggi",
      "location": {"line": 42}
    }
  ],
  "stats": {
    "total_blocks": 15,
    "valid_blocks": 14,
    "errors": 1,
    "warnings": 1
  }
}
```

## 6. Routing Table (Dispatcher)

The dispatcher routes each block to the appropriate component:

```
Block              → Destination
────────────────────────────────
ARCH:PLAN           → Planning system
BUILD:EXEC          → Builder (executor)
BUILD:DONE          → Orchestrator (notification)
BUILD:FIX           → Builder (correction)
BUILD:REVERT        → Builder (rollback)
TEST:RUN            → Tester
TEST:PASS           → Orchestrator (success)
TEST:FAIL           → Orchestrator (error)
CTX:PRIMITIVES      → Context manager
CTX:UPDATE          → Context manager
CTX:PRUNE           → Context manager (pruning)
CTX:COMPACT         → Context manager (compaction)
CTX:FREEZE          → Context manager (freezing)
STATE:FINDINGS      → Auditing system
STATE:ACK           → Protocol (handshake)
ORCH:END            → Orchestrator (termination)
SKILL:PROMPT        → Agent definition
```

## 7. Implementation Roadmap

| Phase | Component | Status |
|-------|-----------|--------|
| 1 | Python parser (minimal) | DRAFT |
| 2 | Syntactic validator | DRAFT |
| 3 | NL codegen (H2C → text) | DRAFT |
| 4 | JSON codegen (H2C → API) | DRAFT |
| 5 | Reverse compiler NL → H2C | RESEARCH |
| 6 | Native MCP integration | RESEARCH |
| 7 | Rust/WASM parser (production) | RESEARCH |
| 8 | IDE extension (syntax highlight, validation) | FUTURE |
