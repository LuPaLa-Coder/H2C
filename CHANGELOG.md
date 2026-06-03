# Changelog

## v1.3 — Formal EBNF, spec audit, English translation (2026-06-04)

Protocol grammar consolidated to ISO 14977 EBNF. All spec documents translated to English. Multiple protocol issues fixed following systematic audit.

### Spec fixes (15 issues resolved)

| # | Issue | Fix |
|---|-------|-----|
| 1 | Dead/broken cross-references | Re-routed to existing paths |
| 2 | BNF grammar ambiguity | Ordered `<value>` PEG-style (int, rev, list, string) |
| 3 | String definition mismatch (grammar vs parser) | Aligned parser STRING regex to grammar |
| 4 | cycle_id REQUIRED/OPTIONAL contradiction | `CASE:` marker for conditional requirement |
| 5 | State machine incomplete | Added COMPACT→BUILDING, FROZEN→BUILDING transitions |
| 6 | EBNF not valid ISO 14977 | Rewrote with proper `,` concatenation, explicit `{...}` |
| 7 | `diff:` signed integers missing | Added `signed_int` production |
| 9 | Benchmark methodology | Unified tiktoken for H2C and NL |
| 10 | `note:` vs `notes:` in examples | Fixed mapping table |
| 12 | CONTRIBUTING.md path | Corrected reference |
| 13 | Italian-only documentation | Translated all spec docs to English |
| 14 | "Zero text" whitespace ambiguity | Clarified newline exception |
| 15 | est_token undefined | Added tiktoken recommendation |
| 16 | DAG cycle detection missing | Added to VALIDATOR-6 and rule #7 |
| 17 | `~progress` contained `\|` field separator | Changed to `,` separator |

### Breaking changes
- **MINOR**: `~progress:` format changes from `layer=N\|status=X` to `layer=N,status=X`
- **NONE**: All v1.2 blocks remain valid; protocol field advances to `h2c_v1.3`

### Documentation
- All spec files translated from Italian to English: SPEC.md, grammar.md, semantics.md, blocks.md, architecture docs, parser docs, compiler docs, ecosystem docs, risk analysis, changelog, test docs
- EBNF rewritten to conform to ISO 14977 standard

## v1.2 — Documentation alignment, naming, and bug fixes (2026-05-25)

No changes to the protocol grammar. Changes only to documentation, skills, and examples, to align everything with `SPEC.md` v1.2.

### Skills — renames and fixes

| Before | After |
|--------|-------|
| `skills/h2c_v3.md` | `skills/h2c_architect.md` (id: `h2c_architect_v1.2`) |
| `skills/orch_v1.md` | `skills/h2c_orchestrator.md` (id: `h2c_orchestrator_v1.2`) |
| `skills/build.md` | `skills/h2c_builder.md` (id: `h2c_builder_v1.2`) |
| `skills/test.md` | `skills/h2c_tester.md` (id: `h2c_tester_v1.2`) |

Specific fixes:

- **h2c_architect**: added `[SKILL:PROMPT]` marker aligned with the other 3 skills; fixed "Blocks" table that had 2-column header and 3-column separator (not rendering); fixed causal order of `cycle_id` in rule 5 (`TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS`); references to `§3.3 SPEC` / `§3.5 SPEC` now cite `SPEC.md` by name.
- **h2c_orchestrator**: collapsed the two duplicate rules `[BUILD:DONE] with/without cycle_id → [TEST:RUN]` (both had the same routing) into one with the `cycle_id` propagation rule; added explicit rules to handle `[TEST:PASS]` with/without `cycle_id`; fixed `[REGOLES]` → `[REGOLE]`.
- **h2c_builder**: removed `[BUILD:FIX]` block from "FORMATO_OUTPUT" (was a wrong copy-paste — Builder does not emit FIX, it's output from the Orchestrator); activation trigger corrected to only `[BUILD:EXEC]` (even after a FIX, the Orchestrator resends an EXEC with inherited `cycle_id`); fixed `[REGOLES]` → `[REGOLE]`; fixed `diff:` format from `[file~+n]` to `[file~N,+M]`.
- **h2c_tester**: rule 2 reformulated: the Tester executes the received `cmd` and reads the exit code, does not perform syntactic/static analysis; fixed `[REGOLES]` → `[REGOLE]`.

### README

- Fixed malformed image alt tag: `![Human-to-Compressed)](...)` → `![Human-to-Compressed](...)`.
- Typical flow placed in code block (previously broke markdown rendering).
- "Skills" table no longer included two extra rows `[CTX:PRUNE]` / `[CTX:COMPACT]` that were accidentally attached.
- Updated skill paths to new `h2c_*.md` names.
- Changed "h2c v1.1" label in first row of Skills table to "h2c Architect".

### SPEC.md

- §2.6 `TEST:PASS`: clarified that `cycle_id` is REQUIRED when PASS closes a fix cycle opened by a previous `BUILD:FIX`, OPTIONAL otherwise. SPEC v1.2 declared it only OPTIONAL, conflicting with §7.4.
- §2.6 `TEST:FAIL`: already required `cycle_id` REQUIRED; made the rule more explicit ("opens or continues a fix cycle").

### Examples

- `examples/api-meteo.md`, `examples/todo-console.md`: removed `[ARCH:DONE]` block (does not exist in SPEC v1.2 — allowed ARCH subtypes are only `PLAN`); converted `note:` to `notes:[...]` as per §2.1.
- `examples/prune_demo.md`: removed `~pruned_edges` field from `CTX:UPDATE` (deprecated in v1.2, see SPEC §3.2); fixed `final:demo_completato` → `final:complete` (allowed values are only `complete|error|timeout`, SPEC §5); added `cycle_id`/`retry_n` to fix cycle blocks; normalized `keep:` syntax (removed extra non-standard `ids:` field); added `fw:` REQUIRED in `ARCH:PLAN`; removed non-spec fields (`target:` in `TEST:RUN`, `fail_count:0` in `TEST:PASS`); updated title to v1.2.

### Test.md

- Updated to v1.2: protocol, expected fields (`cycle_id`, `retry_n`), `CTX:FREEZE` for Test 5, v1.1 vs v1.2 comparison.

### Archive

- `Test-Sonnet4.6.md` → `archive/test-sonnet-4.6-v1.1.md` with archive notice at the top (was a v1.1 test, no longer aligned with SPEC v1.2).

### Unchanged (by choice)

- `opus4_7/REPORT.md` and the 5 `.h2c` files under `opus4_7/`: are historical evidence of the Opus 4.7 test from 2026-05-25 and contain the recommendations that motivated these fixes. Left intact.
- `LICENSE`, `1779633660140.png`: unchanged.
