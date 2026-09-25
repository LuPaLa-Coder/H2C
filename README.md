# H2C Semantic Compression Protocol

**Protocollo di handoff strutturato tra agenti AI: blocchi tipizzati, parsing deterministico, stato versionato.**

![H2C Protocol](1779633660140.png)

```
Protocollo: H2C v1.4
Stato:      DRAFT (validato)
Licenza:    MIT
Specifica:  SPEC.md
```

> **NON** è HTTP/2 h2c (RFC 7540). HTTP/2 h2c è un meccanismo di upgrade in chiaro per connessioni HTTP/1.1. Questo H2C è un **protocollo di compressione semantica per comunicazione AI-to-AI**, grammaticalmente e funzionalmente indipendente. Vedi [Confronto con alternative](docs/comparisons/vs-alternatives.md) per la disambiguazione completa.

---

## Visione

I sistemi multi-agente oggi comunicano in linguaggio naturale — verboso, ridondante, non analizzabile. Ogni piano architetturale costa 500–2000 token. Ogni ciclo build-test-fix brucia migliaia di token. Spiegazioni, cortesie, markdown e ripetizioni dominano il cablaggio.

H2C sostituisce il linguaggio naturale con una grammatica a blocchi strutturata progettata per il parsing nativo da LLM. È un **protocollo di handoff strutturato**: stato esplicito e versionato, parsing deterministico invece di interpretazione di prosa.

Non è un formato di prompt. È un **wire protocol per agenti AI.**

---

## Perché Esiste

| Problema | Impatto | Soluzione H2C |
|----------|---------|---------------|
| Nessun protocollo agenti analizzabile | Orchestrator leggono testo libero | Blocchi strutturati con campi tipizzati |
| Fragilità cross-modello | Prompt falliscono tra famiglie di modelli | Grammatica autodescrittiva, zero-shot cross-modello |
| Nessun handoff versionato tra agenti | Gli agenti non possono riprendere conversazioni | `rev`/`base_rev`, `cycle_id`, `STATE:FINDINGS` |
| Handoff ambigui tra agenti | Stato perso o reinterpretato | Blocchi tipizzati, validator, FSM |

---

## Architettura

```
┌─────────────────────────────────────────────────────┐
│                   Pipeline Agenti                     │
│                                                       │
│  [Umano] → [Architetto] → [Orchestratore] → [Builder]│
│                                          ↕            │
│                                      [Tester]         │
│                                                       │
│  Formato:  [TIPO:SOTTOTIPO] chiave:val|chiave:val|...│
│  Trasporto: stdin/stdout | HTTP | WebSocket | MCP     │
└─────────────────────────────────────────────────────┘
```

### Modello a Strati

