# Grammatica H2C — Specifica EBNF Formale

**Versione:** 1.2
**Stato:** FORMALE
**Scopo:** Definire la grammatica EBNF completa del protocollo H2C per parser, validatori e transpiler.

---

## 1. Grammatica EBNF Completa

```ebnf
(* === H2C Protocol v1.2 Formal Grammar === *)

(* --- Top-Level --- *)
message          = block;
block            = "[" type ":" subtype "]" newline fields;
newline          = ? ASCII 0x0A ?;

(* --- Type & Subtype --- *)
type             = "ARCH" | "BUILD" | "TEST" | "CTX" | "STATE" | "ORCH" | "SKILL";
subtype          = arch_subtype | build_subtype | test_subtype 
                 | ctx_subtype | state_subtype | orch_subtype | skill_subtype;

arch_subtype     = "PLAN";
build_subtype    = "EXEC" | "DONE" | "FIX" | "REVERT";
test_subtype     = "RUN" | "PASS" | "FAIL";
ctx_subtype      = "PRIMITIVES" | "UPDATE" | "PRUNE" | "COMPACT" | "FREEZE";
state_subtype    = "FINDINGS" | "ACK";
orch_subtype     = "END";
skill_subtype    = "PROMPT";

(* --- Fields --- *)
fields           = field ( "|" field )*;
field            = key ":" value;
key              = letter ( letter | digit | "_" )*;
value            = string | list | revision | integer;

(* --- Primitives --- *)
string           = ? characters except "|", "\n", "[", "]" ?;
list             = "[" string ( "," string )* "]";
revision         = string "~" integer;
integer          = digit+;

letter           = "A" | ... | "Z" | "a" | ... | "z";
digit            = "0" | ... | "9";

(* --- Context Prefix Fields --- *)
ctx_field        = "~" key ":" value;  (* fields in CTX:* blocks *)
```

---

## 2. Schema dei Blocchi (Tipo × Sottotipo × Campi)

### 2.1 ARCH:PLAN

```
[ARCH:PLAN]
id:<string>             REQUIRED
fw:<string>             REQUIRED
lib:<string>            OPTIONAL  (lista separata da virgole)
auth:<string>           OPTIONAL
pattern:<string>        OPTIONAL
tools:<list>            OPTIONAL
struct:<list>           OPTIONAL
deps:<string>           OPTIONAL
notes:<list>            OPTIONAL
```

### 2.2 BUILD:EXEC

```
[BUILD:EXEC]
id:<string>             REQUIRED
target:<string>         REQUIRED
after:<list>            OPTIONAL  (DAG dipendenze)
desc:<string>           OPTIONAL
cmd:<string>            OPTIONAL
```

### 2.3 BUILD:DONE

```
[BUILD:DONE]
id:<string>             REQUIRED
diff:<list_rev>         REQUIRED   (formato: [file~N,+M,file~N,-K])
rev:<integer>           OPTIONAL   (default: 1)
notes:<list>            OPTIONAL
cycle_id:<string>       OPTIONAL   (REQUIRED se generato da FIX)
```

### 2.4 BUILD:FIX

```
[BUILD:FIX]
id:<string>             REQUIRED
target:<string>         REQUIRED
base_rev:<integer>      REQUIRED
desc:<string>           REQUIRED
cycle_id:<string>       REQUIRED
retry_n:<integer>       OPTIONAL   (range: 1-3)
cmd:<string>            OPTIONAL
```

### 2.5 BUILD:REVERT

```
[BUILD:REVERT]
id:<string>             REQUIRED
target:<string>         REQUIRED
to_rev:<integer>        REQUIRED
```

### 2.6 TEST:RUN / TEST:PASS / TEST:FAIL

```
[TEST:RUN]
id:<string>             REQUIRED
cmd:<string>            REQUIRED

[TEST:PASS]
id:<string>             REQUIRED
cycle_id:<string>       REQUIRED se chiude ciclo fix
pass_count:<integer>    OPTIONAL

[TEST:FAIL]
id:<string>             REQUIRED
error:<string>          REQUIRED
cycle_id:<string>       REQUIRED
fail_count:<integer>    OPTIONAL
pass_count:<integer>    OPTIONAL
```

