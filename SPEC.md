# H2C Protocol - Specification v1.3

## 1. Formal Grammar (BNF)

```
<message>      ::= <block>
<block>        ::= "[" <type> ":" <subtype> "]" "\n" <fields>
<fields>       ::= <field> ("|" <field>)*
<field>        ::= <key> ":" <value>
<key>          ::= [a-zA-Z_][a-zA-Z0-9_]*
<value>        ::= <int> | <rev> | <list> | <string>
<string>       ::= [^\|\n\[\]]+
<list>         ::= "[" <string> ("," <string>)* "]"
<rev>          ::= <string> "~" <int>
<int>          ::= [0-9]+
<signed_int>   ::= ["+" | "-"] <int>

<type>         ::= "ARCH" | "BUILD" | "TEST" | "CTX" | "STATE" | "ORCH" | "SKILL"
<subtype>      ::= "PLAN" | "EXEC" | "DONE" | "FIX" | "REVERT"
                 | "RUN" | "PASS" | "FAIL"
                 | "PRIMITIVES" | "UPDATE" | "PRUNE" | "COMPACT" | "FREEZE"
                 | "FINDINGS" | "ACK"
                 | "END" | "PROMPT"
```

### 1.1 Separators

| Sep | Usage | Regex |
|-----|-------|-------|
| `:` | key:value | `[^:\\|\\n\\[\\]]+:[^:\\|\\n\\[\\]]+` |
| `\|` | between fields | `\|` |
| `,` | list item separator | `,` |
| `[]` | block and list delimiters | `\[...\]` |
| `~` | CTX field prefix and file revisions | `~` |

### 1.2 Conventions

- Inline lists: max 5 items, no spaces after comma
- REQUIRED fields: must be present or block is invalid
- OPTIONAL fields: omitted if not applicable
- Field order: irrelevant for parsing
- Zero text outside fields: violation = block discarded (newlines between blocks allowed)

---

## 2. Standard Blocks

### 2.1 ARCH:PLAN

```
[ARCH:PLAN]
REQUIRED: id:<string>|fw:<string>
OPTIONAL: lib:<string>|auth:<string>|pattern:<string>|tools:<list>|struct:<list>|deps:<string>|notes:<list>
```

### 2.2 BUILD:EXEC

```
[BUILD:EXEC]
REQUIRED: id:<string>|target:<string>
OPTIONAL: after:<list>|desc:<string>|cmd:<string>
```
- `after:`: list of prerequisite ids (explicit DAG)
- `cmd:`: build command executed (optional, e.g. `dotnet build`, `npm run build`)

### 2.3 BUILD:DONE

```
[BUILD:DONE]
REQUIRED: id:<string>|diff:<list_rev>
OPTIONAL: rev:<int>|notes:<list>|cycle_id:<string>
```
- `diff:`: list of `<rev>` and `<signed_int>`, e.g. `[file~N,+M,file2~N,-K]`
- `rev:`: defaults to 1 if omitted
- `cycle_id:`: links this DONE to the FIX that generated it

### 2.4 BUILD:FIX

```
[BUILD:FIX]
REQUIRED: id:<string>|target:<string>|base_rev:<int>|desc:<string>
REQUIRED: cycle_id:<string>
OPTIONAL: retry_n:<int>|cmd:<string>
```
- `cycle_id:`: uniquely identifies the fix cycle (e.g. `fix-qdrant-collection`)
- `retry_n:`: progressive counter 1-3. If >3 or omitted: error
- `base_rev:`: file revision to apply the fix on

### 2.5 BUILD:REVERT

```
[BUILD:REVERT]
REQUIRED: id:<string>|target:<string>|to_rev:<int>
```

### 2.6 TEST:RUN / TEST:PASS / TEST:FAIL

```
[TEST:RUN]
REQUIRED: id:<string>|cmd:<string>

[TEST:PASS]
REQUIRED: id:<string>
CASE: cycle_id:<string> REQUIRED when closing a fix cycle (otherwise OPTIONAL)
OPTIONAL: pass_count:<int>

[TEST:FAIL]
REQUIRED: id:<string>|error:<string>|cycle_id:<string>
OPTIONAL: fail_count:<int>|pass_count:<int>
```
- `cycle_id:` in TEST:FAIL is always REQUIRED (opens or continues a fix cycle)
- `cycle_id:` in TEST:PASS is REQUIRED only when closing an open fix cycle (cycle_id present in a prior BUILD:FIX not yet closed); optional otherwise
- `fail_count:`: absolute counter per cycle_id (resets when cycle_id changes)

---

## 3. Context Blocks

### 3.1 CTX:PRIMITIVES

```
[CTX:PRIMITIVES]
~task:<string>
~constraint:<string>
~goal:<string>
OPTIONAL: ~form:<string>
```
Initial state snapshot. Fields prefixed with `~`.

### 3.2 CTX:UPDATE

```
[CTX:UPDATE]
REQUIRED: ~progress:<layer=N,status=X>
REQUIRED: ~next:<string>
OPTIONAL: ~active_files:<list_rev>
```
- `~progress:`: current layer and status (done/in_progress/blocked), separator `,`
- `~next:`: next step
- `~active_files:`: files currently in play with revision
- **NOTE**: `~pruned_edges` REMOVED in v1.2. Use CTX:PRUNE as single authority for pruning

### 3.3 CTX:PRUNE