| Strato | Componente | Ruolo |
|--------|------------|-------|
| **Trasporto** | MCP, stdin/stdout, HTTP, WebSocket | Trasporta blocchi H2C tra agenti |
| **Semantico** | Grammatica a blocchi H2C | Definisce significato, stato e flusso |
| **Orchestrazione** | cycle_id, retry_n, PRUNE/COMPACT/FREEZE | Gestisce catene di agenti di lunga durata |
| **Applicativo** | Skill agente (skills/*.md) | Mappa blocchi H2C a comportamento agente |

---

## Installazione (Claude Code Plugin)

H2C è disponibile come plugin Claude Code. Aggiunge i comandi `/h2c:h2c` e skill automatiche per Architect, Builder, Orchestrator, Tester e Compress.

```
/plugin install github:LuPaLa-Coder/H2C
```

Oppure carica il marketplace e installa:

```
/plugin marketplace add LuPaLa-Coder/H2C
/plugin install h2c
```

Dopo l'installazione, usa `/h2c:h2c help` per vedere tutti i comandi disponibili.

### Skill incluse

| Skill | Tipo | Descrizione |
|-------|------|-------------|
| `/h2c:h2c` | Comandi | Generazione, analisi e statistiche blocchi H2C |
| `h2c-architect` | Automatica | Traduzione prompt NL → `ARCH:PLAN` |
| `h2c-builder` | Automatica | Implementazione `BUILD:EXEC` → codice |
| `h2c-orchestrator` | Automatica | Instradamento blocchi tra agenti |
| `h2c-tester` | Automatica | Esecuzione `TEST:RUN` → `TEST:PASS`/`FAIL` |
| `h2c-compress` | Automatica | Compressione prompt NL → H2C |

Vedi [docs/PLUGIN.md](docs/PLUGIN.md) per la guida completa.

### Python Runtime

```bash
pip install -e .
h2c parse examples/api-meteo.md
h2c validate tests/fixtures/test1-hello-world.h2c
h2c transpile examples/api-meteo.md --to nl
h2c run tests/fixtures/test1-hello-world.h2c
h2c stats examples/api-meteo.md
```

### Sviluppo plugin locale

```bash
claude --plugin-dir .
```

---

## Sintassi (Grammatica Core)

```
[TIPO:SOTTOTIPO]
chiave1:valore1|chiave2:valore2|...

TIPO     ::= "ARCH" | "BUILD" | "TEST" | "CTX" | "STATE" | "ORCH" | "SKILL"
SOTTOTIPO::= "PLAN" | "EXEC" | "DONE" | "FIX" | "REVERT" | "NACK" | "RUN" | "PASS"
           | "FAIL" | "PRIMITIVES" | "UPDATE" | "PRUNE" | "COMPACT" | "FREEZE"
           | "NEGOTIATE" | "FINDINGS" | "ACK" | "END" | "PROMPT"
```

I campi sono coppie chiave-valore tipizzate con separatore `|`. Liste usano `[a,b,c]`. Revisioni usano `file~N`. Vedi [SPEC.md](SPEC.md) e [docs/specification/grammar.md](docs/specification/grammar.md).

### Esempio Minimo

```
[CTX:NEGOTIATE]
version:h2c_v1.4|capabilities:[PRUNE,COMPACT,FREEZE,NEGOTIATE,NACK]

[STATE:ACK]
protocol:h2c_v1.4

[ARCH:PLAN]
id:api-meteo|fw:python3.11|lib:fastapi,httpx,cachetools|auth:APIKey::env(OPENWEATHER_API_KEY)|struct:[main.py,routers/weather.py,services/weather_service.py]|notes:[cache_TTL_10min,rate-limit_60req-min]

[BUILD:EXEC]
id:m1|target:main.py|desc:setup_fastapi_app

[BUILD:DONE]
id:m1|diff:[main.py~1]|rev:1

[ORCH:END]
final:complete|est_token:15
```

## Esempi

| Esempio | Descrizione |
|---------|-------------|
| [API Meteo](examples/api-meteo.md) | Servizio meteo Python/FastAPI vs prompt NL |
| [TODO Console](examples/todo-console.md) | App console C# .NET 8 con SQLite vs NL |
| [Catena PRUNE/COMPACT](examples/prune_demo.md) | Catena v1.4 completa con gestione contesto |

---

### E i token?

H2C non è un formato di compressione. Le catene portano stato esplicito
(id, revisioni, `cycle_id`) e costano più token di un brief in linguaggio
naturale: vedi i numeri misurati in [`conformance/Result.md`](conformance/Result.md)
(`python3 conformance/benchmark.py fixtures`). Il valore è altrove: un
orchestratore legge l'handoff con un parser deterministico invece di
interpretare prosa.

---

## Casi d'Uso

- **Orchestrazione multi-agente**: Cicli Architetto → Builder → Tester con tracciamento retry
- **Catene di agenti di lunga durata**: Conversazioni 100+ messaggi con pruning contesto
- **Handoff LLM-to-LLM**: Agente A produce output strutturato per Agente B senza parsing NL
- **IR Cognitivo**: Compressione semantica per retrieval-augmented generation
- **Trasporto ragionamento**: Trasportare catene di ragionamento intermedio compresse tra chiamate LLM
- **Protocollo runtime agenti**: Formato standard per piattaforme di hosting agenti

---

## Integrazione Ecosistema

H2C è il **layer semantico**; i framework esistenti fungono da **layer di trasporto**:

| Framework | Modello di Integrazione |
|-----------|-------------------------|
| **MCP** | Blocchi H2C trasportati come contenuto tool call MCP |
| **LangGraph** | H2C come formato output nodo, schema stato |
| **AutoGen** | H2C come protocollo risposta agente |
| **Semantic Kernel** | H2C come serializzazione risultato funzione |
| **CrewAI** | H2C come formato output task |
| **OpenAI Agents SDK** | H2C come formato output strutturato |

Vedi [docs/ecosystem/integrations.md](docs/ecosystem/integrations.md).

---

## Roadmap del Progetto

| Fase | Cosa | Stato |
|------|------|-------|
| v1.0 | Grammatica core, blocchi base | RILASCIATO |
| v1.1 | PRUNE/COMPACT, rev, fail/pass count | RILASCIATO |
| v1.2 | FREEZE, cycle_id obbligatorio, retry_n, rinomina skill | RILASCIATO |
| v1.3 | EBNF formale (ISO 14977), modello AST, opcode semantici, macchina stati completa | RILASCIATO |
| v1.4 | CTX:NEGOTIATE handshake, BUILD:NACK error recovery, fix grammatica BNF, DAG transitive closure, campi STATE:FINDINGS formali | RILASCIATO |
| v2.0 | Implementazione di riferimento parser, validatore, transpiler | PIANIFICATO |
| v3.0 | Compilatore H2C, trasporto nativo MCP, runtime agenti | RICERCA |

---

## Per Iniziare

```bash
# Clona
git clone https://github.com/LuPaLa-Coder/H2C.git

# Leggi la specifica
cat SPEC.md

# Esegui una skill (copia come system prompt in qualsiasi LLM)
cat docs/agents/h2c_architect.md

# Esplora benchmark
cat InternalTest/opus4_7/REPORT.md
cat InternalTest/deepseek-v4-pro/REPORT.md

# Auto-test
cat Test.md
```

Requisiti: Qualsiasi LLM con context window ≥8K. Nessuna libreria. Nessuna dipendenza. Solo testo.

---

## Contributi

Vedi [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licenza

MIT — Copyright © 2026 **Paolino Salamone**.
