# Riferimento Blocchi H2C

**Versione:** 1.2
**Stato:** COMPLETO
**Scopo:** Guida di riferimento rapido per tutti i blocchi H2C, campi, regole e pattern.

---

## Indice Blocchi

| Tipo | Sottotipo | Ruolo | Obbligatorio |
|------|-----------|-------|:------------:|
| ARCH | PLAN | Piano architetturale | Sì (1 per catena) |
| BUILD | EXEC | Richiesta implementazione | Sì |
| BUILD | DONE | Implementazione completata | Sì |
| BUILD | FIX | Richiesta correzione | Se TEST:FAIL |
| BUILD | REVERT | Rollback revisione | Raro |
| TEST | RUN | Richiesta test | Sì |
| TEST | PASS | Test superato | O PASS o FAIL |
| TEST | FAIL | Test fallito | O FAIL o PASS |
| CTX | PRIMITIVES | Snapshot stato iniziale | Sì (catene >5 msg) |
| CTX | UPDATE | Aggiornamento layer | Ogni cambio layer |
| CTX | PRUNE | Pulizia finestra attiva | Ogni 5 msg |
| CTX | COMPACT | Compattazione storia | Ogni 20 msg |
| CTX | FREEZE | Congelamento baseline | ~100 msg |
| STATE | FINDINGS | Risultato analisi | Opzionale |
| STATE | ACK | Accusa protocollo | 1x (dopo PLAN) |
| ORCH | END | Chiusura ciclo | Sì (1 per catena) |
| SKILL | PROMPT | Definizione agente | Skills |

---

## Dettaglio Blocchi

### ARCH:PLAN
```
Scopo:    Tradurre prompt umano in piano strutturato
Emesso da: Architetto
Ricevuto da: Orchestratore
Frequenza: 1 per catena (raro: 2-3 se cambio scenario)

Campi:
  id:<string>         Identificativo unico piano
  fw:<string>         Framework/linguaggio target
  lib:<string>        Librerie (separate da virgola)
  auth:<string>       Schema autenticazione
  pattern:<string>    Pattern architetturale
  tools:<list>        Strumenti/funzionalità
  struct:<list>       Struttura file
  deps:<string>       Dipendenze esterne
  notes:<list>        Note aggiuntive
```

### BUILD:EXEC
```
Scopo:    Richiedere implementazione di un componente
Emesso da: Orchestratore
Ricevuto da: Builder
Frequenza: 1 per componente

Campi:
  id:<string>         Identificativo build
  target:<string>     File/componente target
  after:<list>        Dipendenze DAG (id prerequisiti)
  desc:<string>       Descrizione implementazione
  cmd:<string>        Comando build (es. dotnet build)
```

### BUILD:DONE
```
Scopo:    Notificare completamento implementazione
Emesso da: Builder
Ricevuto da: Orchestratore
Frequenza: 1 per BUILD:EXEC o BUILD:FIX

Campi:
  id:<string>         Matcha BUILD:EXEC.id
  diff:<list_rev>     Modifiche [file~rev,+lines,file~rev,-lines]
  rev:<int>           Revisione file (default 1)
  notes:<list>        Note implementazione
  cycle_id:<string>   Se emesso per FIX
```

### BUILD:FIX
```
Scopo:    Richiedere correzione su implementazione
Emesso da: Orchestratore
Ricevuto da: Builder
Frequenza: 1 per ciclo fix

Campi:
  id:<string>         Identificativo fix
  target:<string>     File da correggere
  base_rev:<int>      Revisione base su cui applicare fix
  desc:<string>       Descrizione errore/correzioni
  cycle_id:<string>   Identificativo ciclo fix
  retry_n:<int>       Numero tentativo (1-3)
  cmd:<string>        Comando verifica
```

### TEST:RUN
```
Scopo:    Eseguire test suite
Emesso da: Orchestratore
Ricevuto da: Tester
Frequenza: 1 per suite

Campi:
  id:<string>         Identificativo test
  cmd:<string>        Comando da eseguire
```

### TEST:PASS / TEST:FAIL
```
Scopo:    Notificare esito test
Emesso da: Tester
Ricevuto da: Orchestratore
Frequenza: 1 per TEST:RUN

Campi (PASS):
  id:<string>         Matcha TEST:RUN.id
  cycle_id:<string>   Richiesto se chiude ciclo fix
  pass_count:<int>    Contatore superati

Campi (FAIL):
  id:<string>         Matcha TEST:RUN.id
  error:<string>      Messaggio errore
  cycle_id:<string>   Obbligatorio (apre ciclo fix)
  fail_count:<int>    Contatore falliti
  pass_count:<int>    Contatore superati (parziale)
```

### CTX:PRUNE
```
Scopo:    Purgare messaggi non necessari dalla finestra attiva
Emesso da: Qualsiasi agente
Frequenza: Ogni 5 messaggi

Campi:
  keep:<string/list>  "last_N" o lista ids da mantenere
  pruned:<list>       Lista ids rimossi
  reason:<string>     Spiegazione pruning
```

### CTX:COMPACT
```
Scopo:    Compattare storia cumulativa in riassunto
Emesso da: Orchestratore
Frequenza: Ogni 20 messaggi

Campi:
  summary:<list>      Riassunto (max 5 voci)
  keep_active:<list>  File ancora in modifica attiva
  pruned_history:<str> Range storia potata
  pass_count:<int>    Contatore cumulativo
  fail_count:<int>    Contatore cumulativo
```

### CTX:FREEZE
```
Scopo:    Congelare baseline quando COMPACT non basta
Emesso da: Orchestratore
Frequenza: Una volta, ~100 messaggi

Campi:
  snapshot:<list>     Tutti i file attivi con revisione
  baseline:<int>      Numero messaggio al freeze
```

---

## Pattern di Flusso

### Flusso Base (nessun errore)
```
ARCH:PLAN → BUILD:EXEC → BUILD:DONE → TEST:RUN → TEST:PASS → ORCH:END
```

### Flusso con Fix
```
TEST:RUN → TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:RUN → TEST:PASS
```

### Flusso Multi-Step con DAG
```
BUILD:EXEC (m1) ──→ BUILD:EXEC (m2) ──→ BUILD:EXEC (m4)
      │                                         │
      └──→ BUILD:EXEC (m3) ─────────────────────┘
```

### Flusso lungo con Context Lifecycle
```
ARCH:PLAN → BUILD:EXEC × N → CTX:PRUNE → BUILD:EXEC × N → CTX:PRUNE
→ CTX:COMPACT → BUILD:EXEC × N → ... → CTX:FREEZE → ... → ORCH:END
```
