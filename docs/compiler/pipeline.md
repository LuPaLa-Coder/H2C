# Pipeline del Compilatore — Protocollo H2C

**Versione:** 1.0
**Stato:** RICERCA
**Scopo:** Definire l'architettura del compilatore/transpiler H2C — da H2C ad altri formati e viceversa.

---

## 1. Visione

Il compilatore H2C trasforma blocchi H2C in altri formati (linguaggio naturale, JSON, MCP, YAML) e viceversa. Serve come ponte tra il protocollo H2C e gli strumenti/framework esistenti.

```
┌──────────┐    ┌──────────────┐    ┌──────────┐
│  H2C     │───→│  Compilatore │───→│  Output  │
│ (input)  │    │  H2C v1.2    │    │ formati  │
└──────────┘    └──────────────┘    └──────────┘
                      │
                      ├──→ Linguaggio Naturale
                      ├──→ JSON / JSON-RPC
                      ├──→ YAML
                      ├──→ MCP Tool Call
                      └──→ Prompt LLM completo
```

## 2. Pipeline di Compilazione

```
H2C Input
   │
   ▼
┌──────────────┐
│   Parsing    │  → AST (docs/parser/architecture.md)
└──────────────┘
   │
   ▼
┌──────────────┐
│  Validazione │  → Controllo campi REQUIRED, tipi, vincoli
└──────────────┘
   │
   ▼
┌──────────────┐
│  Analisi     │  → Risoluzione riferimenti (cycle_id, after)
│  Semantica   │  → Ricostruzione stato e contesto
└──────────────┘
   │
   ▼
┌──────────────┐
│  Codegen     │  → Generazione output nel formato target
└──────────────┘
   │
   ▼
Output
```

## 3. Backend di Codegen

### 3.1 H2C → Linguaggio Naturale

Converte blocchi H2C in prompt leggibili da umani. Utile per debugging, logging e documentazione.

```
Input:
[ARCH:PLAN]
id:api|fw:python|lib:fastapi,redis|notes:[auth_JWT,cache_10min]

Output:
=== ARCH:PLAN ===
ID: api
Framework: python
Librerie: fastapi, redis
Note: autenticazione JWT, cache 10 minuti
```

**Template per ogni blocco:**

| Blocco | Template NL |
|--------|-------------|
| `ARCH:PLAN` | `Piano architetturale per {id}. Framework: {fw}. Librerie: {lib}. Note: {notes}` |
| `BUILD:EXEC` | `Esegui build {id} su {target}. Descrizione: {desc}` |
| `BUILD:DONE` | `Build {id} completata su {diff}` |
| `BUILD:FIX` | `Correggi {target} (rev {base_rev}): {desc}` |
| `TEST:RUN` | `Esegui test {id}: {cmd}` |
| `TEST:PASS` | `Test {id} superato` |
| `TEST:FAIL` | `Test {id} fallito: {error}` |
| `CTX:PRUNE` | `Pruning contesto: mantenuto {keep}, potato {pruned}` |
| `CTX:COMPACT` | `Compattazione: {summary}` |
| `ORCH:END` | `Orchestrazione terminata: {final}` |

### 3.2 H2C → JSON

Converte blocchi H2C in JSON strutturato per integrazione con API REST e sistemi di messaggistica.

```
Input:
[BUILD:DONE]
id:m1|diff:[main.py~1,+15]|rev:1

Output:
{
  "type": "BUILD",
  "subtype": "DONE",
  "fields": {
    "id": "m1",
    "diff": [{"file": "main.py", "rev": 1, "lines": "+15"}],
    "rev": 1
  }
}
```

### 3.3 H2C → MCP Tool Call

Converte blocchi H2C in chiamate strumento MCP. Permette a H2C di essere trasportato su MCP.

```
Input:
[BUILD:EXEC]
id:m2|target:models/user.py|desc:crea_modello_utente

Output:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "h2c_build_exec",
    "arguments": {
      "id": "m2",
      "target": "models/user.py",
      "desc": "crea_modello_utente"
    }
  },
  "id": 1
}
```

### 3.4 H2C → YAML

```
build_exec:
  id: m2
  target: models/user.py
  desc: crea_modello_utente
```

## 4. Compilatore Inverso (NL → H2C)

Il compilatore inverso analizza testo in linguaggio naturale e produce blocchi H2C. Utile per:
- Migrazione graduale da prompt NL a H2C
- Interfacce ibride (umano scrive NL, sistema converte in H2C)
- Tooling di onboarding

