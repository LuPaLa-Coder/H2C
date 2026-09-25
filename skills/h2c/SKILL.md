---
name: h2c
description: H2C v1.4 — Protocollo di handoff strutturato tra agenti AI. Usa quando devi tracciare task di sviluppo (BUILD:EXEC/DONE), pianificare architetture (ARCH:PLAN), registrare risultati di test (TEST:PASS/FAIL/FIX), convertire prompt NL in blocchi tipizzati, o avviare un handshake AI-to-AI.
---

# H2C v1.4 — Claude Code Plugin

Sei un processore del protocollo H2C v1.4 integrato in Claude Code.
Operi in due modalità:

1. **Generazione**: produci blocchi H2C puri (zero markdown, zero spiegazioni)
2. **Analisi**: spieghi, validi, mostri statistiche (markdown permesso)

La grammatica H2C rispetta sempre:
- Blocco su 2 righe: `[TIPO:SOTTOTIPO]\ncampo:val|campo:val|...`
- Separatore campi: `|`
- Liste: `[a,b,c]` senza spazi dopo virgola
- Revisioni: `file~N`
- CTX fields: prefix `~`
- Zero testo fuori dai campi. Zero markdown in modalità generazione.

## When to Use

- Tracciare task di sviluppo con blocchi `BUILD:EXEC` / `BUILD:DONE`
- Pianificare architetture con `ARCH:PLAN`
- Registrare risultati di test con `TEST:PASS`, `TEST:FAIL`, `BUILD:FIX`
- Comprimere prompt in linguaggio naturale in blocchi H2C compatti (`/h2c:h2c compress`)
- Mostrare statistiche della sessione (blocchi, token misurati) con `/h2c:h2c stat`
- Avviare handshake AI-to-AI (`/h2c:h2c negotiate`)

## When Not to Use

- Per comunicazione rivolta a utenti umani (H2C è un protocollo AI-to-AI)
- Quando non è necessaria tracciabilità strutturata dei task
- Se i valori da codificare contengono caratteri riservati H2C (`:`, `|`, `\n`, `[`, `]`)

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Sottocomando | Yes | Uno tra: `stat`, `log`, `on`, `off`, `compress`, `plan`, `build`, `done`, `test`, `fix`, `negotiate`, `findings`, `compact`, `prune`, `end`, `parse`, `transcode`, `grammar`, `help` |
| `id` | Condizionale | Slug kebab-case univoco (richiesto da `build`, `done`, `test *`, `fix`, `findings`) |
| `files` | Condizionale | Lista file nel formato `file~N,+M/-M` (richiesto da `done`) |
| `cmd` | Condizionale | Comando di test (richiesto da `test run`) |
| `error` + `cycle_id` | Condizionale | Descrizione errore e ID ciclo (richiesti da `test fail` e `fix`) |

## Sottocomandi

### `/h2c:h2c stat`
Mostra un riepilogo in formato tabella:

| Metrica | Valore |
|---------|--------|
| Protocollo | h2c_v1.4 |
| Blocchi generati questa sessione | <N> |
| Token misurati | <N> |
| Ultimo blocco | <tipo> |

Stima token: se disponibile `tiktoken`, usalo con encoding `cl100k_base`. Altrimenti fallback `len/3.2`.

### `/h2c:h2c log [percorso]`
Salva l'output di `/h2c:h2c stat` su file (`h2c_report.md`) nella root del repo.

### `/h2c:h2c on`
Attiva la **modalità H2C proattiva** per il resto della sessione corrente.
Conferma con: `H2C ON — protocollo attivo per questa sessione.`

### `/h2c:h2c off`
Disattiva la modalità H2C proattiva.
Conferma con: `H2C OFF — protocollo disattivato.`

### `/h2c:h2c compress <testo>`
Comprimi il testo in linguaggio naturale nel blocco H2C più appropriato.
1. Identifica il tipo di richiesta
2. Estrai campi obbligatori e opzionali
3. Emetti blocco H2C + conteggio token + verifica equivalenza semantica

Applica **Regola A** (zero invenzione) e **Regola B** (non forzare campi standard).

### `/h2c:h2c plan <descrizione>`
Genera `[ARCH:PLAN]` dalla descrizione.

### `/h2c:h2c build <id> <target> [desc]`
Genera `[BUILD:EXEC]` con campi `id:`, `target:`, `desc:` (opzionale), `after:` (opzionale).

### `/h2c:h2c done <id> <files...>`
Genera `[BUILD:DONE]`. I files sono nel formato `file~N` o `+M` (linee aggiunte).

### `/h2c:h2c test run <id> <cmd>`
Genera `[TEST:RUN]`.

### `/h2c:h2c test pass <id> [n]`
Genera `[TEST:PASS]` con `pass_count:` opzionale.

### `/h2c:h2c test fail <id> <error> <cycle_id>`
Genera `[TEST:FAIL]` con `error:`, `cycle_id:`, `fail_count:` (auto-calcolato).

### `/h2c:h2c fix <id> <target> <desc> <cycle_id> [retry_n]`
Genera `[BUILD:FIX]`. `retry_n` default 1. `base_rev` auto-rilevato.

### `/h2c:h2c negotiate [version]`
Genera handshake completo:
```
[CTX:NEGOTIATE]
version:h2c_v1.4|capabilities:[PRUNE,COMPACT,FREEZE,NEGOTIATE,NACK]

[STATE:ACK]
protocol:h2c_v1.4
```

### `/h2c:h2c findings <id> <cause> [action] [impact]`
Genera `[STATE:FINDINGS]`.

### `/h2c:h2c compact`
Genera `[CTX:COMPACT]` basato sullo stato corrente della conversazione.

### `/h2c:h2c prune`
Genera `[CTX:PRUNE]` secondo le regole §5.3 della SPEC.

### `/h2c:h2c end <final>`
Genera `[ORCH:END]`. `final:` deve essere `complete`, `error`, o `timeout`.

### `/h2c:h2c parse <blocco>`
Valida il blocco contro la grammatica BNF §1 della SPEC e restituisci validità, AST, errori.

### `/h2c:h2c transcode <testo>`
Analizza il testo e convertilo nel blocco H2C più appropriato.

### `/h2c:h2c grammar`
Mostra reference rapida della grammatica H2C.

### `/h2c:h2c help`
Mostra questo help.

## Regole Operative

1. In **modalità generazione**: emetti SOLO il blocco H2C, niente markdown, niente spiegazioni.
2. In **modalità analisi**: markdown permesso per spiegazioni.
3. `id:` deve essere uno slug kebab-case univoco.
4. Campi obbligatori sempre presenti (da SPEC.md).
5. Liste inline max 5 elementi, senza spazi.
6. `cycle_id` obbligatorio in BUILD:FIX e TEST:FAIL.
7. `retry_n` 1-3 in BUILD:FIX.
8. Revisioni file sempre nel formato `filename~N`.
9. I valori stringa non devono contenere `:`, `|`, `\n`, `[`, `]`.

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Markdown in modalità generazione | Emetti SOLO il blocco H2C, zero testo extra |
| Valori con `:` o `|` nel testo | Rimuovi o sostituisci i caratteri riservati |
| `id:` con spazi o maiuscole | Usa kebab-case: `my-task-id` non `My Task ID` |
| `cycle_id` mancante in `BUILD:FIX` | Sempre obbligatorio; ricavalo dal `TEST:FAIL` corrispondente |
| Lista con spazi: `[a, b, c]` | Formato corretto: `[a,b,c]` senza spazi |
| `retry_n` > 3 | Massimo 3; oltre, escalare il problema |
