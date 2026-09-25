# H2C v1.4 — Semantic Compression Protocol

> H2C is a block-based grammar for AI-to-AI communication. This file provides project-level H2C instructions for Claude Code standalone mode.
> For the full plugin experience with `/h2c:h2c` commands, install via: `/plugin install github:LuPaLa-Coder/H2C`

## When to Use H2C

Use H2C blocks when:
- The user asks to compress or optimize a prompt
- Tracing development tasks with structured BUILD/ARCH/TEST blocks
- Planning architecture with design constraints
- Running multi-agent orchestration with fix cycles
- The user explicitly requests H2C format

## Core Grammar

```
[TYPE:SUBTYPE]
key1:value|key2:value|...
```

**Types:** ARCH | BUILD | TEST | CTX | STATE | ORCH | SKILL
**Subtypes:** PLAN | EXEC | DONE | FIX | REVERT | NACK | RUN | PASS | FAIL | PRIMITIVES | UPDATE | PRUNE | COMPACT | FREEZE | NEGOTIATE | FINDINGS | ACK | END | PROMPT

**Rules:**
- Each block is exactly 2 lines: header `[TYPE:SUBTYPE]` + fields separated by `|`
- Lists use `[a,b,c]` — no spaces after commas
- File revisions use `file~N` format
- CTX fields prefix keys with `~`
- String values must NOT contain `:`, `|`, `\n`, `[`, `]`
- Zero text outside fields. Zero markdown in generation mode.

## Block Reference

### ARCH:PLAN
```
[ARCH:PLAN]
id:<kebab-case>|fw:<lang>|lib:<csv>|auth:<type>|notes:[...]
```
Required: `id`, `fw`. Optional: `lib`, `auth`, `pattern`, `tools`, `struct`, `deps`, `notes`.

### BUILD:EXEC / BUILD:DONE
```
[BUILD:EXEC]  id:<slug>|target:<file>|desc:<what>
[BUILD:DONE]  id:<slug>|diff:[file~N,+M]|rev:<N>
```

### TEST:RUN / TEST:PASS / TEST:FAIL
```
[TEST:RUN]   id:<slug>|cmd:<command>
[TEST:PASS]  id:<slug>|pass_count:<N>
[TEST:FAIL]  id:<slug>|error:<file:line|type>|cycle_id:<cid>|fail_count:<N>
```

### BUILD:FIX
```
[BUILD:FIX]
id:<slug>|target:<file>|base_rev:<N>|desc:<what>|cycle_id:<cid>|retry_n:<1-3>
```

### CTX:NEGOTIATE + STATE:ACK (Handshake, v1.4 mandatory)
```
[CTX:NEGOTIATE]
version:h2c_v1.4|capabilities:[PRUNE,COMPACT,FREEZE,NEGOTIATE,NACK]

[STATE:ACK]
protocol:h2c_v1.4
```

### STATE:FINDINGS
```
[STATE:FINDINGS]
id:<slug>|cause:<why>|action:<what>|impact:<effect>|risk:[<items>]
```

### ORCH:END
```
[ORCH:END]
final:complete|est_token:<N>
```

### Context Management
```
[CTX:PRUNE]   keep:[<ids>]|pruned:[<ids>]|reason:<why>
[CTX:COMPACT] summary:[<items>]|keep_active:[<files>]|pruned_history:<range>
[CTX:FREEZE]  snapshot:[<file~N>]|baseline:<msg_N>
```

## Core Rules

1. **Generation mode** (compress, plan, build, done, test, fix, negotiate, findings, compact, prune, end): emit ONLY the H2C block. Zero markdown.
2. **Analysis mode** (explain, validate, show stats): markdown allowed.
3. `id:` must be kebab-case, unique within the chain.
4. `cycle_id` REQUIRED in BUILD:FIX and TEST:FAIL.
5. `retry_n` 1-3 in BUILD:FIX. Max 3 retries per cycle_id.
6. **Zero invention**: only include fields derivable from the input.
7. Lists inline, max 5, no spaces: `[a,b,c]`.

## Example: NL brief → H2C block

Input: "Create a weather API in Python with FastAPI, use httpx, cache 10min, rate limit 60/min"

Output:
```
[ARCH:PLAN]
id:weather-api|fw:python3.11|lib:fastapi,httpx,cachetools|notes:[cache_TTL_10min,rate-limit_60req-min]
```

---

Full spec: SPEC.md | Python runtime: `pip install h2c` | Plugin: `/plugin install github:LuPaLa-Coder/H2C`
