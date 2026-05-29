# Documentazione H2C Protocol

Indice della documentazione tecnica del protocollo H2C Semantic Compression.

---

## Struttura

```
docs/
├── README.md                  # Questo file
├── specification/
│   ├── grammar.md             # Grammatica EBNF formale
│   ├── blocks.md              # Riferimento blocchi
│   └── semantics.md           # Semantica operazionale
├── architecture/
│   ├── overview.md            # Panoramica architetturale
│   ├── agent-runtime.md       # Modello runtime agenti
│   └── context-lifecycle.md   # Ciclo vita contesto (PRUNE/COMPACT/FREEZE)
├── examples/
│   ├── basic/                 # Esempi base
│   ├── advanced/              # Esempi avanzati
│   └── integrations/          # Esempi con framework
├── benchmarks/
│   └── comparison.md          # Tabelle comparative + metodologia
├── comparisons/
│   └── vs-alternatives.md     # Confronto con NL, JSON, YAML, MCP
├── ecosystem/
│   └── integrations.md        # Modelli integrazione framework
├── semantic-ir/
│   └── model.md               # Modello IR semantico
├── parser/
│   ├── architecture.md        # Architettura parser di riferimento
│   └── schema.md              # Schema tipizzato JSON per validazione
├── compiler/
│   └── pipeline.md            # Pipeline compilatore/transpiler H2C
├── agent-runtime/
│   └── protocol.md            # Specifica runtime agenti
├── risks/
│   └── analysis.md            # Analisi rischi SWOT
└── CONTRIBUTING.md            # Linee guida contributi
```

---

## Percorsi di Lettura Consigliati

| Se sei... | Leggi... |
|-----------|----------|
| Nuovo al protocollo | `../README.md` → `../SPEC.md` → `docs/specification/grammar.md` |
| Sviluppatore framework agenti | `docs/ecosystem/integrations.md` → `docs/architecture/overview.md` |
| Ricercatore | `docs/specification/semantics.md` → `docs/benchmarks/comparison.md` |
| Contributore OSS | `docs/parser/architecture.md` → `docs/parser/schema.md` → `docs/specification/blocks.md` |
| Implementatore parser | `docs/parser/architecture.md` → `docs/parser/schema.md` → `docs/compiler/pipeline.md` |
| Architetto enterprise | `docs/positioning/README.md` → `docs/architecture/overview.md` |
