# H2C Operational Semantics

**Version:** 1.4
**Status:** FORMAL
**Purpose:** Define the operational semantics of the H2C protocol — block meaning, transition rules, and execution model.

---

## 1. State Model

An H2C chain execution can be modeled as a finite state machine:

```
States:
  INIT       → Initial state (waiting for CTX:NEGOTIATE)
  HANDSHAKE  → Version negotiation (CTX:NEGOTIATE received)
  ACKED      → Protocol acknowledged (STATE:ACK received)
  PLANNED    → Plan received (ARCH:PLAN emitted)
  BUILDING   → Build in progress (BUILD:EXEC emitted)
  BUILT      → Build completed (BUILD:DONE received)
  TESTING    → Test in progress (TEST:RUN emitted)
  TEST_PASS  → Test passed (TEST:PASS received)
  TEST_FAIL  → Test failed (TEST:FAIL received)
  FIXING     → Fixing (BUILD:FIX emitted)
  REJECTING  → Malformed block rejected (BUILD:NACK emitted)
  COMPACT    → Context compaction (CTX:COMPACT emitted)
  FROZEN     → Context frozen (CTX:FREEZE emitted)
  TERM       → Terminal (ORCH:END received)
```

### Transition Matrix

```
Current State     → Block Received     → New State
─────────────────────────────────────────────────────
INIT              → CTX:NEGOTIATE      → HANDSHAKE
HANDSHAKE         → STATE:ACK          → ACKED
ACKED             → ARCH:PLAN          → PLANNED
PLANNED           → BUILD:EXEC         → BUILDING
PLANNED           → TEST:RUN           → TESTING        (v1.4: skip build)
BUILDING          → BUILD:DONE         → BUILT
BUILT             → TEST:RUN           → TESTING
BUILT             → BUILD:EXEC         → BUILDING       (next step)
TESTING           → TEST:PASS          → TEST_PASS
TESTING           → TEST:FAIL          → TEST_FAIL
TEST_FAIL         → BUILD:FIX          → FIXING
TEST_FAIL         → BUILD:REVERT       → BUILT
FIXING            → BUILD:DONE         → BUILT
BUILT|TEST_PASS   → BUILD:EXEC         → BUILDING       (next step)
ANY               → CTX:PRUNE          → (unchanged)
ANY               → CTX:COMPACT        → COMPACT
COMPACT           → BUILD:EXEC         → BUILDING       (resumes after compact)
COMPACT           → TEST:RUN           → TESTING        (v1.4)
COMPACT           → CTX:FREEZE         → FROZEN
ANY               → CTX:FREEZE         → FROZEN
FROZEN            → BUILD:EXEC         → BUILDING       (resumes after freeze)
FROZEN            → TEST:RUN           → TESTING        (v1.4: test after freeze)
FROZEN            → CTX:PRUNE          → FROZEN
FROZEN            → STATE:FINDINGS     → FROZEN         (v1.4)
ANY               → BUILD:NACK         → REJECTING      (v1.4: malformed block)
REJECTING         → (corrected block)  → (appropriate state)
TEST_PASS|FROZEN  → ORCH:END           → TERM
ANY               → ORCH:END           → TERM           (error/timeout)
```

---

## 2. Semantic Opcodes

Each H2C block corresponds to a semantic opcode with defined effects:

| Opcode | Symbol | Effect |
|--------|--------|--------|
| `CTX_NEGOTIATE` | `◈N` | Version handshake, capability negotiation |
| `ARCH_PLAN` | `↻` | Initialize context, define plan |
| `BUILD_EXEC` | `→` | Start execution on target |
| `BUILD_DONE` | `✓` | Register completion and diff |
| `BUILD_FIX` | `✗→` | Request correction on revision |
| `BUILD_REVERT` | `↩` | Return to previous revision |
| `BUILD_NACK` | `✗N` | Reject malformed block with error |
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
CTX_NEGOTIATE    → Set protocol version, validate capabilities
ARCH_PLAN        → Create context, initialize msg counters
BUILD_EXEC       → Increment build counter, push execution stack
BUILD_DONE       → Pop execution stack, register diff
BUILD_FIX        → Increment retry_n, open cycle_id
BUILD_REVERT     → Restore file to previous revision
BUILD_NACK       → Log rejection, signal sender for retry
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
│ [CTX:NEGOTIATE]         │  ← handshake
│ version:h2c_v1.4|...    │
└─────────────────────────┘
         │
         ▼
