# H2C Block Reference

**Version:** 1.3
**Status:** COMPLETE
**Purpose:** Quick reference guide for all H2C blocks, fields, rules, and patterns.

---

## Block Index

| Type | Subtype | Role | Mandatory |
|------|---------|------|:---------:|
| ARCH | PLAN | Architectural plan | Yes (1 per chain) |
| BUILD | EXEC | Implementation request | Yes |
| BUILD | DONE | Implementation completed | Yes |
| BUILD | FIX | Correction request | If TEST:FAIL |
| BUILD | REVERT | Revision rollback | Rare |
| TEST | RUN | Test request | Yes |
| TEST | PASS | Test passed | Either PASS or FAIL |
| TEST | FAIL | Test failed | Either FAIL or PASS |
| CTX | PRIMITIVES | Initial state snapshot | Yes (chains >5 msgs) |
| CTX | UPDATE | Layer update | Every layer change |
| CTX | PRUNE | Active window cleanup | Every 5 msgs |
| CTX | COMPACT | History compaction | Every 20 msgs |
| CTX | FREEZE | Baseline freeze | ~100 msgs |
| STATE | FINDINGS | Analysis result | Optional |
| STATE | ACK | Protocol acknowledgment | 1x (after PLAN) |
| ORCH | END | Cycle closure | Yes (1 per chain) |
| SKILL | PROMPT | Agent definition | Skills |

---

## Block Details

### ARCH:PLAN
```
Purpose:   Translate human prompt into structured plan
Emitted by: Architect
Received by: Orchestrator
Frequency: 1 per chain (rare: 2-3 if scenario changes)

Fields:
  id:<string>         Unique plan identifier
  fw:<string>         Target framework/language
  lib:<string>        Libraries (comma-separated)
  auth:<string>       Authentication scheme
  pattern:<string>    Architectural pattern
  tools:<list>        Tools/functionalities
  struct:<list>       File structure
  deps:<string>       External dependencies
  notes:<list>        Additional notes
```

### BUILD:EXEC
```
Purpose:   Request implementation of a component
Emitted by: Orchestrator
Received by: Builder
Frequency: 1 per component

Fields:
  id:<string>         Build identifier
  target:<string>     File/component target
  after:<list>        DAG dependencies (prerequisite ids)
  desc:<string>       Implementation description
  cmd:<string>        Build command (e.g. dotnet build)
```

### BUILD:DONE
```
Purpose:   Notify implementation completion
Emitted by: Builder
Received by: Orchestrator
Frequency: 1 per BUILD:EXEC or BUILD:FIX

Fields:
  id:<string>         Matches BUILD:EXEC.id
  diff:<list_rev>     Changes [file~rev,+lines,file~rev,-lines]
  rev:<int>           File revision (default 1)
  notes:<list>        Implementation notes
  cycle_id:<string>   If emitted for FIX
```

### BUILD:FIX
```
Purpose:   Request correction on implementation
Emitted by: Orchestrator
Received by: Builder
Frequency: 1 per fix cycle

Fields:
  id:<string>         Fix identifier
  target:<string>     File to correct
  base_rev:<int>      Base revision to apply fix on
  desc:<string>       Error/correction description
  cycle_id:<string>   Fix cycle identifier
  retry_n:<int>       Attempt number (1-3)
  cmd:<string>        Verification command
```

### TEST:RUN
```
Purpose:   Execute test suite
Emitted by: Orchestrator
Received by: Tester
Frequency: 1 per suite

Fields:
  id:<string>         Test identifier
  cmd:<string>        Command to execute
```

### TEST:PASS / TEST:FAIL
```
Purpose:   Notify test outcome
Emitted by: Tester
Received by: Orchestrator
Frequency: 1 per TEST:RUN

Fields (PASS):
  id:<string>         Matches TEST:RUN.id
  cycle_id:<string>   Required if closing a fix cycle
  pass_count:<int>    Passed counter

Fields (FAIL):
  id:<string>         Matches TEST:RUN.id
  error:<string>      Error message
  cycle_id:<string>   Mandatory (opens fix cycle)
  fail_count:<int>    Failed counter
  pass_count:<int>    Passed counter (partial)
```

### CTX:PRUNE
```
Purpose:   Purge unnecessary messages from active window
Emitted by: Any agent
Frequency: Every 5 messages

Fields:
  keep:<string/list>  "last_N" or list of ids to keep
  pruned:<list>       List of removed ids
  reason:<string>     Pruning explanation
```

### CTX:COMPACT
```
Purpose:   Compact cumulative history into summary
Emitted by: Orchestrator
Frequency: Every 20 messages

Fields:
  summary:<list>      Summary (max 5 entries)
  keep_active:<list>  Files still under active modification
  pruned_history:<str> Pruned history range
  pass_count:<int>    Cumulative counter
  fail_count:<int>    Cumulative counter
```

### CTX:FREEZE
```
Purpose:   Freeze baseline when COMPACT is insufficient
Emitted by: Orchestrator
Frequency: Once, ~100 messages

Fields:
  snapshot:<list>     All active files with revision
  baseline:<int>      Message number at freeze
```

---

## Flow Patterns

### Base Flow (no errors)
```
ARCH:PLAN → BUILD:EXEC → BUILD:DONE → TEST:RUN → TEST:PASS → ORCH:END
```

### Fix Flow
```
TEST:RUN → TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:RUN → TEST:PASS
```

### Multi-Step Flow with DAG
```
BUILD:EXEC (m1) ──→ BUILD:EXEC (m2) ──→ BUILD:EXEC (m4)
      │                                         │
      └──→ BUILD:EXEC (m3) ─────────────────────┘
```

### Long Flow with Context Lifecycle
```
ARCH:PLAN → BUILD:EXEC × N → CTX:PRUNE → BUILD:EXEC × N → CTX:PRUNE
→ CTX:COMPACT → BUILD:EXEC × N → ... → CTX:FREEZE → ... → ORCH:END
```
