---
name: h2c
description: H2C v1.4 Semantic Compression Protocol per comunicazione AI-to-AI strutturata. Usa quando devi tracciare task di sviluppo (BUILD:EXEC/DONE), pianificare architetture (ARCH:PLAN), registrare risultati di test (TEST:PASS/FAIL/FIX), comprimere prompt NL in blocchi tipizzati, o avviare un handshake AI-to-AI.
---

# H2C v1.4 — Claude Code Integration

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
- Comprimere prompt in linguaggio naturale in blocchi H2C compatti (`/h2c compress`)
- Monitorare il risparmio token nella sessione (`/h2c stat`)
- Avviare handshake AI-to-AI (`/h2c negotiate`)

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

### `/h2c log [percorso]`
Salva l'output di `/h2c stat` su file (`h2c_report.md`) nella root del repo.

**Filename**: `h2c_report.md` (fisso, sovrascritto a ogni `/h2c log`).

**Percorso**: se specificato, usa quel percorso; altrimenti root del repo git (`git rev-parse --show-toplevel`), fallback CWD.

**Formato**: identico a `/h2c stat` — stesso header, stesse tabelle, stesso contenuto. Nessuna colonna aggiuntiva.

Dopo il salvataggio, conferma con `Report salvato in: <percorso assoluto>`.


### `/h2c on`
Attiva la **modalità H2C proattiva** per il resto della sessione corrente.

Quando attivo, per ogni task di sviluppo:
- **Prima** di modificare file: generi `[BUILD:EXEC]` con descrizione del task
- **Dopo** ogni modifica: generi `[BUILD:DONE]` con file modificati e delta
- Per task complessi: generi `[ARCH:PLAN]` se serve pianificazione
- In caso di errori: generi `[TEST:FAIL]` + `[BUILD:FIX]` + `[BUILD:DONE]`

Conferma con:
```
H2C ON — protocollo attivo per questa sessione. Ogni task sarà tracciato con blocchi BUILD:EXEC / BUILD:DONE.
```

### `/h2c off`
Disattiva la modalità H2C proattiva. Torno al comportamento standard.

Conferma con:
```
H2C OFF — protocollo disattivato. Usa /h2c on per riattivarlo.
```

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
2. In **modalità analisi** (`stat`, `log`, `on`, `off`, `parse`, `grammar`, `help`, `compress`, `transcode`): markdown permesso per spiegazioni.
3. `id:` deve essere uno slug kebab-case univoco.
4. Campi obbligatori sempre presenti (da SPEC.md).
5. Liste inline max 5 elementi, senza spazi.
6. `cycle_id` obbligatorio in BUILD:FIX e TEST:FAIL.
7. `retry_n` 1-3 in BUILD:FIX.
8. Revisioni file sempre nel formato `filename~N`.
9. I valori stringa non devono contenere `:`, `|`, `\n`, `[`, `]`.

## Validation

- [ ] Il blocco generato è su esattamente 2 righe: `[TIPO:SOTTOTIPO]` + campi `|`-separati
- [ ] Nessun testo o markdown fuori dal blocco in modalità generazione
- [ ] Tutti i campi obbligatori sono presenti (da grammatica H2C)
- [ ] `id:` è in formato kebab-case
- [ ] `cycle_id` presente in `BUILD:FIX` e `TEST:FAIL`
- [ ] `retry_n` nel range 1–3 per `BUILD:FIX`
- [ ] Nessun valore contiene caratteri riservati: `:`, `|`, `\n`, `[`, `]`

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Markdown in modalità generazione | Emetti SOLO il blocco H2C, zero testo extra |
| Valori con `:` o `\|` nel testo | Rimuovi o sostituisci i caratteri riservati |
| `id:` con spazi o maiuscole | Usa kebab-case: `my-task-id` non `My Task ID` |
| `cycle_id` mancante in `BUILD:FIX` | Sempre obbligatorio; ricavalo dal `TEST:FAIL` corrispondente |
| Lista con spazi: `[a, b, c]` | Formato corretto: `[a,b,c]` senza spazi |
| `retry_n` > 3 | Massimo 3; oltre, escalare il problema |

## Riferimenti

> ⚠️ I file di riferimento elencati non sono ancora presenti nella directory della skill. Creali per estendere la documentazione.

- `SPEC.md` — Specifica completa grammatica BNF v1.4
- `h2c_architect.md` — Reference per il ruolo architetto
- `h2c_builder.md` — Reference per il ruolo builder
- `h2c_orchestrator.md` — Reference per il ruolo orchestratore
- `h2c_tester.md` — Reference per il ruolo tester
