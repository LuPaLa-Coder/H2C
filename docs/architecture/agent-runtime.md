# H2C Agent Runtime Model

**Version:** 1.0
**Status:** DESIGN
**Purpose:** Specify the execution model for H2C agents — scheduling, routing, error recovery.

---

## 1. Agent Execution Cycle

```
┌──────────────────────┐
│    Wait Input        │
│  (listen on channel) │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   Block Parsing      │
│  (EBNF grammar)      │
└──────────┬───────────┘
           ▼
┌────────────────────────┐
│   Validation           │
│  (operational rules)   │
└──────────┬─────────────┘
    ┌──────┴──────┐
    ▼             ▼
┌──────────┐ ┌───────────┐
│ Valid    │ │ Invalid   │
└────┬─────┘ └────┬──────┘
     ▼            ▼
┌──────────┐ ┌───────────┐
│ Execute   │ │ Reject +  │
│ Action    │ │ Log       │
└────┬─────┘ └───────────┘
     ▼
┌───────────────────────┐
│   Emit Output         │
│  (next block)         │
└───────────────────────┘
```

---

## 2. Routing

| Input Block | Sender | Receiver | Output Block |
|------------|--------|----------|--------------|
| ARCH:PLAN | Architect | Orchestrator | BUILD:EXEC |
| BUILD:EXEC | Orchestrator | Builder | BUILD:DONE |
| BUILD:DONE | Builder | Orchestrator | TEST:RUN or BUILD:EXEC |
| BUILD:FIX | Orchestrator | Builder | BUILD:DONE |
| TEST:RUN | Orchestrator | Tester | TEST:PASS/FAIL |
| TEST:PASS | Tester | Orchestrator | ORCH:END or BUILD:EXEC |
| TEST:FAIL | Tester | Orchestrator | BUILD:FIX |
| CTX:* | Orchestrator | Broadcast | — |

---

## 3. Error Recovery

| Failure | Behavior |
|---------|----------|
| Parsing failed | Block discarded, error log |
| Validation failed | Warning, attempt recovery |
| Execution timeout | ORCH:END final:timeout |
| retry_n > 3 | ORCH:END final:error |
| Duplicate cycle_id | Merge context, warning |
| Missing REQUIRED field | ORCH:END final:error |
