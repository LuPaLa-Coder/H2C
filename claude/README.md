# Claude Code — H2C Skill (disattivata)

Questa directory era `.claude/` ed è stata rinominata `claude/` per disattivarla.
Claude Code cerca automaticamente le skill in `.claude/skills/` — con il rename, la
skill di progetto non viene più caricata, evitando il duplicato con la skill utente
installata via `npx`.

Per riattivarla: `mv claude .claude`

## Struttura

```
claude/
  settings.local.json   # Permessi allowlist (non attivi)
  skills/
    h2c/
      SKILL.md          # Claude Code Integration v1.4
```

## skills/h2c/SKILL.md

È la skill che integra il protocollo H2C dentro Claude Code. Espone i comandi `/h2c`:

| Comando | Descrizione |
|---------|-------------|
| `/h2c plan <desc>` | Genera `[ARCH:PLAN]` |
| `/h2c build <id> <target> [desc]` | Genera `[BUILD:EXEC]` |
| `/h2c done <id> <files>` | Genera `[BUILD:DONE]` |
| `/h2c test run <id> <cmd>` | Genera `[TEST:RUN]` |
| `/h2c test pass <id> [n]` | Genera `[TEST:PASS]` |
| `/h2c test fail <id> <err> <cid>` | Genera `[TEST:FAIL]` |
| `/h2c fix <id> <tgt> <desc> <cid>` | Genera `[BUILD:FIX]` |
| `/h2c negotiate [version]` | Handshake `CTX:NEGOTIATE` |
| `/h2c findings <id> <cause>` | Genera `[STATE:FINDINGS]` |
| `/h2c compact` | Genera `[CTX:COMPACT]` |
| `/h2c prune` | Genera `[CTX:PRUNE]` |
| `/h2c end <final>` | Genera `[ORCH:END]` |
| `/h2c parse <blocco>` | Valida e spiega un blocco H2C |
| `/h2c transcode <testo>` | Converti NL → H2C |
| `/h2c compress <testo>` | Comprimi testo in blocco H2C |
| `/h2c grammar` | Reference rapida grammatica |
| `/h2c stat` | Statistiche sessione |
| `/h2c log` | Salva statistiche su `h2c_report.md` |
| `/h2c on` / `/h2c off` | Attiva/disattiva modo proattivo |
| `/h2c help` | Help |

### Come funziona

La skill opera in due modalità:

1. **Generazione** — emette SOLO il blocco H2C puro, zero markdown. Usata per
   `plan`, `build`, `done`, `test *`, `fix`, `negotiate`, `findings`, `compact`,
   `prune`, `end`.

2. **Analisi** — output in markdown con spiegazioni. Usata per `stat`, `log`,
   `parse`, `grammar`, `help`, `compress`, `transcode`, `on`, `off`.

Il protocollo H2C comprime la comunicazione AI-to-AI in blocchi strutturati su 2 righe:

```
[TIPO:SOTTOTIPO]
campo1:val|campo2:val|...
```

La specifica completa è in [`SPEC.md`](../SPEC.md). Il runtime Python è in [`h2c/`](../h2c/).

### Modo proattivo (`/h2c on`)

Quando attivo, ogni task di sviluppo viene tracciato automaticamente:
- Prima di modificare file → `[BUILD:EXEC]`
- Dopo ogni modifica → `[BUILD:DONE]`
- Task complessi → `[ARCH:PLAN]`
- In caso di errori → `[TEST:FAIL]` + `[BUILD:FIX]` + `[BUILD:DONE]`

### Perché è disattivata

La skill H2C è installata anche a livello utente (`~/.claude/skills/h2c`, installata
via `npx`). Tenere entrambe attive causava un duplicato nella lista comandi.
Rinominando `.claude/` in `claude/`, Claude Code carica solo la skill utente.

Per riattivare la skill di progetto: `mv claude .claude`
(e, se serve, rimuovere o rinominare quella utente).
