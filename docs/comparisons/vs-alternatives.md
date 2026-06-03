# H2C vs Alternatives

**Version:** 1.0
**Status:** COMPLETE
**Purpose:** Structured comparison between H2C and other formats/approaches for AI-to-AI communication.

---

## 1. Natural Language

| Dimension | NL | H2C |
|-----------|:---:|:---:|
| Tokens | ~5,000/cycle | ~200/cycle |
| Analyzability | None | Complete |
| Automatic parsing | Impossible | Formal EBNF |
| Versioning | Absent | rev/base_rev |
| Fix cycles | Implicit | Explicit (cycle_id) |
| Cross-model | Fragile | Zero-shot |
| Protocol overhead | 30-50% | 5-10% |

**Conclusion:** NL is the baseline — flexible but unsuitable for agent automation.

---

## 2. JSON / JSON Schema

| Dimension | JSON | H2C |
|-----------|:----:|:---:|
| Tokens (architectural plan) | ~1,200 | ~50 |
| Formal schema | JSON Schema | EBNF |
| Native types | string, number, bool, null, array, object | string, list, revision, int |
| Agent semantics | None | cycle_id, retry_n, PRUNE/COMPACT/FREEZE |
| File versioning | Manual | Native (file~N) |
| List support | [] | [] |
| Semantic density | Medium | Very High |

**Conclusion:** JSON is more verbose (+40-60% tokens) and lacks agent semantics. Useful as transpiler target for interoperability.

---

## 3. YAML

| Dimension | YAML | H2C |
|-----------|:----:|:---:|
| Tokens | ~9,500/3-agent cycle | ~200/cycle |
| Human readability | High | High |
| Parsing | Ambiguous (indentation) | Unambiguous (| separators) |
| Density | 5 files, 20 lines per block | 1 line per block |
| Agent semantics | None | Native |

**Conclusion:** YAML is the most verbose among structured formats. Indentation complicates LLM parsing.

---

## 4. MCP (Model Context Protocol)

| Dimension | MCP | H2C |
|-----------|:---:|:---:|
| Purpose | Tool invocation | Agent communication |
| Layer | Transport | Semantic |
| Token overhead | ~300/call | ~15/block |
| State machine | None | Built-in |
| Context management | None | PRUNE/COMPACT/FREEZE |
| Fix cycles | External logic | Native (cycle_id, retry_n) |
| Relationship | — | H2C blocks can be transported via MCP |

**Conclusion:** MCP and H2C are complementary. MCP transports; H2C communicates. They work best together.

---

## 5. Summary Table

| Feature | NL | JSON | YAML | MCP | H2C |
|---------|:--:|:----:|:----:|:---:|:---:|
| Token efficiency | ✗ | ✗ | ✗ | ✗ | ✓ |
| Formal grammar | ✗ | JSON Schema | ✗ | ✗ | EBNF |
| Agent semantics | ✗ | ✗ | ✗ | ✗ | ✓ |
| Context pruning | ✗ | ✗ | ✗ | ✗ | ✓ |
| File versioning | ✗ | ✗ | ✗ | ✗ | ✓ |
| Fix cycles (retry) | ✗ | ✗ | ✗ | ✗ | ✓ |
| LLM zero-shot | ✓ | ✓ | ✓ | ✓ | ✓ |
| Human readable | ✓ | ✗ | ✓ | ✗ | ✓ |

---

## 6. When to Use What

| If you need... | Use... |
|----------------|--------|
| Human-agent communication | NL (input) → H2C (protocol) |
| API integration | JSON (via transpiler) |
| Configuration files | YAML |
| Tool invocation | MCP (transport) + H2C (payload) |
| Agent-to-agent chain | **H2C** (native) |
