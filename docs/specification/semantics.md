# Semantica Operazionale H2C

**Versione:** 1.2
**Stato:** FORMALE
**Scopo:** Definire la semantica operazionale del protocollo H2C — significato dei blocchi, regole di transizione e modello di esecuzione.

---

## 1. Modello a Stati

L'esecuzione di una catena H2C è modellabile come macchina a stati finiti:

```
Stati:
  INIT      → Stato iniziale (attesa ARCH:PLAN)
  PLANNED   → Piano ricevuto (ARCH:PLAN emesso)
  BUILDING  → In esecuzione build (BUILD:EXEC emesso)
  BUILT     → Build completata (BUILD:DONE ricevuto)
  TESTING   → In esecuzione test (TEST:RUN emesso)
  TEST_PASS → Test superato (TEST:PASS ricevuto)
  TEST_FAIL → Test fallito (TEST:FAIL ricevuto)
  FIXING    → In correzione (BUILD:FIX emesso)
  COMPACT   → Compattazione contesto (CTX:COMPACT emesso)
  FROZEN    → Congelamento contesto (CTX:FREEZE emesso)
  TERM      → Terminale (ORCH:END ricevuto)
```

### Matrice di Transizione

```
Stato Corrente    → Blocco Ricevuto    → Nuovo Stato
─────────────────────────────────────────────────────
INIT              → ARCH:PLAN          → PLANNED
PLANNED           → BUILD:EXEC         → BUILDING
BUILDING          → BUILD:DONE         → BUILT
BUILT             → TEST:RUN           → TESTING
TESTING           → TEST:PASS          → TEST_PASS
TESTING           → TEST:FAIL          → TEST_FAIL
TEST_FAIL         → BUILD:FIX          → FIXING
FIXING            → BUILD:DONE         → BUILT
BUILT|TEST_PASS   → BUILD:EXEC         → BUILDING    (prossimo step)
ANY               → CTX:PRUNE          → ANY         (non cambia stato)
ANY               → CTX:COMPACT        → COMPACT
ANY               → CTX:FREEZE         → FROZEN
TEST_PASS|FROZEN  → ORCH:END           → TERM
ANY               → ORCH:END           → TERM        (errore/timeout)
```

---

## 2. Opcode Semantici

Ogni blocco H2C corrisponde a un opcode semantico con effetti definiti:

| Opcode | Simbolo | Effetto |
|--------|---------|---------|
| `ARCH_PLAN` | `↻` | Inizializza contesto, definisce piano |
| `BUILD_EXEC` | `→` | Avvia esecuzione su target |
| `BUILD_DONE` | `✓` | Registra completamento e diff |
| `BUILD_FIX` | `✗→` | Richiede correzione su revisione |
| `BUILD_REVERT` | `↩` | Torna a revisione precedente |
| `TEST_RUN` | `⚡` | Esegui test suite |
| `TEST_PASS` | `✔` | Test superato, incrementa contatore |
| `TEST_FAIL` | `✘` | Test fallito, apre ciclo fix |
| `CTX_PRIM` | `◈` | Snapshot stato iniziale |
| `CTX_UPD` | `◈→` | Aggiorna layer corrente |
| `CTX_PRUNE` | `✂` | Pota messaggi non necessari |
| `CTX_COMPACT` | `⊞` | Compatta storia cumulativa |
| `CTX_FREEZE` | `⊟` | Congela baseline, reset contatori |
| `STATE_FIND` | `◆` | Emette risultato analisi |
| `STATE_ACK` | `◀` | Accusa ricezione protocollo |
| `ORCH_END` | `■` | Termina orchestrazione |

### Effetti Collaterali

```
Opcode           → Side Effect
─────────────────────────────────
ARCH_PLAN        → Crea contesto, inizializza contatori msg
BUILD_EXEC       → Incrementa contatore build, push stack esecuzione
BUILD_DONE       → Pop stack esecuzione, registra diff
BUILD_FIX        → Incrementa retry_n, apre cycle_id
TEST_PASS        → Incrementa pass_count per cycle_id
TEST_FAIL        → Incrementa fail_count per cycle_id
CTX_PRUNE        → Decrementa contatore messaggi attivi
CTX_COMPACT      → Reset contatore PRUNE, compatta storia
CTX_FREEZE       → Reset PRUNE + COMPACT, archivia storia
```

---

## 3. Modello di Concorrenza

H2C è **sequentiale** per progetto. Ogni messaggio è una transizione atomica:

```
┌─ Lock ─────────────────┐
│ [ARCH:PLAN]             │  ← solo un blocco per messaggio
│ id:X|fw:python|...      │
└─────────────────────────┘
         │
         ▼
┌─ Lock ─────────────────┐
│ [BUILD:EXEC]            │
│ id:m1|target:a.py|...   │
└─────────────────────────┘
```

Non esiste concorrenza nativa. L'orchestrazione multi-agente è sequenziale:
- Un blocco in input
- Un blocco in output
- transizione atomica

Per parallelismo, usare `after:` per DAG esplicito:
```
[BUILD:EXEC] id:m1|target:a.py
[BUILD:EXEC] id:m2|target:b.py|after:m1
[BUILD:EXEC] id:m3|target:c.py|after:m1   ← parallelo a m2 (DAG)
```

---

## 4. Modello di Memoria

H2C definisce uno **spazio di memoria condiviso** tra agenti:

```
Memoria Globale:
  ├── msg_counter:      integer       (contatore messaggi globale)
  ├── context_state:    { layer, status, next, active_files }
  ├── revision_table:   { file → rev } (stato revisioni)
  ├── cycle_registry:   { cycle_id → { retry_n, fail_count, pass_count, status }}
  └── findings:         [FINDING*]     (lista risultati analisi)
```

Questo spazio è **implicito** — non serializzato esplicitamente ma ricostruibile dal parsing della cronologia dei blocchi.

---

## 5. Regole di Integrità

```
R1: Un cycle_id aperto da BUILD:FIX deve chiudersi con TEST:PASS o ORCH:END
R2: retry_n non può superare 3 per cycle_id
R3: fail_count resetta quando cycle_id cambia
R4: CTX:PRUNE obbligatorio ogni 5 messaggi
R5: CTX:COMPACT obbligatorio ogni 20 messaggi (dopo il reset: ogni 20 dal COMPACT)
R6: CTX:FREEZE esattamente una volta, quando COMPACT non basta (~100 msg)
R7: CTX:UPDATE obbligatorio a ogni cambio layer
R8: ORCH:END è terminale — nessun blocco dopo
R9: Ogni id deve essere unico nello scope della catena
R10: base_rev in BUILD:FIX deve corrispondere a rev in BUILD:DONE
```
