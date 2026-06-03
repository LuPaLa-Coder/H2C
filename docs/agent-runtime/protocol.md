# H2C Agent Runtime Specification

**Version:** 1.0
**Status:** DRAFT
**Scope:** Define the runtime model for executing H2C chains between AI agents.

---

## 1. Runtime Model

```
┌──────────────────────────────────────────────┐
│             H2C Agent Runtime                │
│                                              │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Parser   │──→│ State    │──→│ Dispatcher│ │
│  │ (EBNF)   │   │ Machine  │   │ (Router)  │ │
│  └──────────┘   └──────────┘   └───────────┘ │
│       │              │               │       │
│       ▼              ▼               ▼       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │Validator │   │Context   │   │Skills    │  │
│  │(Rules)   │   │Manager   │   │Loader    │  │
│  └──────────┘   └──────────┘   └──────────┘  │
└──────────────────────────────────────────────┘
```

---

## 2. Components

### Parser
- Input: H2C text
- Output: AST (Abstract Syntax Tree)
- Validation: EBNF grammar + constraints
- Errors: malformed block → discarded + log

### State Machine
- Input: AST
- Output: new state transition
- Table: see [docs/specification/semantics.md](../specification/semantics.md)

### Dispatcher
- Input: AST + current state
- Output: routing to correct skill/agent
- Logic: type/subtype → handler

### Context Manager
- Maintains: msg_counter, cycle_registry, revision_table
- Triggers: PRUNE every 5, COMPACT every 20, FREEZE ~100
- Reset: after COMPACT and FREEZE

### Validator
- Rules: operational constraints (retry_n ≤ 3, cycle_id match, ...)
- Output: valid/invalid block + warning

---

## 3. Future Architecture: H2C Compiler

```
H2C Source Code
      │
      ▼
┌─────────────┐
│   Parser    │  AST
└──────┬──────┘
       ▼
┌─────────────┐
│   Analyzer  │  Type checking, semantic analysis
└──────┬──────┘
       ▼
┌─────────────┐
│   Optimizer │  Block fusion, compression
└──────┬──────┘
       ▼
┌─────────────┐
│   Codegen   │  Target: JSON, MCP, gRPC, custom
└─────────────┘
```

### Transpiler Targets
- JSON → interoperability with existing systems
- MCP → native transport over Model Context Protocol
- gRPC → high performance for agent runtimes
- NL → debug, logging, human-readable audit trail

---

## 4. Transport Bindings

| Binding | Medium | Use Case |
|---------|--------|----------|
| stdin/stdout | UNIX pipe | Local agents, CLI |
| HTTP POST | REST | API gateway, microservices |
| WebSocket | Bidirectional | Streaming, long-lived |
| MCP | Tool call | Framework agnostic |
| File system | .h2c file | Batch, debug, replay |
