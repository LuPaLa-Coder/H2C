# H2C Protocol Documentation

Index of technical documentation for the H2C Semantic Compression protocol.

---

## Structure

```
docs/
├── README.md                  # This file
├── specification/
│   ├── grammar.md             # Formal EBNF grammar
│   ├── blocks.md              # Block reference
│   └── semantics.md           # Operational semantics
├── architecture/
│   ├── overview.md            # Architectural overview
│   ├── agent-runtime.md       # Agent runtime model
│   └── context-lifecycle.md   # Context lifecycle (PRUNE/COMPACT/FREEZE)
├── examples/
│   └── (examples in examples/ root)
├── benchmarks/
│   └── comparison.md          # Comparative tables + methodology
├── comparisons/
│   └── vs-alternatives.md     # Comparison with NL, JSON, YAML, MCP
├── ecosystem/
│   └── integrations.md        # Framework integration models
├── semantic-ir/
│   └── model.md               # Semantic IR model
├── parser/
│   ├── architecture.md        # Reference parser architecture
│   └── schema.md              # Typed JSON schema for validation
├── compiler/
│   └── pipeline.md            # Compiler/transpiler pipeline
├── agent-runtime/
│   └── protocol.md            # Agent runtime specification
├── risks/
│   └── analysis.md            # SWOT risk analysis
└── (CONTRIBUTING.md in root/)  # Contribution guidelines
```

---

## Recommended Reading Paths

| If you are... | Read... |
|--------------|---------|
| New to the protocol | `../README.md` → `../SPEC.md` → `docs/specification/grammar.md` |
| Framework developer | `docs/ecosystem/integrations.md` → `docs/architecture/overview.md` |
| Researcher | `docs/specification/semantics.md` → `docs/benchmarks/comparison.md` |
| OSS contributor | `docs/parser/architecture.md` → `docs/parser/schema.md` → `docs/specification/blocks.md` |
| Parser implementor | `docs/parser/architecture.md` → `docs/parser/schema.md` → `docs/compiler/pipeline.md` |
| Enterprise architect | `docs/comparisons/vs-alternatives.md` → `docs/architecture/overview.md` |
