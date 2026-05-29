# Specifica Runtime Agenti H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Definire il modello di runtime per l'esecuzione di catene H2C tra agenti AI.

---

## 1. Modello di Runtime

```
┌──────────────────────────────────────────────┐
│             H2C Agent Runtime                │
│                                              │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Parser   │──→│ State    │──→│ Dispatcher│ │
│  │ (EBNF)   │   │ Machine  │   │ (Router)  │ │
│  └──────────┘   └──────────┘   └───────────┘ │
│       │              │               │       │
│       ▼              ▼               ▼       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │Validator │   │Context   │   │Skills    │  │
│  │(Regole)  │   │Manager   │   │Loader    │  │
│  └──────────┘   └──────────┘   └──────────┘  │
└──────────────────────────────────────────────┘
```

---

## 2. Componenti

### Parser
- Input: testo H2C
- Output: AST (Albero Sintattico Astratto)
- Validazione: EBNF grammar + vincoli
- Errori: blocco malformato → scartato + log

### State Machine
- Input: AST
- Output: nuova transizione stato
- Tabella: vedi [docs/specification/semantics.md](../specification/semantics.md)

### Dispatcher
- Input: AST + stato corrente
- Output: routing a skill/agente corretto
- Logica: tipo/subtipo → handler

### Context Manager
- Mantiene: msg_counter, cycle_registry, revision_table
- Trigger: PRUNE ogni 5, COMPACT ogni 20, FREEZE ~100
- Reset: dopo COMPACT e FREEZE

### Validator
- Regole: vincoli operazionali (retry_n ≤ 3, cycle_id match, ...)
- Output: blocco valido/invalido + warning

---

## 3. Architettura Futura: Compilatore H2C

```
H2C Source Code
      │
      ▼
┌─────────────┐
│   Parser    │  AST
└──────┬──────┘
       ▼
┌─────────────┐
│   Analyzer  │  Type checking, semantic analysis
└──────┬──────┘
       ▼
┌─────────────┐
│   Optimizer │  Block fusion, compression
└──────┬──────┘
       ▼
┌─────────────┐
│   Codegen   │  Target: JSON, MCP, gRPC, custom
└─────────────┘
```

### Target del Transpiler
- JSON → interoperabilità con sistemi esistenti
- MCP → trasporto nativo su Model Context Protocol
- gRPC → alta performance per runtime agenti
- NL → debug, logging, human-readable audit trail

---

## 4. Binding di Trasporto

| Binding | Mezzo | Caso d'Uso |
|---------|-------|------------|
| stdin/stdout | Pipe UNIX | Agenti locali, CLI |
| HTTP POST | REST | API gateway, microservizi |
| WebSocket | Bidirezionale | Streaming, long-lived |
| MCP | Tool call | Framework agnostic |
| File system | File .h2c | Batch, debug, riproduzione |