```
Input NL:
"Crea un'API meteo in Python con FastAPI.
Usa httpx per le chiamate HTTP.
Richiede autenticazione con API key.
Cache TTL 10 minuti."

Output:
[ARCH:PLAN]
id:api|fw:python3.11|lib:fastapi,httpx,cachetools|auth:APIKey|notes:[cache_TTL_10min]
```

**Strategia:** Usa pattern matching su strutture tipiche del prompt engineering:
- "Crea un ... in ..." → `id` + `fw`
- "Usa ... per ..." → `lib`
- "Richiede ..." → `auth`
- Note tecniche in parentesi → `notes`

## 5. Validatore

### 5.1 Regole di Validazione

```
VALIDATOR-1:  Ogni blocco deve avere tipo e sottotipo validi (contro enum §1)
VALIDATOR-2:  I campi REQUIRED devono essere presenti
VALIDATOR-3:  I campi devono avere tipo corretto (string/list/int/enum)
VALIDATOR-4:  cycle_id deve essere coerente nella catena
VALIDATOR-5:  retry_n nel range [1..3]
VALIDATOR-6:  after: deve riferirsi a id esistenti (DAG integro)
VALIDATOR-7:  diff: formato corretto [file~N,+M,file~N,-K]
VALIDATOR-8:  ORCH:END è terminale — nessun blocco dopo
VALIDATOR-9:  CTX:PRUNE ogni 5 messaggi (controllo temporale)
VALIDATOR-10: CTX:COMPACT ogni 20 messaggi
VALIDATOR-11: CTX:FREEZE non più di una volta
VALIDATOR-12: Nessun testo fuori dai campi
```

### 5.2 Architettura del Validatore

```
┌──────────────┐
│  Validatore  │
│  H2C         │
└──────┬───────┘
       │
       ├── Validatore Sintattico
       │     ├── Controllo formato blocco [TIPO:SOTTOTIPO]
       │     ├── Controllo separatori : e |
       │     └── Controllo parentesi []
       │
       ├── Validatore Strutturale
       │     ├── Campi REQUIRED presenti
       │     ├── Tipi campi corretti
       │     └── Vincoli di formato
       │
       ├── Validatore Contestuale
       │     ├── cycle_id coerente
       │     ├── DAG after: integro
       │     ├── retry_n range
       │     └── Frequenza PRUNE/COMPACT/FREEZE
       │
       └── Validatore Terminale
             ├── ORCH:END è ultimo
             └── Nessun blocco dopo END
```

### 5.3 Output di Validazione

```json
{
  "valid": false,
  "errors": [
    {
      "level": "error",
      "rule": "VALIDATOR-1",
      "message": "Blocco [INVALID:FOO] ha tipo non valido",
      "location": {"line": 3, "block": 2}
    },
    {
      "level": "warning",
      "rule": "VALIDATOR-9",
      "message": "CTX:PRUNE non emesso da 6 messaggi",
      "location": {"line": 42}
    }
  ],
  "stats": {
    "total_blocks": 15,
    "valid_blocks": 14,
    "errors": 1,
    "warnings": 1
  }
}
```

## 6. Tabella di Routing (Dispatcher)

Il dispatcher instrada ogni blocco al componente appropriato:

```
Blocco              → Destinazione
────────────────────────────────
ARCH:PLAN           → Sistema di pianificazione
BUILD:EXEC          → Builder (esecutore)
BUILD:DONE          → Orchestratore (notifica)
BUILD:FIX           → Builder (correzione)
BUILD:REVERT        → Builder (rollback)
TEST:RUN            → Tester
TEST:PASS           → Orchestratore (successo)
TEST:FAIL           → Orchestratore (errore)
CTX:PRIMITIVES      → Gestore contesto
CTX:UPDATE          → Gestore contesto
CTX:PRUNE           → Gestore contesto (pruning)
CTX:COMPACT         → Gestore contesto (compattazione)
CTX:FREEZE          → Gestore contesto (congelamento)
STATE:FINDINGS      → Sistema di auditing
STATE:ACK           → Protocollo (handshake)
ORCH:END            → Orchestratore (terminazione)
SKILL:PROMPT        → Definizione agente
```

## 7. Roadmap Implementativa

| Fase | Componente | Stato |
|------|-----------|-------|
| 1 | Parser Python (minimo) | PROGETTAZIONE |
| 2 | Validatore sintattico | PROGETTAZIONE |
| 3 | Codegen NL (H2C → testo) | PROGETTAZIONE |
| 4 | Codegen JSON (H2C → API) | PROGETTAZIONE |
| 5 | Compilatore inverso NL → H2C | RICERCA |
| 6 | Integrazione MCP nativa | RICERCA |
| 7 | Parser Rust/WASM (produzione) | RICERCA |
| 8 | IDE extension (syntax highlight, validation) | FUTURO |
