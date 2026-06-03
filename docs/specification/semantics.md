# H2C Operational Semantics

**Version:** 1.3
**Status:** FORMAL
**Purpose:** Define the operational semantics of the H2C protocol — block meaning, transition rules, and execution model.

---

## 1. State Model

An H2C chain execution can be modeled as a finite state machine:

```
States:
  INIT      → Initial state (waiting for ARCH:PLAN)
  PLANNED   → Plan received (ARCH:PLAN emitted)
  BUILDING  → Build in progress (BUILD:EXEC emitted)
  BUILT     → Build completed (BUILD:DONE received)
  TESTING   → Test in progress (TEST:RUN emitted)
  TEST_PASS → Test passed (TEST:PASS received)
  TEST_FAIL → Test failed (TEST:FAIL received)
  FIXING    → Fixing (BUILD:FIX emitted)
  COMPACT   → Context compaction (CTX:COMPACT emitted)
  FROZEN    → Context frozen (CTX:FREEZE emitted)
  TERM      → Terminal (ORCH:END received)
```

### Transition Matrix

```
Current State     → Block Received     → New State
─────────────────────────────────────────────────────
INIT              → ARCH:PLAN          → PLANNED
PLANNED           → BUILD:EXEC         → BUILDING
BUILDING          → BUILD:DONE         → BUILT
BUILT             → TEST:RUN           → TESTING
TESTING           → TEST:PASS          → TEST_PASS
TESTING           → TEST:FAIL          → TEST_FAIL
TEST_FAIL         → BUILD:FIX          → FIXING
FIXING            → BUILD:DONE         → BUILT
BUILT|TEST_PASS   → BUILD:EXEC         → BUILDING    (next step)
ANY               → CTX:PRUNE          → ANY         (state unchanged)
ANY               → CTX:COMPACT        → COMPACT
COMPACT           → BUILD:EXEC         → BUILDING    (resumes after compact)
COMPACT           → CTX:FREEZE         → FROZEN
ANY               → CTX:FREEZE         → FROZEN
FROZEN            → BUILD:EXEC         → BUILDING    (resumes after freeze)
FROZEN            → CTX:PRUNE          → FROZEN
TEST_PASS|FROZEN  → ORCH:END           → TERM
ANY               → ORCH:END           → TERM        (error/timeout)
```

---

## 2. Semantic Opcodes

Each H2C block corresponds to a semantic opcode with defined effects:

| Opcode | Symbol | Effect |
|--------|--------|--------|
| `ARCH_PLAN` | `↻` | Initialize context, define plan |
| `BUILD_EXEC` | `→` | Start execution on target |
| `BUILD_DONE` | `✓` | Register completion and diff |
| `BUILD_FIX` | `✗→` | Request correction on revision |
| `BUILD_REVERT` | `↩` | Return to previous revision |
| `TEST_RUN` | `⚡` | Execute test suite |
| `TEST_PASS` | `✔` | Test passed, increment counter |
| `TEST_FAIL` | `✘` | Test failed, open fix cycle |
| `CTX_PRIM` | `◈` | Initial state snapshot |
| `CTX_UPD` | `◈→` | Update current layer |
| `CTX_PRUNE` | `✂` | Prune unnecessary messages |
| `CTX_COMPACT` | `⊞` | Compact cumulative history |
| `CTX_FREEZE` | `⊟` | Freeze baseline, reset counters |
| `STATE_FIND` | `◆` | Emit analysis result |
| `STATE_ACK` | `◀` | Acknowledge protocol |
| `ORCH_END` | `■` | Terminate orchestration |

### Side Effects

```
Opcode           → Side Effect
─────────────────────────────────
ARCH_PLAN        → Create context, initialize msg counters
BUILD_EXEC       → Increment build counter, push execution stack
BUILD_DONE       → Pop execution stack, register diff
BUILD_FIX        → Increment retry_n, open cycle_id
TEST_PASS        → Increment pass_count per cycle_id
TEST_FAIL        → Increment fail_count per cycle_id
CTX_PRUNE        → Decrement active message counter
CTX_COMPACT      → Reset PRUNE counter, compact history
CTX_FREEZE       → Reset PRUNE + COMPACT counters, archive history
```

---

## 3. Concurrency Model

H2C is **sequential** by design. Each message is an atomic transition:

```
┌─ Lock ─────────────────┐
│ [ARCH:PLAN]             │  ← only one block per message
│ id:X|fw:python|...      │
└─────────────────────────┘
         │
         ▼
┌─ Lock ─────────────────┐
│ [BUILD:EXEC]            │
│ id:m1|target:a.py|...   │
└─────────────────────────┘
```

No native concurrency. Multi-agent orchestration is sequential:
- One block in input
- One block in output
- Atomic transition

For parallelism, use `after:` for explicit DAG:
```
[BUILD:EXEC] id:m1|target:a.py
[BUILD:EXEC] id:m2|target:b.py|after:m1
[BUILD:EXEC] id:m3|target:c.py|after:m1   ← parallel to m2 (DAG)
```

---

## 4. Memory Model

H2C defines a **shared memory space** between agents:

```
Global Memory:
  ├── msg_counter:      integer       (global message counter)
  ├── context_state:    { layer, status, next, active_files }
  ├── revision_table:   { file → rev } (revision state)
  ├── cycle_registry:   { cycle_id → { retry_n, fail_count, pass_count, status }}
  └── findings:         [FINDING*]     (analysis results list)
```

This space is **implicit** — not explicitly serialized but reconstructible by parsing the block history.

---

## 5. Integrity Rules

```
R1: A cycle_id opened by BUILD:FIX must close with TEST:PASS or ORCH:END
R2: retry_n cannot exceed 3 per cycle_id
R3: fail_count resets when cycle_id changes
R4: CTX:PRUNE mandatory every 5 messages
R5: CTX:COMPACT mandatory every 20 messages (after reset: every 20 from COMPACT)
R6: CTX:FREEZE exactly once, when COMPACT is no longer sufficient (~100 msgs)
R7: CTX:UPDATE mandatory on every layer change
R8: ORCH:END is terminal — no blocks after
R9: Every id must be unique within the chain scope
R10: base_rev in BUILD:FIX must match rev in BUILD:DONE
```
