# Changelog

## v1.2 — Allineamento documentazione, naming e fix bug (2026-05-25)

Nessun cambiamento alla grammatica del protocollo. Modifiche solo a documentazione, skill e esempi, per allineare tutto a `SPEC.md` v1.2.

### Skill — rename e fix

| Prima | Dopo |
|---|---|
| `skills/h2c_v3.md` | `skills/h2c_architect.md` (id: `h2c_architect_v1.2`) |
| `skills/orch_v1.md` | `skills/h2c_orchestrator.md` (id: `h2c_orchestrator_v1.2`) |
| `skills/build.md` | `skills/h2c_builder.md` (id: `h2c_builder_v1.2`) |
| `skills/test.md` | `skills/h2c_tester.md` (id: `h2c_tester_v1.2`) |

Fix specifici:

- **h2c_architect**: aggiunto marker `[SKILL:PROMPT]` allineato alle altre 3 skill; corretta tabella "Blocchi" che aveva header a 2 colonne e separator a 3 (non renderizzava); corretto ordine causale `cycle_id` in regola 5 (`TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS`); i riferimenti a `§3.3 SPEC` / `§3.5 SPEC` ora citano `SPEC.md` per nome.
- **h2c_orchestrator**: collassate le due regole duplicate `[BUILD:DONE] con/senza cycle_id → [TEST:RUN]` (entrambe avevano stesso routing) in una sola con la regola di propagazione di `cycle_id`; aggiunte regole esplicite per gestire `[TEST:PASS]` con/senza `cycle_id`; corretto `[REGOLES]` → `[REGOLE]`.
- **h2c_builder**: rimosso il blocco `[BUILD:FIX]` dal "FORMATO_OUTPUT" (era un copia-incolla sbagliato — il Builder non emette FIX, è output dell'Orchestrator); trigger di attivazione corretto a solo `[BUILD:EXEC]` (anche dopo un FIX, l'Orchestrator rispedisce un EXEC con `cycle_id` ereditato); corretto `[REGOLES]` → `[REGOLE]`; corretto formato `diff:` da `[file~+n]` a `[file~N,+M]`.
- **h2c_tester**: regola 2 riformulata: il Tester esegue il `cmd` ricevuto e legge l'exit code, non fa analisi sintattica/statica; corretto `[REGOLES]` → `[REGOLE]`.

### README

- Corretto alt tag malformato dell'immagine: `![Human-to-Compressed)](...)` → `![Human-to-Compressed](...)`.
- Flusso tipico messo in code block (prima si rompeva il rendering markdown).
- Tabella "Skills" non includeva più due righe `[CTX:PRUNE]` / `[CTX:COMPACT]` che le si erano accidentalmente attaccate.
- Aggiornati i percorsi delle skill ai nuovi nomi `h2c_*.md`.
- Etichetta "h2c v1.1" della prima riga della tabella Skills sostituita con "h2c Architect".

### SPEC.md

- §2.6 `TEST:PASS`: chiarito che `cycle_id` è REQUIRED quando il PASS chiude un ciclo di fix aperto da un `BUILD:FIX` precedente, OPTIONAL altrimenti. La SPEC v1.2 lo dichiarava solo OPTIONAL, in conflitto con §7.4.
- §2.6 `TEST:FAIL`: già richiedeva `cycle_id` REQUIRED; resa la regola più esplicita ("apre o prosegue un ciclo di fix").

### Esempi

- `examples/api-meteo.md`, `examples/todo-console.md`: rimosso il blocco `[ARCH:DONE]` (non esiste in SPEC v1.2 — i sottotipi ammessi per ARCH sono solo `PLAN`); convertito `note:` in `notes:[...]` come previsto da §2.1.
- `examples/prune_demo.md`: rimosso il campo `~pruned_edges` da `CTX:UPDATE` (deprecato in v1.2, vedi SPEC §3.2); corretto `final:demo_completato` → `final:complete` (i valori ammessi sono solo `complete|error|timeout`, SPEC §5); aggiunto `cycle_id`/`retry_n` ai blocchi del ciclo di fix; normalizzata sintassi `keep:` (rimosso campo `ids:` extra, non standard); aggiunto `fw:` REQUIRED in `ARCH:PLAN`; rimossi campi non-spec (`target:` in `TEST:RUN`, `fail_count:0` in `TEST:PASS`); titolo aggiornato a v1.2.

### Test.md

- Aggiornato a v1.2: protocollo, campi attesi (`cycle_id`, `retry_n`), `CTX:FREEZE` per Test 5, confronto v1.1 vs v1.2.

### Archivio

- `Test-Sonnet4.6.md` → `archive/test-sonnet-4.6-v1.1.md` con nota di archivio in testa (era un test v1.1, non più allineato alla SPEC v1.2).

### Non modificato (per scelta)

- `opus4_7/REPORT.md` e i 5 file `.h2c` sotto `opus4_7/`: sono evidenza storica del test Opus 4.7 del 2026-05-25 e contengono le raccomandazioni che hanno motivato questi fix. Si lasciano intatti.
- `LICENSE`, `1779633660140.png`: invariati.
