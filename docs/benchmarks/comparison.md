# H2C Benchmark — Comparison & Methodology

**Version:** 1.0
**Status:** EXPERIMENTAL
**Scope:** Compare H2C with natural language, JSON, YAML, and MCP on structural characteristics of AI-to-AI communication. Token counts are measured, not estimated — see [conformance/Result.md](../../conformance/Result.md).

---

## 1. Methodology

### Test Setup
- **Scenarios:** Hello World (simple), Calculator CLI (medium), Clean Architecture (advanced), RAG Pipeline (complex), Stress 130 msg (extreme) — see `tests/fixtures/`
- **Token counting:** H2C and NL via tiktoken `o200k_base`. Fallback: coarse chars/token heuristic, flagged inexact, never published as a measured figure.
- **Reproducible tests:** `python3 conformance/benchmark.py fixtures`, results in [conformance/Result.md](../../conformance/Result.md)

---

## 2. Structural Comparison

| Feature | NL | JSON | YAML | MCP | H2C |
|---------|:--:|:----:|:----:|:---:|:---:|
| Formal grammar | No | JSON Schema | No | No | EBNF |
| Deterministic parsing | No | Yes | Partial (indentation-sensitive) | Yes | Yes |
| Native agent semantics (cycle_id, retry_n) | No | No | No | Partial | Yes |
| File versioning (`file~N`) | No | No | No | No | Yes |
| Fix cycles | No | No | No | No | Yes |
| Context management (PRUNE/COMPACT/FREEZE) | No | No | No | No | Yes |
| Runtime dependencies | None | JSON library | YAML library | MCP SDK | None |

Token counts per format are not included here — they vary by prompt and must be
measured, not estimated. Run `python3 conformance/benchmark.py fixtures` and see
[conformance/Result.md](../../conformance/Result.md) for the measured numbers.

---

## 3. Defined Metrics

### Tokens
Absolute count of LLM tokens consumed to transmit the same information, measured
per prompt with tiktoken `o200k_base`. No fixed ratio between formats — see
[conformance/Result.md](../../conformance/Result.md).

### Latency
Measured in round-trips; scales with token count for the specific prompt and
model. Not a property of the format alone.

### Orchestration Efficiency
Qualitative measure of the ability to express orchestration constructs natively
in the grammar (not a token-count metric):

| Construct | NL | JSON | YAML | MCP | H2C |
|-----------|:--:|:----:|:----:|:---:|:---:|
| Retry tracking | ✗ | ✗ | ✗ | ✗ | ✓ |
| File versioning | ✗ | ✗ | ✗ | ✗ | ✓ |
| DAG dependencies | Textual | Manual | Manual | Manual | ✓ |
| State machine | Textual | Manual | Manual | Manual | ✓ |
| Context pruning | ✗ | ✗ | ✗ | ✗ | ✓ |
| Fix cycle | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 4. Reproducible Tests

All benchmarks are generated from real H2C chains in `tests/fixtures/`:

```bash
python3 conformance/benchmark.py fixtures
cat conformance/Result.md
```

To reproduce on a new prompt:
1. Write the equivalent H2C chain by hand (see `SPEC.md` for the grammar)
2. Run both the NL prompt and the H2C chain through tiktoken `o200k_base`
3. Compare — do not assume a fixed ratio, measure it
