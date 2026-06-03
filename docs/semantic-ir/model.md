# H2C Semantic IR Model

**Version:** 1.0
**Status:** DRAFT
**Scope:** Define the semantic Intermediate Representation (IR) model for retrieval, indexing, and reuse of H2C chains.

---

## 1. What is Semantic IR

The H2C Semantic IR is an intermediate representation that captures the meaning of an H2C block chain in an indexable and retrievable form. It serves as a bridge between the wire-format H2C and retrieval systems (vector DB, search, LLM context).

---

## 2. Data Model

```json
{
  "chain_id": "uuid",
  "protocol_version": "1.3",
  "created_at": "ISO8601",
  "model": "claude-sonnet-4.6",
  "messages": [
    {
      "seq": 1,
      "type": "ARCH:PLAN",
      "opcode": "ARCH_PLAN",
      "semantic_hash": "sha256",
      "fields": {
        "id": "...",
        "fw": "python3.11",
        "lib": ["fastapi", "httpx"],
        "pattern": "router,service",
        "struct": ["main.py", "routers/"},
        "deps": ["openweathermap"]
      },
      "embedding": [0.1, 0.2, ...],
      "tokens": 55,
      "tokens_nl_equivalent": 170
    }
  ],
  "metrics": {
    "total_tokens": 200,
    "total_tokens_nl": 5000,
    "token_savings_pct": 96,
    "chain_length": 15,
    "fix_cycles": 0,
    "context_operations": {
      "prune": 3,
      "compact": 1,
      "freeze": 0
    }
  },
  "tags": ["python", "fastapi", "weather", "api-key"]
}
```

---

## 3. Fields for Retrieval

| Field | Type | Usage |
|-------|------|-------|
| `chain_id` | uuid | Unique reference |
| `type` | string | Filter by block type |
| `fields.fw` | string | Filter by framework |
| `fields.lib` | list | Search by library |
| `fields.pattern` | string | Search by architectural pattern |
| `semantic_hash` | hash | Deduplication |
| `embedding` | vector[float] | Semantic similarity |
| `metrics.token_savings_pct` | float | Efficiency filter |
| `tags` | list[string] | Categorization tags |

---

## 4. Use Cases

- **Retrieval-Augmented Generation (RAG)**: Retrieve H2C chains similar to a given prompt
- **Agent Knowledge Base**: Store and search completed chains
- **Transfer Learning**: Reuse architectural plans from previous chains
- **Benchmarking**: Compare efficiency across models and protocol versions
- **Audit**: Track architectural decisions and fix cycles
