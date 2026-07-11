# H2C v1.4 — Benchmark Results

Benchmark eseguito incollando `conformance/benchmark_prompt.md` in 4 LLM diversi.
Data: 2026-07-11. Metodo: caratteri, parole, token stimati (chars÷3.7 H2C, chars÷1.3 NL).

## Risultati per modello

### Claude Sonnet 5
| Scenario | H2C tok | NL tok | Tok save |
|----------|---------|--------|----------|
| Hello World | 125 | 440 | 72% |
| Calculator | 202 | 580 | 65% |
| Clean Arch | 360 | 1.023 | 65% |
| RAG Pipeline | 444 | 1.172 | 62% |
| Stress (130) | 1.465 | 1.725 | 15% |
| **TOTALE** | **2.596** | **4.941** | **47%** |

### GPT-5.5-mini
| Scenario | H2C tok | NL tok | Tok save |
|----------|---------|--------|----------|
| Hello World | 142 | 651 | 78% |
| Calculator | 214 | 998 | 79% |
| Clean Arch | 509 | 2.417 | 79% |
| RAG Pipeline | 424 | 2.080 | 80% |
| Stress (130) | 1.348 | 6.708 | 80% |
| **TOTALE** | **2.637** | **12.854** | **79%** |

### Kimi K2.6
| Scenario | H2C tok | NL tok | Tok save |
|----------|---------|--------|----------|
| Hello World | 126 | 524 | 76% |
| Calculator | 257 | 1.113 | 77% |
| Clean Arch | 500 | 2.242 | 78% |
| RAG Pipeline | 670 | 3.087 | 78% |
| Stress (130) | 1.858 | 3.032 | 39% |
| **TOTALE** | **3.411** | **9.997** | **66%** |

### Grok
| Scenario | H2C tok | NL tok | Tok save |
|----------|---------|--------|----------|
| Hello World | 129 | 240 | 46% |
| Calculator | 165 | 219 | 25% |
| Clean Arch | 251 | 368 | 32% |
| RAG Pipeline | 285 | 324 | 12% |
| Stress (130) | 580 | 394 | -47% |
| **TOTALE** | **1.410** | **1.545** | **9%** |

## Riepilogo

| Modello | Token H2C | Token NL | Risparmio | Stress test |
|---------|-----------|----------|-----------|-------------|
| GPT-5.5-mini | 2.637 | 12.854 | **79%** | ✅ 80% |
| Kimi K2.6 | 3.411 | 9.997 | **66%** | ✅ 39% |
| Claude Sonnet 5 | 2.596 | 4.941 | **47%** | ⚠️ 15% |
| Grok | 1.410 | 1.545 | **9%** | ❌ -47% |

## Osservazioni

- **GPT-5.5-mini**: miglior risultato, risparmio costante ~79% su tutti gli scenari. Catene H2C ben formate.
- **Kimi K2.6**: buon risultato (66%), eccetto lo stress test dove l'NL reference è più denso dell'H2C.
- **Claude Sonnet 5**: discreto sui test semplici (65-72%), ma sullo stress test l'H2C è quasi uguale all'NL — il modello ha generato catene più verbose.
- **Grok**: ha interpretato il prompt diversamente, generando catene H2C molto corte e NL reference più corti del previsto. Lo stress test è andato in negativo.

## v1.4 Features (tutti i modelli)

- [x] CTX:NEGOTIATE handshake
- [x] STATE:ACK response
- [x] BUILD:NACK error recovery
- [x] STATE:FINDINGS formal fields
- [x] CTX:PRUNE / COMPACT / FREEZE
- [x] DAG transitive closure
- [x] Fix cycle con cycle_id + retry_n

## Conclusione

Il benchmark è **parzialmente deterministico**: i modelli che seguono fedelmente le istruzioni producono risultati confrontabili (GPT-5.5, Kimi, Claude). Modelli meno instruction-following (Grok) divergono. L'NL reference fissato funziona come àncora, ma la qualità della catena H2C generata dipende dal modello.

---

*Prompt utilizzato:* `conformance/benchmark_prompt.md`
*Validazione:* `python3 conformance/run.py` sulle fixture ufficiali → 5/5 PASS
