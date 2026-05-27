# Ciclo di Vita del Contesto H2C

**Versione:** 1.2
**Stato:** DEFINITIVO
**Scopo:** Specificare il sistema di gestione del contesto — meccanismo PRUNE/COMPACT/FREEZE che abilita catene lunghe.

---

## 1. Problema

Le catene di agenti AI soffrono di saturazione della context window del modello. In linguaggio naturale, il degrado inizia dopo ~40 messaggi (crollo coerenza referenziale). H2C risolve con un sistema di gestione del contesto a tre livelli.

---

## 2. Triade di Gestione Contesto

```
Soglia     Messaggio     Azione
─────────────────────────────────────
Ogni 5     CTX:PRUNE     Purgare messaggi non necessari
Ogni 20    CTX:COMPACT   Compattare storia in riassunto
~100       CTX:FREEZE    Congelare baseline, reset totale
```

---

## 3. PRUNE — Purging Locale

**Trigger:** Ogni 5 messaggi (contatore globale)
**Scopo:** Rimuovere messaggi che non servono più alla finestra attiva

### Regole di Pruning

| Blocco | Condizione | Prunabile? |
|--------|-----------|:----------:|
| ARCH:PLAN | Esiste COMPACT successivo | Sì |
| ARCH:PLAN | Ultimo, nessun COMPACT | NO |
| BUILD:EXEC | BUILD:DONE corrispondente emesso | Sì |
| BUILD:EXEC | BUILD:DONE NON ancora emesso | NO |
| BUILD:FIX | cycle_id ancora aperto | NO |
| BUILD:FIX | cycle_id chiuso (TEST:PASS) | Sì |
| BUILD:DONE | Esiste COMPACT successivo | Sì |
| TEST:RUN | Esito (PASS/FAIL) emesso | Sì |
| TEST:RUN | Esito NON ancora emesso | NO |
| TEST:PASS/FAIL | Esiste COMPACT successivo | Sì |
| CTX:PRUNE | Dopo emissione | Sì (sempre) |
| CTX:COMPACT | Più recente | NO |
| CTX:COMPACT | Precedente | Sì |
| CTX:UPDATE | Dopo COMPACT successivo | Sì |
| STATE:ACK | Dopo primo blocco utile | Sì |
| ORCH:END | Mai (è terminale) | NO |

### Esempio
```
[CTX:PRUNE]
keep:[m5,m6,t2,f1]|pruned:[m1,m2,m3,m4,t1]
```

---

## 4. COMPACT — Compattazione Globale

**Trigger:** Ogni 20 messaggi
**Scopo:** Riassumere la storia cumulativa in poche voci

### Formato
```
[CTX:COMPACT]
summary:[layer=auth|status=done, layer=db|status=done|files:[db.py~1], layer=api|status=in_progress]
keep_active:[main.py~2,auth.py~1,db.py~1,api.py~1]
pruned_history:msg_22_to_40|pass_count:12|fail_count:2
```

### Effetti
- Contatore PRUNE resettato
- Storia precedente (msg 1-20) archiviata nel summary
- File attivi mantenuti con revisione corrente
- I contatori pass_count/fail_count sono cumulativi

---

## 5. FREEZE — Congelamento

**Trigger:** ~100 messaggi (quando COMPACT non basta più)
**Scopo:** Reset completo dei contatori, archiviazione storia

### Formato
```
[CTX:FREEZE]
snapshot:[main.py~2,auth.py~1,db.py~1,api.py~1,routes.py~1,crud.py~2]
baseline:110
```

### Effetti
- Contatori PRUNE e COMPACT ripartono da zero
- Storia precedente archiviata (non cancellata)
- snapshot contiene tutti i file attivi con revisione
- baseline = numero messaggio al freeze

---

## 6. Diagramma Temporale

```
Msg 0:   [ARCH:PLAN]
Msg 1-4: BUILD/EXEC/DONE, TEST/PASS
Msg 5:   [CTX:PRUNE]             ← primo prune
Msg 6-9: BUILD/EXEC/DONE, TEST/PASS
Msg 10:  [CTX:PRUNE]
Msg 11-14: ...
Msg 15:  [CTX:PRUNE]
Msg 16-19: ...
Msg 20:  [CTX:COMPACT]           ← reset contatore PRUNE
Msg 21-24: ...
Msg 25:  [CTX:PRUNE]             ← nuovo ciclo dopo COMPACT
...
Msg 100: [CTX:COMPACT] (ultimo)
Msg 105: [CTX:PRUNE]
Msg 110: [CTX:FREEZE]            ← freeze, reset totale
Msg 111+: nuovo ciclo con contatori azzerati
```

---

## 7. Scalabilità Empirica

| Configurazione | Max Messaggi | Fattore Limitante |
|---------------|:-----------:|-------------------|
| Nessun contesto | ~40 | Saturazione finestra |
| Solo PRUNE | ~60 | Accumulo storia |
| PRUNE + COMPACT | ~100 | Riassunti accumulati |
| PRUNE + COMPACT + FREEZE | ~130+ | Modello (non protocollo) |

Dati validati su Claude Sonnet 4.6 (61 msg) e Opus 4.7 (130 msg).
Vedi [docs/benchmarks/comparison.md](../benchmarks/comparison.md).
