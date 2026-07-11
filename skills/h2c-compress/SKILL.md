---
name: h2c-compress
description: Comprime un prompt scritto in linguaggio naturale in un blocco H2C equivalente, riducendo il numero di token in input senza perdere informazione semantica. Restituisce il blocco H2C pronto da copiare, il conteggio token prima/dopo, la percentuale di risparmio, e una verifica di equivalenza semantica. Si attiva quando l'utente chiede di comprimere un prompt, ridurre i token, o convertire NL in H2C.
---

# H2C Compress — compressione prompt NL → H2C

Obiettivo: prendere un prompt in linguaggio naturale e restituire il blocco H2C equivalente, che l'utente possa usare al posto del prompt originale per ridurre i token in input nelle esecuzioni successive.

## Requisiti modello

Questa skill richiede **instruction-following preciso su formato rigido** per:
1. Distinguere payload (testo da comprimere) da istruzioni (testo da eseguire)
2. Produrre il blocco H2C nel formato canonico `[BLOCK:TYPE]` su **DUE RIGHE** con `|` come separatore di campi
3. Rispettare le regole anti-hallucination su CAMPI e su METRICHE senza inventare

## Procedura

### Step 1 — Identificazione
Leggi il prompt e classificalo in una delle categorie:

| Categoria | Blocco H2C | Quando |
|-----------|-----------|--------|
| Piano architetturale | `[ARCH:PLAN]` | Richieste di design, "crea app con...", "architettura per..." |
| Task implementativo | `[BUILD:EXEC]` | "implementa X in Y", "scrivi codice per..." |
| Richiesta test | `[TEST:RUN]` | "testa X", "verifica che...", "esegui test..." |
| Analisi/audit | `[STATE:FINDINGS]` | "analizza X", "trova problemi in...", "review di..." |
| Contesto/snapshot | `[CTX:PRIMITIVES]` | "contesto: ...", "stato corrente: ..." |
| Altro / multi-tipo | `[ARCH:PLAN]` + `[BUILD:EXEC]` | Prompt complessi che toccano più fasi |

### Step 2 — Estrazione campi
Per il tipo di blocco identificato, estrai SOLO i campi effettivamente presenti nel prompt:

**ARCH:PLAN**: `id` (da nome progetto), `fw` (da linguaggio/framework), `lib` (da librerie menzionate), `auth` (se menzionato), `pattern`, `tools`, `struct`, `deps`, `notes`

**BUILD:EXEC**: `id` (genera slug), `target` (file/componente), `desc` (dal prompt), `after` (se menzionate dipendenze)

**TEST:RUN**: `id`, `cmd` (comando test dal prompt)

**STATE:FINDINGS**: `id`, `cause`, `action`, `impact`, `risk`

**CTX:PRIMITIVES**: `~task`, `~constraint`, `~goal`, `~form`

### Step 3 — Emissione
Emetti il blocco H2C nel formato canonico, seguito da:
- Conteggio token prima/dopo (usa tiktoken `cl100k_base` se disponibile, altrimenti `len/3.2`)
- Percentuale di risparmio
- Verifica di equivalenza semantica (checklist rapida: tutti i requisiti del prompt originale sono coperti?)

## Regole anti-hallucination

- **Regola A — Zero invenzione**: Non aggiungere MAI un campo che non è supportato dal testo originale. Se il prompt non menziona autenticazione, non mettere `auth:`.
- **Regola B — Non forzare campi standard**: Se un'informazione esiste ma non rientra in un campo H2C standard, usa `notes:[...]` o `desc:`. Non inventare mapping.
- **Regola C — Metriche oneste**: Il conteggio token deve essere misurato, non stimato a occhio. Se non puoi misurare con tiktoken, dichiara il metodo di stima.
- **Regola D — Equivalenza verificabile**: Dopo aver generato il blocco, rileggi il prompt originale e verifica che ogni requisito sia rappresentato.

## Formato output

```
[BLOCK:TYPE]
campo1:valore1|campo2:valore2|...

---
**Token prima:** <N>
**Token dopo:** <M>
**Risparmio:** <X>%
**Metodo:** tiktoken cl100k_base | stima len/3.2

**Verifica equivalenza:**
- [x] Requisito 1
- [x] Requisito 2
- [ ] Requisito 3 (non applicabile — vedi note)
```

## Esempio

Input: "Devo creare una API meteo in Python con FastAPI che usa httpx per chiamare OpenWeatherMap. Deve avere cache TTL di 10 minuti e rate limiting di 60 richieste al minuto."

Output:
```
[ARCH:PLAN]
id:api-meteo|fw:python3.11|lib:fastapi,httpx,cachetools|auth:APIKey::env(OPENWEATHER_API_KEY)|notes:[cache_TTL_10min,rate-limit_60req-min]

---
**Token prima:** 42
**Token dopo:** 15
**Risparmio:** 64%
**Metodo:** tiktoken cl100k_base

**Verifica equivalenza:**
- [x] API meteo in Python
- [x] FastAPI come framework
- [x] httpx per chiamate HTTP
- [x] OpenWeatherMap come fonte dati
- [x] Cache TTL 10 minuti
- [x] Rate limit 60 req/min
```
