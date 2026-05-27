# H2C Protocol - Specifica v1.2

## 1. Grammatica formale (BNF)

```
<message>      ::= <blocco>
<blocco>       ::= "[" <tipo> ":" <sottotipo> "]" "\n" <campi>
<campi>        ::= <campo> ("|" <campo>)*
<campo>        ::= <chiave> ":" <valore>
<chiave>       ::= [a-zA-Z_][a-zA-Z0-9_]*
<valore>       ::= <stringa> | <lista> | <rev> | <int>
<stringa>      ::= [^\|\n\[\]]+
<lista>        ::= "[" <stringa> ("," <stringa>)* "]"
<rev>          ::= <stringa> "~" <int>
<int>          ::= [0-9]+

<tipo>         ::= "ARCH" | "BUILD" | "TEST" | "CTX" | "STATE" | "ORCH" | "SKILL"
<sottotipo>    ::= "PLAN" | "EXEC" | "DONE" | "FIX" | "REVERT"
                 | "RUN" | "PASS" | "FAIL"
                 | "PRIMITIVES" | "UPDATE" | "PRUNE" | "COMPACT" | "FREEZE"
                 | "FINDINGS" | "ACK"
                 | "END" | "PROMPT"
```

### 1.1 Separatori

| Sep | Uso | Regex |
|-----|-----|-------|
| `:` | chiave:valore | `[^:\\|\\n\\[\\]]+:[^:\\|\\n\\[\\]]+` |
| `\|` | tra campi | `\|` |
| `,` | tra elementi lista | `,` |
| `[]` | delimita blocco e liste | `\[...\]` |
| `~` | prefisso campi CTX e revisioni file | `~` |

### 1.2 Convenzioni

- Liste inline: max 5 elementi, no spazi dopo virgola
- Campi REQUIRED: devono essere presenti o il blocco è invalido
- Campi OPTIONAL: omessi se non applicabili
- Ordine campi: irrilevante per parsing
- Zero testo fuori dai campi: violazione = blocco scartato

---

## 2. Blocchi standard

### 2.1 ARCH:PLAN

```
[ARCH:PLAN]
REQUIRED: id:<stringa>|fw:<stringa>
OPTIONAL: lib:<stringa>|auth:<stringa>|pattern:<stringa>|tools:<lista>|struct:<lista>|deps:<stringa>|notes:<lista>
```

### 2.2 BUILD:EXEC

```
[BUILD:EXEC]
REQUIRED: id:<stringa>|target:<stringa>
OPTIONAL: after:<lista>|desc:<stringa>|cmd:<stringa>
```
- `after:`: lista di id prerequisiti (DAG esplicito)
- `cmd:`: comando di build eseguito (opzionale, es. `dotnet build`, `npm run build`)

### 2.3 BUILD:DONE

```
[BUILD:DONE]
REQUIRED: id:<stringa>|diff:<lista_rev>
OPTIONAL: rev:<int>|notes:<lista>|cycle_id:<stringa>
```
- `diff:`: lista `[file~N,+M,file2~N,-K]`
- `rev:`: default 1 se omesso
- `cycle_id:`: lega questo DONE al FIX che lo ha generato

### 2.4 BUILD:FIX

```
[BUILD:FIX]
REQUIRED: id:<stringa>|target:<stringa>|base_rev:<int>|desc:<stringa>
REQUIRED: cycle_id:<stringa>
OPTIONAL: retry_n:<int>|cmd:<stringa>
```
- `cycle_id:`: identifica univocamente il ciclo di fix (es. `fix-qdrant-collection`)
- `retry_n:`: contatore progressivo 1-3. Se >3 o omesso: errore
- `base_rev:`: revisione del file su cui applicare la fix

### 2.5 BUILD:REVERT

```
[BUILD:REVERT]
REQUIRED: id:<stringa>|target:<stringa>|to_rev:<int>
```

### 2.6 TEST:RUN / TEST:PASS / TEST:FAIL

```
[TEST:RUN]
REQUIRED: id:<stringa>|cmd:<stringa>

[TEST:PASS]
REQUIRED: id:<stringa>
REQUIRED se chiude un ciclo di fix: cycle_id:<stringa>
OPTIONAL: pass_count:<int>

[TEST:FAIL]
REQUIRED: id:<stringa>|error:<stringa>|cycle_id:<stringa>
OPTIONAL: fail_count:<int>|pass_count:<int>
```
- `cycle_id:` in TEST:FAIL è sempre obbligatorio (apre o prosegue un ciclo di fix)
- `cycle_id:` in TEST:PASS è obbligatorio quando il PASS chiude un ciclo di fix aperto (cycle_id presente in un BUILD:FIX precedente non ancora chiuso); opzionale negli altri casi
- `fail_count:`: contatore assoluto per cycle_id (resetta quando cambia cycle_id)

---

## 3. Blocchi di contesto

### 3.1 CTX:PRIMITIVES

```
[CTX:PRIMITIVES]
~task:<stringa>
~constraint:<stringa>
~goal:<stringa>
OPTIONAL: ~form:<stringa>
```
Snapshot iniziale dello stato. Campi con prefisso `~`.

### 3.2 CTX:UPDATE

```
[CTX:UPDATE]
REQUIRED: ~progress:<layer=N|status=X>
REQUIRED: ~next:<stringa>
OPTIONAL: ~active_files:<lista_rev>
```
- `~progress:`: layer corrente e stato (done/in_progress/blocked)
- `~next:`: prossimo step
- `~active_files:`: file attualmente in gioco con revisione
- **NOTA**: `~pruned_edges` RIMOSSO in v1.2. Usare CTX:PRUNE come unica autorità per pruning

