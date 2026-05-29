# Modello Runtime Agenti H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Specificare il modello di esecuzione per agenti H2C — scheduling, routing, error recovery.

---

## 1. Ciclo di Esecuzione Agente

```
┌──────────────────────┐
│    Attesa Input      │
│  (listen sul canale) │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   Parsing Blocco     │
│  (grammatica EBNF)   │
└──────────┬───────────┘
           ▼
┌────────────────────────┐
│   Validazione          │
│  (regole operazionali) │
└──────────┬─────────────┘
    ┌──────┴──────┐
    ▼             ▼
┌──────────┐ ┌───────────┐
│ Valido   │ │  Invalido │
└────┬─────┘ └────┬──────┘
     ▼            ▼
┌──────────┐ ┌───────────┐
│ Execute   │ │ Reject + │
│ Action    │ │ Log      │
└────┬─────┘ └───────────┘
     ▼
┌───────────────────────┐
│   Emetti Output       │
│  (prossimo blocco)    │
└───────────────────────┘
```

---

## 2. Routing

| Blocco Input | Mittente | Destinatario | Blocco Output |
|-------------|----------|--------------|---------------|
| ARCH:PLAN | Architetto | Orchestratore | BUILD:EXEC |
| BUILD:EXEC | Orchestratore | Builder | BUILD:DONE |
| BUILD:DONE | Builder | Orchestratore | TEST:RUN o BUILD:EXEC |
| BUILD:FIX | Orchestratore | Builder | BUILD:DONE |
| TEST:RUN | Orchestratore | Tester | TEST:PASS/FAIL |
| TEST:PASS | Tester | Orchestratore | ORCH:END o BUILD:EXEC |
| TEST:FAIL | Tester | Orchestratore | BUILD:FIX |
| CTX:* | Orchestratore | Broadcast | — |

---

## 3. Error Recovery

| Fallimento | Comportamento |
|------------|---------------|
| Parsing fallito | Blocco scartato, log errore |
| Validazione fallita | Warning, tenta recovery |
| Timeout esecuzione | ORCH:END final:timeout |
| retry_n > 3 | ORCH:END final:error |
| cycle_id duplicato | Merge context, warning |
| Campo mancante REQUIRED | ORCH:END final:error |
