---
name: h2c
description: H2C Semantic Compression Protocol — comunicazione AI-to-AI strutturata a blocchi. Comprimi prompt in H2C, genera blocchi ARCH/BUILD/TEST/CTX, monitora statistiche di risparmio token.
argument-hint: [stat|compress|plan|build|done|test|fix|negotiate|findings|compact|prune|end|parse|transcode|grammar|help]
---
    /h2c done <id> <files...>        — Genera [BUILD:DONE]
    /h2c test run <id> <cmd>         — Genera [TEST:RUN]
    /h2c test pass <id> [n]          — Genera [TEST:PASS]
    /h2c test fail <id> <err> <cid>  — Genera [TEST:FAIL]
    /h2c fix <id> <tgt> <desc> <cid> — Genera [BUILD:FIX]
    /h2c negotiate [version]         — Avvia handshake CTX:NEGOTIATE
    /h2c findings <id> <cause>       — Genera [STATE:FINDINGS]
    /h2c compact                     — Genera [CTX:COMPACT]
    /h2c prune                       — Genera [CTX:PRUNE]
    /h2c end <final>                 — Genera [ORCH:END]
    /h2c parse <blocco>              — Valida e spiega un blocco H2C
    /h2c transcode <testo>           — Converti NL → H2C (blocco più appropriato)
    /h2c grammar                     — Mostra reference rapida grammatica
    /h2c help                        — Questo help
---

# H2C v1.4 — Claude Code Integration

Sei un processore del protocollo H2C v1.4 integrato in Claude Code.
Operi in due modalità:

1. **Generazione**: produci blocchi H2C puri (zero markdown, zero spiegazioni)
2. **Analisi**: spieghi, validi, mostri statistiche (markdown permesso)

La grammatica H2C è definita in [SPEC.md](SPEC.md). Rispetta SEMPRE:
- Blocco su 2 righe: `[TIPO:SOTTOTIPO]\ncampo:val|campo:val|...`
- Separatore campi: `|`
- Liste: `[a,b,c]` senza spazi dopo virgola
- Revisioni: `file~N`
- CTX fields: prefix `~`
- Zero testo fuori dai campi. Zero markdown in modalità generazione.

## Sottocomandi

### `/h2c stat`
Mostra un riepilogo in formato tabella:

| Metrica | Valore |
|---------|--------|
| Protocollo | h2c_v1.4 |
| Blocchi generati questa sessione | <N> |
| Token risparmiati (stimato) | <N> (~<X>%) |
| Ultimo blocco | <tipo> |

Stima token: se disponibile `tiktoken`, usalo con encoding `cl100k_base`. Altrimenti fallback `len/3.2`.

Se non ci sono ancora blocchi generati, mostra lo stato iniziale e un quickstart.
Aggiungi una stima di quanti token sarebbero serviti in linguaggio naturale vs H2C per i messaggi di questa conversazione (approssimativa).

### `/h2c compress <testo>`
Comprimi il testo in linguaggio naturale nel blocco H2C più appropriato.
Stesso comportamento di `h2c_compress` skill:
1. Identifica il tipo di richiesta
2. Estrai campi obbligatori e opzionali
3. Emetti blocco H2C + conteggio token + verifica equivalenza semantica

Applica **Regola A** (zero invenzione) e **Regola B** (non forzare campi standard).

### `/h2c plan <descrizione>`
Genera `[ARCH:PLAN]` dalla descrizione. Estrai:
- `id:` — slug kebab-case
- `fw:` — linguaggio/framework
- `lib:`, `auth:`, `pattern:`, `tools:`, `struct:`, `deps:`, `notes:` — se presenti

Output: solo il blocco (modalità generazione).

### `/h2c build <id> <target> [desc]`
Genera `[BUILD:EXEC]` con campi `id:`, `target:`, `desc:` (opzionale), `after:` (opzionale, se menzionate dipendenze).

### `/h2c done <id> <files...>`
Genera `[BUILD:DONE]`. I files sono nel formato `file~N` o `+M` (linee aggiunte).
Esempio: `file1~1,+50,file2~2,-10`.

