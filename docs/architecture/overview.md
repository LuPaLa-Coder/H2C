# H2C Protocol Architecture

**Version:** 1.0
**Status:** DEFINITIVE
**Purpose:** Architectural overview of the H2C protocol — layered model, components, and flows.

---

## 1. Layered Model

```
┌──────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  Agent skills, orchestration logic, routing              │
│  skills/h2c_architect.md, h2c_orchestrator.md, ...      │
├──────────────────────────────────────────────────────────┤
│                   SEMANTIC LAYER                         │
│  H2C block grammar, opcodes, AST, type/subtype          │
│  SPEC.md, docs/specification/grammar.md                  │
├──────────────────────────────────────────────────────────┤
│              ORCHESTRATION LAYER                         │
│  cycle_id, retry_n, PRUNE/COMPACT/FREEZE,               │
│  state tracking, error recovery                          │
│  docs/architecture/context-lifecycle.md                  │
├──────────────────────────────────────────────────────────┤
│                   TRANSPORT LAYER                        │
│  MCP, stdin/stdout, HTTP, WebSocket                     │
│  Block serialization/deserialization                    │
│  docs/ecosystem/integrations.md                          │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Agent Pipeline

H2C defines a 4-agent model:

```
┌───────────┐    ┌──────────────┐    ┌───────────┐
│ Architect │───→│ Orchestrator │───→│  Builder  │
└───────────┘    └──────────────┘    └───────────┘
                      │                    │
                      │                    ▼
                      │              ┌──────────┐
                      │              │  Tester  │
                      │              └──────────┘
                      │                    │
                      ▼                    │
                [ORCH:END] ◄────────────────┘
```

### Roles

| Agent | Input | Output | State |
|-------|-------|--------|-------|
| **Architect** | Human prompt | ARCH:PLAN + STATE:ACK | INIT → PLANNED |
| **Orchestrator** | Agent blocks | Routing, CTX, ORCH:END | Any → Any |
| **Builder** | BUILD:EXEC / FIX | BUILD:DONE | BUILDING → BUILT |
| **Tester** | TEST:RUN | TEST:PASS / FAIL | TESTING → TEST_PASS/FAIL |

---

## 3. Message Lifecycle

```
1. Block received from transport layer
2. Block parsing (→ EBNF validation)
3. Type/subtype resolution (→ dispatcher)
4. Action execution (→ agent logic)
5. State transition (→ state machine)
6. Block emission on transport layer
7. Context management (PRUNE/COMPACT/FREEZE)
```

---

## 4. Error Handling

| Error | Behavior |
|-------|----------|
| Malformed block | Discarded, ORCH:END with error |
| retry_n > 3 | ORCH:END final:error |
| cycle_id not found | Warning, context inference |
| Missing REQUIRED field | Invalid block |
| Test failed without FIX | Unhandled cycle, ORCH:END |

---

## 5. System Metrics

| Metric | Source | Purpose |
|--------|--------|---------|
| msg_counter | Global counter | PRUNE/COMPACT/FREEZE trigger |
| retry_n | Per cycle_id | Attempt limit |
| fail_count | Per cycle_id | Error tracking |
| pass_count | Per cycle_id | Success tracking |
| est_token | Self-report in ORCH:END | Cost estimation |
| token_savings | Calculated vs NL | Efficiency benchmark |
