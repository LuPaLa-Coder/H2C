# H2C Protocol — Repository Analysis Report

**Status:** COMPLETED
**Date:** 2026-05-26
**Scope:** Structural, semantic, and positioning audit

---

## 1. Executive Summary

H2C is a compressed block grammar protocol for AI-to-AI communication between agents. It achieves 75–93% token reduction compared to natural language while preserving semantic equivalence. The protocol has been validated on multiple models (Claude Sonnet 4.6, Opus 4.7) with chains up to 130 messages.

The repository has solid technical foundations but suffers from five critical issues that compromise discoverability, credibility, and adoption.

---

## 2. Issues Found

### 2.1 Naming Ambiguity — CRITICAL

| Issue | Detail |
|-------|--------|
| **HTTP/2 conflict** | `h2c` is the cleartext upgrade mechanism for HTTP/2 (RFC 7540 §3.1, `Upgrade: h2c`). Every search for "h2c protocol" returns HTTP/2 results. |
| **Acronym overload** | H2C = "Human-to-Compressed" is semantically weak. The real value is AI-to-AI, not human-to-anything. "Compressed" suggests lossy compression. |
| **Brand collision** | `h2c` appears in npm packages, Go libraries, and HTTP/2 middleware. SEO is effectively zero for this name. |
| **Discoverability** | Google/Bing/GitHub searches for "h2c" do not return results for this project in the first 10 pages. |

### 2.2 SEO Weakness — CRITICAL

| Gap | Impact |
|-----|--------|
| No keyword or description in any document | Zero semantic signal for search engines |
| Title "h2c Protocol" collides with HTTP/2 | All traffic goes to HTTP/2 documentation |
| No structured data (JSON-LD) | No rich snippets |
| No GitHub topics beyond "protocol" | No discovery on GitHub |
| No `llms.txt` or `llms-full.txt` | LLM retrieval systems cannot index the protocol |

### 2.3 Low LLM Retrievability — CRITICAL

| Gap | Impact |
|-----|--------|
| Missing keywords: `semantic compression`, `AI-to-AI`, `agent orchestration`, `reasoning transport` | LLMs cannot associate H2C with these concepts |
| README framed as "prompt compression" | Trivializes the protocol; LLMs categorize it as a low-value hack |
| No semantic IR model | No context for retrieval systems |
| No `llms.txt` | Cursor, Copilot, ChatGPT, Claude have no indexed context |

### 2.4 Structural Inconsistency — HIGH

| Issue | Detail |
|-------|--------|
| Mixed Italian/English documentation | README and SPEC in Italian; examples with English comments. No monolingual strategy. |
| Old skill files still present (`h2c_v3.md`, `orch_v1.md`, `build.md`, `test.md`) | Clutters directory, confuses new readers |
| `Test-Sonnet4.6.md` in root vs `archive/` | Root file duplicates archived content |
| No `docs/` directory | Everything flat in root — no hierarchy |
| No `examples/` organization | Everything in a flat folder |
| `h2c_compress/SKILL.md` in root | Skill mixed with root repo, not in skills/ |
| No `index.md` or entry point | New users have no navigation path |
| No `CONTRIBUTING.md` | No contribution guidelines |
| No `ARCHITECTURE.md` | No architectural overview |

### 2.5 Architectural Uncertainty — HIGH

| Issue | Detail |
|-------|--------|
| README calls it "protocol" but SPEC calls it "grammar" | Identity confusion |
| No AST or formal semantic model | Grammar defined in BNF but no parse tree or semantics |
| No reference parser implementation | No validator, no transpiler, no compiler |
| No interoperability specification (vs MCP, JSON-RPC, etc.) | Unclear how H2C relates to existing standards |
| No formal opcode model | Block types are listed but no formal opcode semantics |
| No transport binding specification | How does H2C travel? stdin/stdout? HTTP? WebSocket? |

---

## 3. Scores

| Dimension | Score (1–10) | Severity |
|-----------|:---:|:--------:|
| Code quality | 7 | — |
| Protocol design | 8 | — |
| Documentation | 4 | HIGH |
| SEO / Discoverability | 1 | CRITICAL |
| LLM Retrievability | 1 | CRITICAL |
| Structural organization | 3 | HIGH |
| Naming / Branding | 1 | CRITICAL |
| Ecosystem positioning | 2 | HIGH |
| Formal rigor | 5 | MEDIUM |
| Adoption readiness | 3 | HIGH |

---

## 4. Remediation Recommendations

| Priority | Action | Task |
|:--------:|--------|:----:|
| P0 | Reposition as "Semantic Compression Protocol for AI-to-AI Communication" | Task 8 |
| P0 | Disambiguate from HTTP/2 h2c in every document | Task 2, 8 |
| P0 | Add structured data (JSON-LD), keywords, GitHub topics, `llms.txt` | Task 3 |
| P0 | Create `docs/` hierarchy with specification, architecture, examples | Task 4 |
| P1 | Define formal EBNF grammar, AST model, opcode semantics | Task 5 |
| P1 | Remove old/duplicate files, reorganize examples, archive deprecated content | Task 4 |
| P1 | Create benchmark methodology + comparison tables | Task 6 |
| P1 | Define MCP integration model (H2C = semantic layer, MCP = transport layer) | Task 7 |
| P2 | Produce content strategy (blog posts, talks, paper) | Task 9 |
| P2 | Formal risk analysis with adoption barriers | Task 10 |