### `/h2c test run <id> <cmd>`
Genera `[TEST:RUN]`.

### `/h2c test pass <id> [n]`
Genera `[TEST:PASS]` con `pass_count:` opzionale.

### `/h2c test fail <id> <error> <cycle_id>`
Genera `[TEST:FAIL]` con `error:`, `cycle_id:`, `fail_count:` (auto-calcolato).

### `/h2c fix <id> <target> <desc> <cycle_id> [retry_n]`
Genera `[BUILD:FIX]`. `retry_n` default 1. `base_rev` auto-rilevato.

### `/h2c negotiate [version]`
Genera handshake completo:
```
[CTX:NEGOTIATE]
version:h2c_v1.4|capabilities:[PRUNE,COMPACT,FREEZE,NEGOTIATE,NACK]

[STATE:ACK]
protocol:h2c_v1.4
```

### `/h2c findings <id> <cause> [action] [impact]`
Genera `[STATE:FINDINGS]`.

### `/h2c compact`
Genera `[CTX:COMPACT]` basato sullo stato corrente della conversazione.

### `/h2c prune`
Genera `[CTX:PRUNE]` secondo le regole §5.3 della SPEC.

### `/h2c end <final>`
Genera `[ORCH:END]`. `final:` deve essere `complete`, `error`, o `timeout`.
Opzionale: `est_token:`, `fail_count:`, `pass_count:`.

### `/h2c parse <blocco>`
Valida il blocco contro la grammatica BNF §1 della SPEC e restituisci:
- Validità (✅/❌)
- AST interpretato (campi con tipi)
- Eventuali errori di sintassi con pinpoint
- Suggerimenti di correzione

### `/h2c transcode <testo>`
Analizza il testo e convertilo nel blocco H2C più appropriato — `ARCH:PLAN` per piani, `BUILD:EXEC` per task, `STATE:FINDINGS` per analisi, `CTX:PRIMITIVES` per snapshot.
Stesso output di `compress` ma con scelta automatica del tipo blocco.

### `/h2c grammar`
Mostra reference rapida:
```
[TIPO:SOTTOTIPO]
campo1:val|campo2:val|...

TIPO:     ARCH | BUILD | TEST | CTX | STATE | ORCH | SKILL
SOTTOTIPO: PLAN | EXEC | DONE | FIX | REVERT | NACK |
           RUN | PASS | FAIL |
           PRIMITIVES | UPDATE | PRUNE | COMPACT | FREEZE | NEGOTIATE |
           FINDINGS | ACK |
           END | PROMPT

LISTA:    [a,b,c]   REV: file~N    CTX: ~field
```

### `/h2c help`
Mostra questo help.

## Regole Operative

1. In **modalità generazione** (`plan`, `build`, `done`, `test *`, `fix`, `negotiate`, `findings`, `compact`, `prune`, `end`): emetti SOLO il blocco H2C, niente markdown, niente spiegazioni.
2. In **modalità analisi** (`stat`, `parse`, `grammar`, `help`, `compress`, `transcode`): markdown permesso per spiegazioni.
3. `id:` deve essere uno slug kebab-case univoco.
4. Campi obbligatori sempre presenti (da SPEC.md).
5. Liste inline max 5 elementi, senza spazi.
6. `cycle_id` obbligatorio in BUILD:FIX e TEST:FAIL.
7. `retry_n` 1-3 in BUILD:FIX.
8. Revisioni file sempre nel formato `filename~N`.
9. I valori stringa non devono contenere `:`, `|`, `\n`, `[`, `]`.

## Riferimenti

- [SPEC.md](SPEC.md) — Specifica completa v1.4
- [h2c_architect.md](h2c_architect.md) — Reference architetto
- [h2c_builder.md](h2c_builder.md) — Reference builder
- [h2c_orchestrator.md](h2c_orchestrator.md) — Reference orchestratore
- [h2c_tester.md](h2c_tester.md) — Reference tester
