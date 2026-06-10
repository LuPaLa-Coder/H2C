# Typed Schema — H2C Protocol

**Version:** 1.0
**Status:** DRAFT
**Scope:** Define the JSON schema for all H2C blocks — validation, autocompletion, and tooling support.

---

## 1. Base Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/LuPaLa-Coder/H2C/schemas/h2c.json",
  "title": "Blocco Protocollo H2C",
  "description": "Schema per i blocchi del protocollo H2C Semantic Compression",
  "type": "object",
  "properties": {
    "type": {
      "type": "string",
      "enum": ["ARCH", "BUILD", "TEST", "CTX", "STATE", "ORCH", "SKILL"]
    },
    "subtype": {
      "type": "string",
      "enum": [
        "PLAN", "EXEC", "DONE", "FIX", "REVERT",
        "RUN", "PASS", "FAIL",
        "PRIMITIVES", "UPDATE", "PRUNE", "COMPACT", "FREEZE",
        "FINDINGS", "ACK",
        "END", "PROMPT"
      ]
    },
    "fields": {
      "type": "array",
      "items": {"$ref": "#/definitions/field"}
    }
  },
  "required": ["type", "subtype", "fields"]
}
```

## 2. Schema by Block

### 2.1 ARCH:PLAN

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Non-empty, unique per chain |
| `fw` | string | REQUIRED | Framework/language |
| `lib` | string | OPTIONAL | Comma separated |
| `auth` | string | OPTIONAL | Authentication scheme |
| `pattern` | string | OPTIONAL | Architectural pattern |
| `tools` | list | OPTIONAL | Max 5 elements |
| `struct` | list | OPTIONAL | File paths |
| `deps` | string | OPTIONAL | External dependencies |
| `notes` | list | OPTIONAL | Max 5 elements |

### 2.2 BUILD:EXEC

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Non-empty, unique |
| `target` | string | REQUIRED | File path / component |
| `after` | list | OPTIONAL | DAG dependency IDs |
| `desc` | string | OPTIONAL | Implementation description |
| `cmd` | string | OPTIONAL | Build command |

### 2.3 BUILD:DONE

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Matches BUILD:EXEC.id |
| `diff` | list | REQUIRED | Format: `[file~N,+M,file~N,-K]` (items: revision \| signed_int) |
| `rev` | integer | OPTIONAL | Default 1 |
| `notes` | list | OPTIONAL | Max 3 elements |
| `cycle_id` | string | OPTIONAL | REQUIRED if from FIX |

### 2.4 BUILD:FIX

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Non-empty, unique |
| `target` | string | REQUIRED | File to fix |
| `base_rev` | integer | REQUIRED | Base revision |
| `desc` | string | REQUIRED | Error description |
| `cycle_id` | string | REQUIRED | Links to TEST:FAIL |
| `retry_n` | integer | OPTIONAL | Range [1..3] |
| `cmd` | string | OPTIONAL | Verify command |

### 2.5 BUILD:REVERT

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Non-empty, unique |
| `target` | string | REQUIRED | File to restore |
| `to_rev` | integer | REQUIRED | Target revision |

### 2.6 TEST:RUN / PASS / FAIL

| Field | Type | Requirement | Block | Constraints |
|-------|------|-------------|-------|-------------|
| `id` | string | REQUIRED | All | Unique per chain |
| `cmd` | string | REQUIRED | RUN | Test command |
| `cycle_id` | string | REQUIRED in FAIL, OPT in PASS | FAIL/PASS | Links fix cycle |
| `error` | string | REQUIRED | FAIL | Error message |
| `pass_count` | integer | OPTIONAL | PASS/FAIL | Cumulative |
| `fail_count` | integer | OPTIONAL | FAIL | Per cycle_id |

### 2.7 CTX Blocks

| Field | Type | Requirement | Block | Constraints |
|-------|------|-------------|-------|-------------|
| `~task` | string | REQUIRED | PRIMITIVES | Task description |
| `~constraint` | string | REQUIRED | PRIMITIVES | Context/constraints |
| `~goal` | string | REQUIRED | PRIMITIVES | Objective |
| `~form` | string | OPTIONAL | PRIMITIVES | Preferred output form |
| `~progress` | string | REQUIRED | UPDATE | `layer=N,status=X` |
| `~next` | string | REQUIRED | UPDATE | Next step |
| `~active_files` | list_rev | OPTIONAL | UPDATE | Files in play |
| `keep` | string/list | REQUIRED | PRUNE | `last_N` or `[id,...]` |
| `pruned` | list | REQUIRED | PRUNE | IDs to prune |
| `reason` | string | OPTIONAL | PRUNE | Motivation |
| `summary` | list | REQUIRED | COMPACT | Max 5 entries |
| `keep_active` | list_rev | REQUIRED | COMPACT | Active files |
| `pruned_history` | string | REQUIRED | COMPACT | Range `"msgN_to_M"` |
| `pass_count` | integer | OPTIONAL | COMPACT | Cumulative |
| `fail_count` | integer | OPTIONAL | COMPACT | Cumulative |
| `snapshot` | list_rev | REQUIRED | FREEZE | All active files |
| `baseline` | integer | REQUIRED | FREEZE | Message number |

### 2.8 STATE:FINDINGS

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Unique finding ID |
| `cause` | string | RECOMMENDED | Root cause |
| `action` | string | RECOMMENDED | Corrective action |
| `impact` | string | RECOMMENDED | Measured impact |
| `risk` | list | OPTIONAL | Risk tags |
| `pattern` | string | OPTIONAL | Matched pattern |
| `components` | list | OPTIONAL | Components involved |
| `note` | string | OPTIONAL | Free note |

### 2.9 STATE:ACK

| Field | Type | Requirement | Constraint |
|-------|------|-------------|------------|
| `protocol` | string | REQUIRED | Must be `h2c_v1.3` |

### 2.10 ORCH:END

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `final` | enum | REQUIRED | `complete`\|`error`\|`timeout` |
| `est_token` | integer | OPTIONAL | Self-report estimate |
| `fail_count` | integer | OPTIONAL | Final failure count |
| `pass_count` | integer | OPTIONAL | Final success count |

### 2.11 SKILL:PROMPT

| Field | Type | Requirement | Constraints |
|-------|------|-------------|-------------|
| `id` | string | REQUIRED | Skill identifier |
| `role` | string | REQUIRED | Agent role description |
| `activation` | string | REQUIRED | Activation phrase/command |

## 3. Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/LuPaLa-Coder/H2C/schemas/block.json",
  "title": "Blocco H2C",
  "definitions": {
    "field": {
      "type": "object",
      "properties": {
        "key": {"type": "string"},
        "value": {"type": "string"}
      },
      "required": ["key", "value"]
    },
    "block_arch_plan": {
      "type": "object",
      "properties": {
        "type": {"const": "ARCH"},
        "subtype": {"const": "PLAN"},
        "fields": {
          "type": "array",
          "contains": [
            {"$ref": "#/definitions/field_required", "properties": {"key": {"pattern": "^(id|fw)$"}}}
          ]
        }
      },
      "required": ["type", "subtype", "fields"]
    }
  },
  "oneOf": [
    {"$ref": "#/definitions/block_arch_plan"},
    {"$ref": "#/definitions/block_build_exec"},
    {"$ref": "#/definitions/block_build_done"},
    {"$ref": "#/definitions/block_build_fix"},
    {"$ref": "#/definitions/block_build_revert"},
    {"$ref": "#/definitions/block_test_run"},
    {"$ref": "#/definitions/block_test_pass"},
    {"$ref": "#/definitions/block_test_fail"},
    {"$ref": "#/definitions/block_ctx_primitives"},
    {"$ref": "#/definitions/block_ctx_update"},
    {"$ref": "#/definitions/block_ctx_prune"},
    {"$ref": "#/definitions/block_ctx_compact"},
    {"$ref": "#/definitions/block_ctx_freeze"},
    {"$ref": "#/definitions/block_state_findings"},
    {"$ref": "#/definitions/block_state_ack"},
    {"$ref": "#/definitions/block_orch_end"},
    {"$ref": "#/definitions/block_skill_prompt"}
  ]
}
```