```
[CTX:PRUNE]
REQUIRED: keep:<"last_N" | list_ids>
REQUIRED: pruned:<list_ids>
OPTIONAL: reason:<string>
```
- **Mandatory every 5 messages** (global counter)
- `keep:`: MUST include at least: latest ARCH:PLAN, all open BUILD:FIX, latest COMPACT
- `pruned:`: MUST include BUILD:EXEC whose BUILD:DONE was already emitted, TEST:RUN with known outcome
- `reason:`: optional, explains why certain messages were pruned

**Pruning rules (RULES, not suggestions):**

| Block | Condition | Prunable? |
|-------|-----------|-----------|
| ARCH:PLAN | Subsequent COMPACT exists | ✅ Yes |
| ARCH:PLAN | Last emitted, no COMPACT | ❌ NO |
| BUILD:EXEC | Corresponding BUILD:DONE emitted | ✅ Yes |
| BUILD:EXEC | BUILD:DONE NOT yet emitted | ❌ NO |
| BUILD:FIX | cycle_id still open | ❌ NO |
| BUILD:FIX | cycle_id closed (TEST:PASS) | ✅ Yes |
| BUILD:DONE | Subsequent COMPACT exists | ✅ Yes |
| TEST:RUN | Outcome (PASS/FAIL) emitted | ✅ Yes |
| TEST:RUN | Outcome NOT yet emitted | ❌ NO |
| TEST:PASS/FAIL | Subsequent COMPACT exists | ✅ Yes |
| CTX:PRUNE | After emission | ✅ Yes (always) |
| CTX:COMPACT | Most recent | ❌ NO |
| CTX:COMPACT | Previous (not most recent) | ✅ Yes |
| CTX:UPDATE | After subsequent COMPACT | ✅ Yes |
| STATE:ACK | After first useful block | ✅ Yes |
| STATE:FINDINGS | After subsequent COMPACT | ✅ Yes |
| ORCH:END | Never (terminal) | ❌ NO |

### 3.4 CTX:COMPACT

```
[CTX:COMPACT]
REQUIRED: summary:<list>
REQUIRED: keep_active:<list_rev>
REQUIRED: pruned_history:<range_string>
OPTIONAL: pass_count:<int>|fail_count:<int>
```
- **Mandatory every 20 messages**
- `summary:`: max 5 entries, format `layer=N,status=X,files:[f1~rev]`
- `keep_active:`: files still under active modification
- `pruned_history:`: exact range e.g. `msg2_to_19`
- After COMPACT: PRUNE counter restarts from zero

### 3.5 CTX:FREEZE

```
[CTX:FREEZE]
REQUIRED: snapshot:<list_rev>
REQUIRED: baseline:<int>
```
- Emitted ONCE, when COMPACT is no longer sufficient (~100 msgs)
- `snapshot:`: all active files with their current revision
- `baseline:`: message number at freeze
- After FREEZE: PRUNE and COMPACT counters restart from zero
- Previous history is archived (not deleted)

---

## 4. STATE:FINDINGS / STATE:ACK

```
[STATE:FINDINGS]
REQUIRED: id:<string>
RECOMMENDED: cause:<string>|action:<string>|impact:<string>
OPTIONAL: risk:<list>|pattern:<string>|components:<list>|note:<string>
```
- `id:`: unique finding identifier (e.g. `s1.1`, `e2e.3`)
- `cause:`: root cause description
- `action:`: corrective action taken
- `impact:`: measured or estimated impact
- If grammar is not structured (free text), parser emits warning but not error

```
[STATE:ACK]
REQUIRED: protocol:h2c_v1.3
```

---

## 5. ORCH:END

```
[ORCH:END]
REQUIRED: final:<"complete"|"error"|"timeout">
OPTIONAL: est_token:<int>|fail_count:<int>|pass_count:<int>
```
- `final:`: "complete" (success), "error" (max retry), "timeout"
- `est_token:`: estimated token consumption (self-reported, non-normative). Recommended: tiktoken (cl100k_base) or fallback len/3.2

---

## 6. SKILL:PROMPT

Specialized agent definition. Format unchanged.

```
[SKILL:PROMPT]
id:<string>
role:<string>
activation:<string>
```

---

## 7. Operational Rules (NORMATIVE)

1. **CTX:PRUNE** every 5 messages — follow table §3.3
2. **CTX:COMPACT** every 20 messages — after COMPACT, PRUNE counter restarts
3. **CTX:UPDATE** mandatory on every layer change
4. **cycle_id** mandatory in BUILD:FIX → TEST:FAIL → BUILD:DONE (same string)
5. **retry_n** in BUILD:FIX: 1-3. If >3, cycle terminates with ORCH:END final:error
6. **fail_count** per cycle_id: resets when cycle_id changes
7. **after:** DAG — cycle detection: if A.after includes B and B.after includes A, block is invalid

---

## 8. Compatibility

- v1.0: all blocks remain valid
- v1.1: v1.1 blocks valid; `~pruned_edges` deprecated but ignored
- v1.2: MINOR breaking change: `cycle_id` mandatory in BUILD:FIX
- v1.3: Formal EBNF (ISO 14977), AST model, semantic opcodes, state machine complete. Fully backward-compatible with v1.2 blocks; `protocol` field advances to `h2c_v1.3`
- Parser v1.0/v1.1: ignores cycle_id if present, processes the rest
