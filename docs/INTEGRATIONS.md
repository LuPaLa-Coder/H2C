# H2C — Installazione per Coding Agent

Il protocollo H2C v1.4 è compatibile con tutti i principali coding agent. Questo documento elenca i metodi di installazione supportati ufficialmente.

---

## 🧩 Agenti con sistema PLUGIN (installabile via marketplace)

Questi agenti supportano un vero sistema di plugin con manifest, skill, comandi e marketplace.

### Claude Code

```bash
# Installazione
/plugin install github:LuPaLa-Coder/H2C

# Oppure via marketplace
/plugin marketplace add LuPaLa-Coder/H2C
/plugin install h2c

# Sviluppo locale
claude --plugin-dir .
```

**Manifest:** `.claude-plugin/plugin.json`  
**Skill esposte:** `/h2c:h2c stat`, `/h2c:h2c compress`, `/h2c:h2c plan`, `/h2c:h2c build`, etc. (20 comandi)  
**Skill automatiche:** `h2c-architect`, `h2c-builder`, `h2c-orchestrator`, `h2c-tester`, `h2c-compress`

### GitHub Copilot CLI

```bash
# Installazione diretta da GitHub
copilot plugin install LuPaLa-Coder/H2C

# Da percorso locale (test)
copilot plugin install ./H2C

# Elenca plugin installati
copilot plugin list
```

**Manifest:** `.claude-plugin/plugin.json` (Copilot CLI lo riconosce — ordine di risoluzione: `.plugin/`, `plugin.json`, `.github/plugin/`, `.claude-plugin/`)  
**Skill esposte:** `/h2c:h2c stat`, `/h2c:h2c compress`, `/h2c:h2c plan`, etc.

### Cursor

```bash
# In-editor
/add-plugin h2c

# Oppure installa da GitHub nella UI: Settings → Plugins → Install
# URL: https://github.com/LuPaLa-Coder/H2C

# Locale (test)
mkdir -p ~/.cursor/plugins/local/
git clone https://github.com/LuPaLa-Coder/H2C ~/.cursor/plugins/local/h2c
```

**Manifest:** `.cursor-plugin/plugin.json`  
**Skill esposte:** `/h2c:h2c stat`, `/h2c:h2c compress`, etc.  
**Rules:** `.cursor/rules/h2c.mdc` (alwaysApply: true)

---

## 📄 Agenti con RULE FILE (nessun plugin, caricamento automatico)

Questi agenti **NON** hanno un sistema plugin. Leggono file di regole/istruzioni direttamente dal repository. Non serve installazione — basta clonare il repo o copiare i file.

### Cursor (rule file, alternativa al plugin)

Il file `.cursor/rules/h2c.mdc` è già nel repo. Cursor lo carica automaticamente come regola (`alwaysApply: true`).  
Viene letto anche senza installare il plugin.

### GitHub Copilot (coding assistant)

Il file `.github/copilot-instructions.md` è già nel repo. Copilot lo applica in ogni chat.

```bash
# Per usarlo in un altro progetto:
cp .github/copilot-instructions.md <tuo-progetto>/.github/
cp AGENTS.md <tuo-progetto>/
```

### Windsurf

Il file `.windsurfrules` è già nel repo. Windsurf lo carica come regole di progetto.

```bash
cp .windsurfrules <tuo-progetto>/
```

### Cline

Cline legge nativamente `AGENTS.md`, `CLAUDE.md` e `.clinerules`. I file sono già nel repo.

### Aider

```bash
aider --system-prompt AGENTS.md
```

### OpenAI Codex / Zed AI / Gemini CLI

Leggono `AGENTS.md` nativamente. Il file è già nella root del repo.

---

## 🌍 Standard Universale: `AGENTS.md`

Il file `AGENTS.md` è lo standard emergente supportato da: **Codex, Gemini CLI, Claude Code, Cursor, Copilot, Cline, Zed AI, Aider**.

È sempre disponibile nella root del repository. Basta clonare il repo e l'agente lo rileva automaticamente.

---

## 🐍 Python Runtime (qualsiasi ambiente)

```bash
pip install -e .
h2c parse file.h2c          # Parsing e validazione
h2c validate file.h2c       # Validazione protocollo
h2c transpile file.h2c --to nl    # H2C → NL
h2c transpile file.h2c --to json  # H2C → JSON
h2c run file.h2c            # Esecuzione catena
h2c stats file.h2c          # Statistiche token
```

---

## 📊 Riepilogo: Plugin vs Rules

| Agente | Plugin | Rule file | Installazione |
|--------|--------|-----------|---------------|
| **Claude Code** | ✅ `.claude-plugin/` | `CLAUDE.md` | `/plugin install github:LuPaLa-Coder/H2C` |
| **Copilot CLI** | ✅ `.claude-plugin/` | `.github/copilot-instructions.md` | `copilot plugin install LuPaLa-Coder/H2C` |
| **Cursor** | ✅ `.cursor-plugin/` | `.cursor/rules/h2c.mdc` | `/add-plugin h2c` |
| **Windsurf** | ❌ | `.windsurfrules` | File già nel repo |
| **Cline** | ❌ | `AGENTS.md` | File già nel repo |
| **Aider** | ❌ | `AGENTS.md` | `aider --system-prompt AGENTS.md` |
| **Codex** | ❌ | `AGENTS.md` | File già nel repo |
| **Zed AI** | ❌ | `AGENTS.md` | File già nel repo |
| **Gemini CLI** | ❌ | `AGENTS.md` | File già nel repo |

---

## 🔑 File nel Repository

| File | Tipo | Agenti |
|------|------|--------|
| `.claude-plugin/plugin.json` | Plugin manifest | Claude Code, Copilot CLI |
| `.cursor-plugin/plugin.json` | Plugin manifest | Cursor |
| `skills/*/SKILL.md` | Plugin skills | Claude Code, Copilot CLI, Cursor |
| `AGENTS.md` | Universale | Tutti |
| `CLAUDE.md` | Standalone | Claude Code |
| `.cursor/rules/h2c.mdc` | Rule file | Cursor |
| `.github/copilot-instructions.md` | Rule file | GitHub Copilot |
| `.windsurfrules` | Rule file | Windsurf |
| `h2c/` | Python runtime | Qualsiasi (CLI) |
