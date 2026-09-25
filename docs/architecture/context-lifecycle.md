# H2C Context Lifecycle

**Version:** 1.3
**Status:** DEFINITIVE
**Purpose:** Specify the context management system — PRUNE/COMPACT/FREEZE mechanism enabling long chains.

---

## 1. Problem

AI agent chains suffer from model context window saturation as conversation history grows: verbose natural-language history accumulates faster than structured history, and referential coherence degrades as unpruned context grows (not independently benchmarked). H2C addresses this at the protocol level with a three-tier context management system.

---

## 2. Context Management Triad

```
Threshold   Message        Action
─────────────────────────────────────
Every 5     CTX:PRUNE      Purge unnecessary messages
Every 20    CTX:COMPACT    Compact history into summary
~100        CTX:FREEZE     Freeze baseline, full reset
```

> **Status:** today these blocks are signals for the orchestrator — they tell
> it what *could* be pruned, compacted, or frozen. Automatic history
> compaction in the reference runtime (actually shrinking what is sent back
> to the model) is planned for a later phase and is not implemented yet.

---

## 3. PRUNE — Local Purging

**Trigger:** Every 5 messages (global counter)
**Purpose:** Remove messages no longer needed in the active window

### Pruning Rules

| Block | Condition | Prunable? |
|-------|-----------|:---------:|
| ARCH:PLAN | Subsequent COMPACT exists | Yes |
| ARCH:PLAN | Latest, no COMPACT | NO |
| BUILD:EXEC | Corresponding BUILD:DONE emitted | Yes |
| BUILD:EXEC | BUILD:DONE NOT yet emitted | NO |
| BUILD:FIX | cycle_id still open | NO |
| BUILD:FIX | cycle_id closed (TEST:PASS) | Yes |
| BUILD:DONE | Subsequent COMPACT exists | Yes |
| TEST:RUN | Outcome (PASS/FAIL) emitted | Yes |
| TEST:RUN | Outcome NOT yet emitted | NO |
| TEST:PASS/FAIL | Subsequent COMPACT exists | Yes |
| CTX:PRUNE | After emission | Yes (always) |
| CTX:COMPACT | Most recent | NO |
| CTX:COMPACT | Previous | Yes |
| CTX:UPDATE | After subsequent COMPACT | Yes |
| STATE:ACK | After first useful block | Yes |
| ORCH:END | Never (terminal) | NO |

### Example
```
[CTX:PRUNE]
keep:[m5,m6,t2,f1]|pruned:[m1,m2,m3,m4,t1]
```

---

## 4. COMPACT — Global Compaction

**Trigger:** Every 20 messages
**Purpose:** Summarize cumulative history in few entries

### Format
```
[CTX:COMPACT]
summary:[layer=auth,status=done,layer=db,status=done,files:[db.py~1],layer=api,status=in_progress]
keep_active:[main.py~2,auth.py~1,db.py~1,api.py~1]
pruned_history:msg_22_to_40|pass_count:12|fail_count:2
```

### Effects
- PRUNE counter reset
- Previous history (msg 1-20) archived in summary
- Active files kept with current revision
- pass_count/fail_count counters are cumulative

---

## 5. FREEZE — Freezing

**Trigger:** ~100 messages (when COMPACT is no longer sufficient)
**Purpose:** Full counter reset, history archival

### Format
```
[CTX:FREEZE]
snapshot:[main.py~2,auth.py~1,db.py~1,api.py~1,routes.py~1,crud.py~2]
baseline:110
```

### Effects
- PRUNE and COMPACT counters restart from zero
- Previous history archived (not deleted)
- snapshot contains all active files with revision
- baseline = message number at freeze

---

## 6. Timeline Diagram

```
Msg 0:   [ARCH:PLAN]
Msg 1-4: BUILD/EXEC/DONE, TEST/PASS
Msg 5:   [CTX:PRUNE]             ← first prune
Msg 6-9: BUILD/EXEC/DONE, TEST/PASS
Msg 10:  [CTX:PRUNE]
Msg 11-14: ...
Msg 15:  [CTX:PRUNE]
Msg 16-19: ...
Msg 20:  [CTX:COMPACT]           ← reset PRUNE counter
Msg 21-24: ...
Msg 25:  [CTX:PRUNE]             ← new cycle after COMPACT
...
Msg 100: [CTX:COMPACT] (last)
Msg 105: [CTX:PRUNE]
Msg 110: [CTX:FREEZE]            ← freeze, full reset
Msg 111+: new cycle with reset counters
```

---

## 7. Scalability — Status

The conformance fixture chains exercise chains up to 130 messages through
the parser, validator, and FSM (`python3 conformance/run.py`), confirming
the grammar and state machine hold at that length. This is not a
cross-model or empirical scalability benchmark: no cross-model testing has
been run, and no claim is made about a maximum message count in production
use. See [docs/benchmarks/comparison.md](../benchmarks/comparison.md) and
[conformance/Result.md](../../conformance/Result.md) for what has actually
been measured.