### 2.7 CTX:PRIMITIVES

```
[CTX:PRIMITIVES]
~task:<string>          REQUIRED
~constraint:<string>    REQUIRED
~goal:<string>          REQUIRED
~form:<string>          OPTIONAL
```

### 2.8 CTX:UPDATE

```
[CTX:UPDATE]
~progress:<string>      REQUIRED   (formato: layer=N|status=X)
~next:<string>          REQUIRED
~active_files:<list>    OPTIONAL   (formato: [file~rev,...])
```

### 2.9 CTX:PRUNE

```
[CTX:PRUNE]
keep:<string_or_list>   REQUIRED   ("last_N" | [id,...])
pruned:<list>           REQUIRED
reason:<string>         OPTIONAL
```

### 2.10 CTX:COMPACT

```
[CTX:COMPACT]
summary:<list>          REQUIRED   (max 5 voci)
keep_active:<list_rev>  REQUIRED
pruned_history:<string> REQUIRED   (formato: "msgN_to_M")
pass_count:<integer>    OPTIONAL
fail_count:<integer>    OPTIONAL
```

### 2.11 CTX:FREEZE

```
[CTX:FREEZE]
snapshot:<list_rev>     REQUIRED
baseline:<integer>      REQUIRED
```

### 2.12 STATE:FINDINGS / STATE:ACK

```
[STATE:FINDINGS]
id:<string>             REQUIRED
cause:<string>          RECOMMENDED
action:<string>         RECOMMENDED
impact:<string>         RECOMMENDED
risk:<list>             OPTIONAL
pattern:<string>        OPTIONAL
components:<list>       OPTIONAL
note:<string>           OPTIONAL

[STATE:ACK]
protocol:h2c_v1.2       REQUIRED
```

### 2.13 ORCH:END

```
[ORCH:END]
final:<enum>            REQUIRED   ( "complete" | "error" | "timeout" )
est_token:<integer>     OPTIONAL
fail_count:<integer>    OPTIONAL
pass_count:<integer>    OPTIONAL
```

### 2.14 SKILL:PROMPT

```
[SKILL:PROMPT]
id:<string>             REQUIRED
role:<string>           REQUIRED
attivazione:<string>    REQUIRED
```

---

## 3. Modello AST

```
Message
  └── Block
       ├── Type        (ARCH|BUILD|TEST|CTX|STATE|ORCH|SKILL)
       ├── Subtype     (PLAN|EXEC|DONE|FIX|REVERT|RUN|PASS|FAIL|...)
       └── Fields[]
            ├── Key    (string)
            └── Value  (String | List | Revision | Integer)

StringValue   → string
ListValue     → StringValue[]
RevisionValue → { file: StringValue, rev: IntegerValue }
IntegerValue  → integer
```

---

## 4. Vincoli di Parsing

```
VINCOLO-1:  Zero testo fuori dai campi (violazione = blocco scartato)
VINCOLO-2:  Liste inline max 5 elementi
VINCOLO-3:  Campi REQUIRED devono essere presenti o blocco invalido
VINCOLO-4:  Ordine campi irrilevante per parsing
VINCOLO-5:  Campi CTX:* usano prefisso ~ per distinzione
VINCOLO-6:  retry_n range [1..3]; >3 = ORCH:END final:error
VINCOLO-7:  cycle_id stessa stringa in FIX → FAIL → DONE → PASS
VINCOLO-8:  fail_count resetta quando cambia cycle_id
```

---

## 5. Esempio di Parsing

Input:
```
[ARCH:PLAN]
id:api-meteo|fw:python3.11|lib:fastapi,httpx|notes:[cache_TTL_10min]
```

AST risultante:
```json
{
  "type": "ARCH",
  "subtype": "PLAN",
  "fields": [
    {"key": "id",    "value": {"type": "string",  "data": "api-meteo"}},
    {"key": "fw",    "value": {"type": "string",  "data": "python3.11"}},
    {"key": "lib",   "value": {"type": "string",  "data": "fastapi,httpx"}},
    {"key": "notes", "value": {"type": "list",    "data": ["cache_TTL_10min"]}}
  ]
}
```