### 3.3 CTX:PRUNE

```
[CTX:PRUNE]
REQUIRED: keep:<"last_N" | lista_ids>
REQUIRED: pruned:<lista_ids>
OPTIONAL: reason:<stringa>
```
- **Obbligatorio ogni 5 messaggi** (contatore globale)
- `keep:`: DEVE includere almeno: ultimo ARCH:PLAN, tutti i BUILD:FIX aperti, ultimo COMPACT
- `pruned:`: DEVE includere BUILD:EXEC il cui BUILD:DONE è già stato emesso, TEST:RUN con esito noto
- `reason:`: opzionale, spiega perché certi msg sono stati potati

**Regole di pruning (REGOLE, non suggerimenti):**

| Blocco | Condizione | Prunabile? |
|--------|-----------|------------|
| ARCH:PLAN | Esiste COMPACT successivo | ✅ Sì |
| ARCH:PLAN | Ultimo emesso, nessun COMPACT | ❌ NO |
| BUILD:EXEC | BUILD:DONE corrispondente emesso | ✅ Sì |
| BUILD:EXEC | BUILD:DONE NON ancora emesso | ❌ NO |
| BUILD:FIX | cycle_id ancora aperto | ❌ NO |
| BUILD:FIX | cycle_id chiuso (TEST:PASS) | ✅ Sì |
| BUILD:DONE | Esiste COMPACT successivo | ✅ Sì |
| TEST:RUN | Esito (PASS/FAIL) emesso | ✅ Sì |
| TEST:RUN | Esito NON ancora emesso | ❌ NO |
| TEST:PASS/FAIL | Esiste COMPACT successivo | ✅ Sì |
| CTX:PRUNE | Dopo emissione | ✅ Sì (sempre) |
| CTX:COMPACT | Più recente | ❌ NO |
| CTX:COMPACT | Precedente (non più recente) | ✅ Sì |
| CTX:UPDATE | Dopo COMPACT successivo | ✅ Sì |
| STATE:ACK | Dopo PRIMO blocco utile | ✅ Sì |
| STATE:FINDINGS | Dopo COMPACT successivo | ✅ Sì |
| ORCH:END | Mai (è terminale) | ❌ NO |

### 3.4 CTX:COMPACT

```
[CTX:COMPACT]
REQUIRED: summary:<lista>
REQUIRED: keep_active:<lista_rev>
REQUIRED: pruned_history:<range_string>
OPTIONAL: pass_count:<int>|fail_count:<int>
```
- **Obbligatorio ogni 20 messaggi**
- `summary:`: max 5 voci, formato `layer=N\|status=X\|files:[f1~rev]`
- `keep_active:`: file ancora in modifica attiva
- `pruned_history:`: range esatto es. `msg2_to_19`
- Dopo COMPACT: contatore PRUNE riparte da zero

### 3.5 CTX:FREEZE

```
[CTX:FREEZE]
REQUIRED: snapshot:<lista_rev>
REQUIRED: baseline:<int>
```
- Si emette UNA volta, quando COMPACT non basta più (~100 msg)
- `snapshot:`: tutti i file attivi con la loro revisione corrente
- `baseline:`: numero messaggio al freeze
- Dopo FREEZE: contatori PRUNE e COMPACT ripartono da zero
- La storia precedente viene archiviata (non cancellata)

---

## 4. STATE:FINDINGS / STATE:ACK

```
[STATE:FINDINGS]
REQUIRED: id:<stringa>
RECOMMENDED: cause:<stringa>|action:<stringa>|impact:<stringa>
OPTIONAL: risk:<lista>|pattern:<stringa>|components:<lista>|note:<stringa>
```
- `id:`: identificativo unico del finding (es. `s1.1`, `e2e.3`)
- `cause:`: descrizione della causa radice
- `action:`: azione correttiva intrapresa
- `impact:`: impatto misurato o stimato
- Se la grammatica non è strutturata (testo libero), il parser emette warning ma non errore

```
[STATE:ACK]
REQUIRED: protocol:h2c_v1.2
```

---

## 5. ORCH:END

```
[ORCH:END]
REQUIRED: final:<"complete"|"error"|"timeout">
OPTIONAL: est_token:<int>|fail_count:<int>|pass_count:<int>
```
- `final:`: "complete" (success), "error" (max retry), "timeout"
- `est_token:`: stima token consumati (self-reported, non normativo)

---

## 6. SKILL:PROMPT

Definizione agente specializzato. Formato invariato.

```
[SKILL:PROMPT]
id:<stringa>
role:<stringa>
attivazione:<stringa>
```

---

## 7. Regole operative (NORMATIVE)

1. **CTX:PRUNE** ogni 5 messaggi — seguire tabella §3.3
2. **CTX:COMPACT** ogni 20 messaggi — dopo COMPACT, contatore PRUNE riparte
3. **CTX:UPDATE** obbligatorio a ogni cambio layer
4. **cycle_id** obbligatorio in BUILD:FIX → TEST:FAIL → BUILD:DONE (stessa stringa)
5. **retry_n** in BUILD:FIX: 1-3. Se >3 il ciclo termina con ORCH:END final:error
6. **fail_count** è per ciclo_id: resetta quando cambia cycle_id

---

## 8. Compatibilità

- v1.0: tutti i blocchi restano validi
- v1.1: blocchi v1.1 validi; `~pruned_edges` deprecato ma ignorato
- v1.2: breaking change MINORE: `cycle_id` obbligatorio in BUILD:FIX
- Parser v1.0/v1.1: ignora cycle_id se presente, elabora il resto
