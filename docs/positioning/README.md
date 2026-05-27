# Protocollo H2C — Posizionamento

**Versione:** 1.0
**Stato:** DEFINITIVO
**Scopo:** Definire cosa H2C è, cosa NON è, e dove si colloca nell'ecosistema agenti.

---

## Identità di Prodotto

H2C è **quattro cose simultaneamente**, a seconda del livello di astrazione:

| Frame | Definizione | Astrazione |
|-------|------------|:----------:|
| **Protocollo Semantico** | Formato wire per comunicazione lossless compressa tra agenti AI | Più alto |
| **Formato IR Cognitivo** | Rappresentazione strutturata di ragionamento intermedio, recuperabile e riutilizzabile | Alto |
| **Linguaggio Orchestrazione Agenti** | DSL per esprimere workflow multi-agente, politiche retry e transizioni di stato | Medio |
| **Layer Trasporto Ragionamento** | Formato carrier per catene di pensiero compresse tra chiamate LLM | Medio |

---

## Cosa H2C È

- Una **grammatica a blocchi** con campi tipizzati, liste e tracciamento revisioni
- Un **sistema di ciclo di vita contesto** (PRUNE ogni 5, COMPACT ogni 20, FREEZE a ~100)
- Un **protocollo di ciclo fix** con `cycle_id`, `retry_n`, `fail_count`, `pass_count`
- Un **formato di gestione stato** per conversazioni agente (`STATE:FINDINGS`, `CTX:UPDATE`)
- Un **formato wire cross-modello** testato su Claude Sonnet 4.6, Opus 4.7 e altri — zero-shot, nessun preambolo
- Una **specifica versionata** con garanzie di retrocompatibilità (v1.0 → v1.2)

---

## Cosa H2C NON È

| Errore | Correzione |
|--------|------------|
| **Un hack di prompt** | H2C è un protocollo strutturato con grammatica formale, versioning e regole di ciclo di vita. L'hacking di prompt è destrutturato. |
| **Un trucco di compressione** | La riduzione token è una *proprietà* del protocollo, non l'obiettivo. L'obiettivo è un formato di comunicazione agenti analizzabile, stateful e cross-modello. |
| **Un'alternativa a JSON** | JSON è un formato di serializzazione dati. H2C è un *protocollo agenti* con semantica, stato, gestione contesto e regole di orchestrazione. |
| **Una cosa HTTP/2** | HTTP/2 h2c è un meccanismo di upgrade in chiaro (RFC 7540). H2C qui non è correlato. |
| **Un linguaggio di programmazione** | H2C non è Turing-completo. È un formato wire per messaggi agente. |
| **Un framework** | H2C non fornisce runtime, SDK o libreria. È un protocollo testuale che qualsiasi LLM può analizzare nativamente. |
| **Un rimpiazzo di MCP** | MCP è trasporto. H2C è semantica. Sono complementari. |

---

## Audience

| Segmento | Ruolo | Perché H2C è Rilevante |
|----------|-------|------------------------|
| **Sviluppatori framework agenti** | Ingegneri che costruiscono integrazioni LangGraph, AutoGen, CrewAI, Semantic Kernel | Formato wire standard riduce l'accoppiamento framework |
| **Ricercatori AI** | Sistemi multi-agente, efficienza comunicazione, ottimizzazione context window | Risparmio token empirico (75-93%), grammatica formale |
| **Ingegneri runtime LLM** | Inference serving, gestione contesto, hosting agenti | PRUNE/COMPACT/FREEZE come lifecycle algoritmico |
| **Contributori OSS** | Protocollo, compilatore, ecosistema strumenti | Licenza MIT, design modulare, specifica formale |
| **Architetti enterprise** | Orchestrazione agenti, ottimizzazione costi, auditabilità | Comunicazione tracciabile, analizzabile, versionata |
| **Prompt engineer** | Workflow agente multi-step | Output strutturato significa parsing strutturato |

---

## Keyword (SEO / Retrieval LLM)

Usare coerentemente in tutta la documentazione:

```
protocollo comunicazione AI-to-AI
compressione semantica per agenti LLM
formato orchestrazione multi-agente
protocollo IR cognitivo
layer trasporto ragionamento
formato wire agenti
comunicazione strutturata LLM-to-LLM
protocollo agenti autonomi
grammatica a blocchi per agenti
comunicazione agenti token-efficiente
```

---

## Panorama Competitivo

| Approccio | Punto di Forza | Debolezza |
|-----------|----------------|-----------|
| **Linguaggio Naturale** | Flessibile, universale | Verboso, non analizzabile, modello-dipendente |
| **JSON / JSON-RPC** | Schema rigoroso, ampio supporto | Token-pesante, nessuna semantica agente |
| **YAML** | Leggibile da umani | Più grande di JSON, parsing ambiguo |
| **XML** | Supporto namespace | Estremamente verboso |
| **MCP** | Trasporto standardizzato | Non è un formato semantico |
| **H2C** | Semplice, compatto, analizzabile, cross-modello | Ecosistema giovane, nessuna implementazione di riferimento |

H2C occupa lo spazio tra "troppo verboso" (NL, JSON, YAML, XML) e "troppo focalizzato su trasporto" (MCP). Fornisce il **layer semantico** mancante per la comunicazione tra agenti.

---

## Elevator Pitch

| Contesto | Frase |
|----------|-------|
| **Tecnico** | H2C è un formato wire a grammatica blocchi per comunicazione compressa lossless tra agenti AI, con riduzione token del 75-93% mantenendo parsing nativo da qualsiasi LLM. |
| **Prodotto** | Un modo standard per agenti AI di parlarsi senza sprecare token in cortesie, markdown e ripetizioni. |
| **Ricerca** | Un protocollo formale per comunicazione strutturata multi-agente con modello di lifecycle contesto dimostrabile (PRUNE/COMPACT/FREEZE) e validazione empirica fino a 130 messaggi. |
| **Ecosistema** | Il layer semantico che MCP trasporta — complementare, non competitivo. |
