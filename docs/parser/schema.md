# Schema Tipizzato — Protocollo H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Definire lo schema JSON per tutti i blocchi H2C — validazione, autocompletamento e supporto tooling.

---

## 1. Schema Base

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/PaoEng/H2C/schemas/h2c.json",
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

## 2. Schema per Blocco

### 2.1 ARCH:PLAN

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Non vuoto, unico per catena |
| `fw` | string | REQUIRED | Framework/linguaggio |
| `lib` | string | OPTIONAL | Separati da virgola |
| `auth` | string | OPTIONAL | Schema autenticazione |
| `pattern` | string | OPTIONAL | Pattern architetturale |
| `tools` | list | OPTIONAL | Max 5 elementi |
| `struct` | list | OPTIONAL | Percorsi file |
| `deps` | string | OPTIONAL | Dipendenze esterne |
| `notes` | list | OPTIONAL | Max 5 elementi |

### 2.2 BUILD:EXEC

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Non vuoto, unico |
| `target` | string | REQUIRED | Percorso file/componente |
| `after` | list | OPTIONAL | ID dipendenze DAG |
| `desc` | string | OPTIONAL | Descrizione implementazione |
| `cmd` | string | OPTIONAL | Comando di build |

### 2.3 BUILD:DONE

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Matcha BUILD:EXEC.id |
| `diff` | list_rev | REQUIRED | Formato: `[file~N,+M,file~N,-K]` |
| `rev` | integer | OPTIONAL | Default 1 |
| `notes` | list | OPTIONAL | Max 3 elementi |
| `cycle_id` | string | OPTIONAL | REQUIRED se da FIX |

### 2.4 BUILD:FIX

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Non vuoto, unico |
| `target` | string | REQUIRED | File da correggere |
| `base_rev` | integer | REQUIRED | Revisione base |
| `desc` | string | REQUIRED | Descrizione errore |
| `cycle_id` | string | REQUIRED | Lega a TEST:FAIL |
| `retry_n` | integer | OPTIONAL | Range [1..3] |
| `cmd` | string | OPTIONAL | Comando verifica |

### 2.5 BUILD:REVERT

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Non vuoto, unico |
| `target` | string | REQUIRED | File da ripristinare |
| `to_rev` | integer | REQUIRED | Revisione target |

### 2.6 TEST:RUN / PASS / FAIL

| Campo | Tipo | Obbligo | Blocco | Vincoli |
|-------|------|---------|--------|---------|
| `id` | string | REQUIRED | Tutti | Unico per catena |
| `cmd` | string | REQUIRED | RUN | Comando test |
| `cycle_id` | string | REQUIRED in FAIL, OPT in PASS | FAIL/PASS | Lega ciclo fix |
| `error` | string | REQUIRED | FAIL | Messaggio errore |
| `pass_count` | integer | OPTIONAL | PASS/FAIL | Cumulativo |
| `fail_count` | integer | OPTIONAL | FAIL | Per cycle_id |

### 2.7 Blocchi CTX

| Campo | Tipo | Obbligo | Blocco | Vincoli |
|-------|------|---------|--------|---------|
| `~task` | string | REQUIRED | PRIMITIVES | Descrizione task |
| `~constraint` | string | REQUIRED | PRIMITIVES | Contesto/vincoli |
| `~goal` | string | REQUIRED | PRIMITIVES | Obiettivo |
| `~form` | string | OPTIONAL | PRIMITIVES | Forma output preferita |
| `~progress` | string | REQUIRED | UPDATE | `layer=N\|status=X` |
| `~next` | string | REQUIRED | UPDATE | Prossimo passo |
| `~active_files` | list_rev | OPTIONAL | UPDATE | File in gioco |
| `keep` | string/list | REQUIRED | PRUNE | `last_N` o `[id,...]` |
| `pruned` | list | REQUIRED | PRUNE | ID da potare |
| `reason` | string | OPTIONAL | PRUNE | Motivazione |
| `summary` | list | REQUIRED | COMPACT | Max 5 voci |
| `keep_active` | list_rev | REQUIRED | COMPACT | File attivi |
| `pruned_history` | string | REQUIRED | COMPACT | Range `"msgN_to_M"` |
| `pass_count` | integer | OPTIONAL | COMPACT | Cumulativo |
| `fail_count` | integer | OPTIONAL | COMPACT | Cumulativo |
| `snapshot` | list_rev | REQUIRED | FREEZE | Tutti i file attivi |
| `baseline` | integer | REQUIRED | FREEZE | Numero messaggio |

### 2.8 STATE:FINDINGS

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | ID finding unico |
| `cause` | string | RACCOMANDATO | Causa radice |
| `action` | string | RACCOMANDATO | Azione correttiva |
| `impact` | string | RACCOMANDATO | Impatto misurato |
| `risk` | list | OPTIONAL | Tag rischio |
| `pattern` | string | OPTIONAL | Pattern corrisposto |
| `components` | list | OPTIONAL | Componenti coinvolti |
| `note` | string | OPTIONAL | Nota libera |

### 2.9 STATE:ACK

| Campo | Tipo | Obbligo | Vincolo |
|-------|------|---------|---------|
| `protocol` | string | REQUIRED | Deve essere `h2c_v1.2` |

### 2.10 ORCH:END

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `final` | enum | REQUIRED | `complete`\|`error`\|`timeout` |
| `est_token` | integer | OPTIONAL | Stima self-report |
| `fail_count` | integer | OPTIONAL | Conteggio fallimenti finale |
| `pass_count` | integer | OPTIONAL | Conteggio successi finale |

### 2.11 SKILL:PROMPT

| Campo | Tipo | Obbligo | Vincoli |
|-------|------|---------|---------|
| `id` | string | REQUIRED | Identificativo skill |
| `role` | string | REQUIRED | Descrizione ruolo agente |
| `attivazione` | string | REQUIRED | Frase/comando di attivazione |

## 3. Schema JSON Completo

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/PaoEng/H2C/schemas/block.json",
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
