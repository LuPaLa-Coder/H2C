# Architettura H2C Protocol

**Versione:** 1.0
**Stato:** DEFINITIVO
**Scopo:** Panoramica architetturale del protocollo H2C — modello a strati, componenti e flussi.

---

## 1. Modello a Strati

```
┌──────────────────────────────────────────────────────────┐
│                   STRATO APPLICATIVO                     │
│  Skills agente, logica di orchestrazione, routing        │
│  skills/h2c_architect.md, h2c_orchestrator.md, ...       │
├──────────────────────────────────────────────────────────┤
│                   STRATO SEMANTICO                       │
│  Grammatica blocchi H2C, opcode, AST, tipo/subtipo       │
│  SPEC.md, docs/specification/grammar.md                  │
├──────────────────────────────────────────────────────────┤
│              STRATO ORCHESTRAZIONE                       │
│  cycle_id, retry_n, PRUNE/COMPACT/FREEZE,                │
│  tracciamento stato, recovery errori                     │
│  docs/architecture/context-lifecycle.md                  │
├──────────────────────────────────────────────────────────┤
│                   STRATO TRASPORTO                       │
│  MCP, stdin/stdout, HTTP, WebSocket                      │
│  Serializzazione/deserializzazione blocchi               │
│  docs/ecosystem/integrations.md                          │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Pipeline Agente

H2C definisce un modello a 4 agenti:

```
┌───────────┐    ┌──────────────┐    ┌───────────┐
│ Architetto│───→│ Orchestratore│───→│  Builder  │
└───────────┘    └──────────────┘    └───────────┘
                      │                    │
                      │                    ▼
                      │              ┌──────────┐
                      │              │  Tester  │
                      │              └──────────┘
                      │                    │
                      ▼                    │
               [ORCH:END] ◄────────────────┘
```

### Ruoli

| Agente | Input | Output | Stato |
|--------|-------|--------|-------|
| **Architetto** | Prompt umano | ARCH:PLAN + STATE:ACK | INIT → PLANNED |
| **Orchestratore** | Blocchi agenti | Routing, CTX, ORCH:END | Qualsiasi → Qualsiasi |
| **Builder** | BUILD:EXEC / FIX | BUILD:DONE | BUILDING → BUILT |
| **Tester** | TEST:RUN | TEST:PASS / FAIL | TESTING → TEST_PASS/FAIL |

---

## 3. Ciclo di Vita Messaggio

```
1. Ricezione blocco da strato trasporto
2. Parsing blocco (→ validazione EBNF)
3. Risoluzione tipo/subtipo (→ dispatcher)
4. Esecuzione azione (→ logica agente)
5. Transizione stato (→ macchina stati)
6. Emissione blocco su strato trasporto
7. Gestione contesto (PRUNE/COMPACT/FREEZE)
```

---

## 4. Gestione Errori

| Errore | Comportamento |
|--------|---------------|
| Blocco malformato | Scartato, ORCH:END con errore |
| retry_n > 3 | ORCH:END final:error |
| cycle_id non trovato | Warning, inferenza da contesto |
| Campo mancante REQUIRED | Blocco invalido |
| Test fallito senza FIX | Ciclo non gestito, ORCH:END |

---

## 5. Metriche di Sistema

| Metrica | Fonte | Scopo |
|---------|-------|-------|
| msg_counter | Contatore globale | Trigger PRUNE/COMPACT/FREEZE |
| retry_n | Per cycle_id | Limite tentativi |
| fail_count | Per cycle_id | Tracciamento errori |
| pass_count | Per cycle_id | Tracciamento successi |
| est_token | Self-report in ORCH:END | Stima costo |
| token_risparmio | Calcolato vs NL | Benchmark efficienza |
