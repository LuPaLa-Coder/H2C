# H2C Protocol Conformance Tests

Test deterministici di conformità al protocollo H2C v1.4. Chiunque può clonare il repo ed eseguirli — stesso input, stesso risultato, sempre.

## Esecuzione

```bash
# Tutti i test
python3 conformance/run.py

# Con output dettagliato
python3 conformance/run.py --verbose

# Report JSON
python3 conformance/run.py --json

# Singolo test
python3 conformance/run.py test1
```

Oppure via shell:

```bash
./conformance/run.sh
./conformance/run.sh --verbose
```

## Test

| # | Test | Complessità | File |
|---|------|-------------|------|
| 1 | Hello World | Simple | `tests/fixtures/test1-hello-world.h2c` |
| 2 | Calculator CLI | Medium | `tests/fixtures/test2-calculator.h2c` |
| 3 | Clean Architecture | Advanced | `tests/fixtures/test3-clean-arch.h2c` |
| 4 | RAG Pipeline | Very Complex | `tests/fixtures/test4-rag-pipeline.h2c` |
| 5 | Stress (130 msg) | Stress | `tests/fixtures/test5-stress-130msg.h2c` |

## Cosa viene validato (deterministico)

Ogni test esegue 4 fasi:

1. **Parse** — il file `.h2c` viene parsato senza errori
2. **Validate** — tutti i blocchi rispettano le regole del protocollo (REQUIRED fields, tipi, range)
3. **State Machine** — la catena di blocchi attraversa gli stati FSM corretti fino a TERM
4. **Agent Runtime** — l'agente processa la catena senza errori

### Check strutturali
- Numero minimo di blocchi
- Primo blocco = `CTX:NEGOTIATE`
- Ultimo blocco = `ORCH:END`
- Blocchi richiesti presenti (es. `BUILD:FIX`, `TEST:PASS`)
- Campi obbligatori presenti (es. `cycle_id`, `retry_n`)

## Uscita

- **Exit code 0** = tutti i test passati
- **Exit code 1** = almeno un test fallito
- Output sempre identico per lo stesso input — zero randomness
