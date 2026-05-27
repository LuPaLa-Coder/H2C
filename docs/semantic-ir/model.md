# Modello IR Semantico H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Definire il modello di Intermediate Representation (IR) semantico per retrieval, indicizzazione e riutilizzo di catene H2C.

---

## 1. Cos'è l'IR Semantico

L'IR Semantico H2C è una rappresentazione intermedia che cattura il significato di una catena di blocchi H2C in forma indicizzabile e recuperabile. Serve come ponte tra il formato wire H2C e sistemi di retrieval (vector DB, search, LLM context).

---

## 2. Modello Dati

```json
{
  "chain_id": "uuid",
  "protocol_version": "1.2",
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

## 3. Campi per Retrieval

| Campo | Tipo | Utilizzo |
|-------|------|----------|
| `chain_id` | uuid | Referenza univoca |
| `type` | string | Filtro per tipo blocco |
| `fields.fw` | string | Filtro per framework |
| `fields.lib` | list | Ricerca per libreria |
| `fields.pattern` | string | Ricerca per pattern architetturale |
| `semantic_hash` | hash | Deduplicazione |
| `embedding` | vector[float] | Similarità semantica |
| `metrics.token_savings_pct` | float | Filtro efficienza |
| `tags` | list[string] | Tag per categorizzazione |

---

## 4. Casi d'Uso

- **Retrieval-Augmented Generation (RAG)**: Recuperare catene H2C simili a un prompt dato
- **Knowledge Base Agenti**: Archiviare e ricercare catene completate
- **Transfer Learning**: Riutilizzare piani architetturali da catene precedenti
- **Benchmarking**: Confrontare efficienza tra modelli e versioni protocollo
- **Audit**: Tracciare decisioni architetturali e cicli fix
