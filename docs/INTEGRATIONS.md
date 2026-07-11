# H2C — Integrazione con Coding Agents

Il protocollo H2C v1.4 è **agent-agnostic**: funziona con qualsiasi LLM e qualsiasi coding agent. Questo documento spiega come integrarlo in ciascun ambiente.

---

## 🌍 Standard Universale: `AGENTS.md`

Il file [`AGENTS.md`](../AGENTS.md) nella root del repository è il formato canonico universale. Viene letto nativamente da:

| Agente | Supporto |
|--------|----------|
| **Cursor** | ✅ Nativo (`AGENTS.md`) |
| **GitHub Copilot** | ✅ Nativo |
| **Claude Code** | ✅ Nativo (`CLAUDE.md`, che punta a `AGENTS.md`) |
| **Cline** | ✅ Nativo (legge anche `AGENTS.md`) |
| **OpenAI Codex** | ✅ Nativo |
| **Zed AI** | ✅ Nativo |
| **Gemini CLI** | ✅ Nativo (`GEMINI.md`) |
| **Windsurf** | ✅ Via `.windsurfrules` |
| **Aider** | ✅ Via `CONVENTIONS.md` |

**Vantaggio:** Un solo file da mantenere, tutti gli agenti lo leggono. Nessuna duplicazione.

---

## 🤖 Claude Code

### Opzione A: Plugin (consigliato, massima integrazione)

```bash
/plugin install github:LuPaLa-Coder/H2C
```

Il plugin espone:
- **Comandi**: `/h2c:h2c stat`, `/h2c:h2c compress`, `/h2c:h2c plan`, etc. (20 comandi)
- **Skill automatiche**: `h2c-architect`, `h2c-builder`, `h2c-orchestrator`, `h2c-tester`, `h2c-compress`
- **Validazione**: `claude plugin validate` già superato ✔

### Opzione B: Standalone (progetto locale)

Claude Code legge automaticamente `CLAUDE.md` nella root del progetto. Clona il repo e lavora nella directory:

```bash
git clone https://github.com/LuPaLa-Coder/H2C
cd H2C
claude
```

### Opzione C: Sviluppo plugin

```bash
claude --plugin-dir /path/to/H2C
```

---

## 🖱️ Cursor

### Installazione

Il file [`.cursor/rules/h2c.mdc`](../.cursor/rules/h2c.mdc) attiva H2C automaticamente in ogni sessione Cursor.

```bash
# Clona il repo o copia solo i file rules:
cp .cursor/rules/h2c.mdc <tuo-progetto>/.cursor/rules/
cp AGENTS.md <tuo-progetto>/
```

### Comportamento

- `alwaysApply: true` — H2C è sempre disponibile
- Quando dici "comprimi questo prompt in H2C" → genera il blocco corretto
- Usa `@h2c` per attivarlo manualmente in una chat

---

## 📋 GitHub Copilot

### Installazione

Il file [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) istruisce Copilot su come usare H2C.

```bash
# Copia nel tuo progetto:
cp .github/copilot-instructions.md <tuo-progetto>/.github/
cp AGENTS.md <tuo-progetto>/
```

### Comportamento

Copilot applica le istruzioni in ogni chat e risponde in formato H2C quando richiesto.

---

## 🌊 Windsurf

### Installazione

```bash
cp .windsurfrules <tuo-progetto>/
cp AGENTS.md <tuo-progetto>/
```

Windsurf legge `.windsurfrules` come regole globali del progetto.

---

## 🧗 Cline

### Installazione

Cline legge automaticamente `AGENTS.md`, `CLAUDE.md`, e `.clinerules`.

```bash
cp AGENTS.md <tuo-progetto>/
cp CLAUDE.md <tuo-progetto>/
```

In alternativa, crea un file `.clinerules`:

```bash
cp .windsurfrules <tuo-progetto>/.clinerules
```

---

## 🔧 Aider

### Installazione

```bash
cp AGENTS.md <tuo-progetto>/CONVENTIONS.md
```

Oppure passa `AGENTS.md` come system prompt:

```bash
aider --system-prompt AGENTS.md
```

---

## 🐍 Python Runtime (tutti gli agenti)

Il runtime Python H2C è utilizzabile da qualsiasi ambiente:

```bash
pip install -e .
h2c parse file.h2c          # Parsing e validazione sintattica
h2c validate file.h2c       # Validazione contro le regole del protocollo
h2c transpile file.h2c --to nl   # H2C → linguaggio naturale
h2c transpile file.h2c --to json # H2C → JSON strutturato
h2c transpile file.h2c --to mcp  # H2C → MCP tool calls
h2c transpile file.h2c --to yaml # H2C → YAML
h2c run file.h2c            # Esecuzione catena H2C nell'agent runtime
h2c stats file.h2c          # Statistiche token risparmiati
```

---

## 📊 Confronto Funzionalità per Agente

| Funzionalità | Claude Code | Cursor | Copilot | Windsurf | Cline | Aider |
|---|---|---|---|---|---|---|
| Comandi `/h2c:*` | ✅ Plugin | ❌ | ❌ | ❌ | ❌ | ❌ |
| Skill automatiche | ✅ Plugin | ❌ | ❌ | ❌ | ❌ | ❌ |
| Compressione NL→H2C | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tracciamento BUILD/ARCH/TEST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fix cycle | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Validazione blocchi | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI |
| Transpilazione NL/JSON/MCP | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI | ✅ CLI |
| Handshake NEGOTIATE | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🔑 File nel Repository

| File | Agenti | Formato |
|------|--------|---------|
| `AGENTS.md` | Cursor, Copilot, Cline, Codex, Zed, Gemini, Aider, Claude Code | Markdown puro |
| `CLAUDE.md` | Claude Code (standalone) | Markdown puro |
| `.cursor/rules/h2c.mdc` | Cursor | YAML frontmatter + Markdown |
| `.github/copilot-instructions.md` | GitHub Copilot | Markdown puro |
| `.windsurfrules` | Windsurf | Markdown puro |
| `.claude-plugin/plugin.json` | Claude Code (plugin) | JSON |
| `skills/*/SKILL.md` | Claude Code (plugin) | YAML frontmatter + Markdown |
| `h2c/` (runtime) | Qualsiasi (CLI) | Python |

---

## 💡 Consiglio: quale usare?

- **Massima integrazione**: Claude Code Plugin + `AGENTS.md`
- **Multi-agente**: `AGENTS.md` + `.cursor/rules/h2c.mdc` + `.github/copilot-instructions.md`
- **Minimale**: solo `AGENTS.md` (coperto il 90% degli agenti)
- **CLI/automazione**: Python runtime `h2c`