┌─ Lock ─────────────────┐
│ [STATE:ACK]             │  ← acknowledgement
│ protocol:h2c_v1.4       │
└─────────────────────────┘
         │
         ▼
┌─ Lock ─────────────────┐
│ [ARCH:PLAN]             │  ← only one block per message
│ id:X|fw:python|...      │
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

## 4. DAG Cycle Detection (v1.4)

The `after:` field defines a Directed Acyclic Graph (DAG) of build dependencies. Cycle detection uses **transitive closure**:

```
Given: BUILD:EXEC block B with after:[A1, A2, ...]
Let T(x) = transitive closure of all blocks reachable via after: from block x

Block B is INVALID if:
  ∃ Ai ∈ B.after such that B ∈ T(Ai)
  (i.e., there exists a path from any dependency back to B)
```

**Example — 3-node cycle (detected):**
```
A → B (A.after includes B)
B → C (B.after includes C)
C → A (C.after includes A)  ← INVALID: T(C) = {A, B, C}, A ∈ T(C)
```

**Example — valid DAG:**
```
m1 → (none)
m2 → m1
m3 → m1     ← valid: m2 and m3 are parallel after m1
m4 → m2,m3  ← valid: m4 after both parallel branches
```

---

## 5. Version Negotiation (v1.4)

```
┌──────────────────────────────────────────┐
│ Agent A (Sender)                          │
│   CTX:NEGOTIATE version:h2c_v1.4         │
│   capabilities:[PRUNE,COMPACT,NACK]      │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ Agent B (Receiver)                        │
│   ✓ version supported                     │
│   ✓ required capabilities present         │
│   → STATE:ACK protocol:h2c_v1.4          │
│   OR (if incompatible):                   │
│   → ORCH:END final:error                  │
└──────────────────────────────────────────┘
```

---

## 6. Memory Model

H2C defines a **shared memory space** between agents:

```
Global Memory:
  ├── protocol_version:  string       (negotiated via CTX:NEGOTIATE)
  ├── capabilities:      [string]     (feature flags)
  ├── msg_counter:       integer      (global message counter)
  ├── prune_counter:     integer      (resets after PRUNE and COMPACT)
  ├── compact_counter:   integer      (resets after COMPACT and FREEZE)
  ├── context_state:     { layer, status, next, active_files }
  ├── revision_table:    { file → rev }
  ├── cycle_registry:    { cycle_id → { retry_n, fail_count, pass_count, status } }
  └── findings:          [FINDING*]
```

This space is **implicit** — not explicitly serialized but reconstructible by parsing the block history.

---

## 7. Integrity Rules

```
R1:  CTX:NEGOTIATE must be the first block of every chain (v1.4)
R2:  STATE:ACK must follow CTX:NEGOTIATE immediately (v1.4)
R3:  A cycle_id opened by BUILD:FIX must close with TEST:PASS or ORCH:END
R4:  retry_n cannot exceed 3 per cycle_id
R5:  fail_count resets when cycle_id changes
R6:  CTX:PRUNE mandatory every 5 messages
R7:  CTX:COMPACT mandatory every 20 messages (after reset: every 20 from COMPACT)
R8:  CTX:FREEZE exactly once, when COMPACT is no longer sufficient (~100 msgs)
R9:  CTX:UPDATE mandatory on every layer change
R10: ORCH:END is terminal — no blocks after
R11: Every id must be unique within the chain scope
R12: base_rev in BUILD:FIX must match rev in BUILD:DONE
R13: On malformed block, receiver emits BUILD:NACK — no silent discard (v1.4)
R14: DAG cycle detection uses transitive closure across all N nodes (v1.4)
```
