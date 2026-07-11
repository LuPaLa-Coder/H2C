# H2C v1.4 — Benchmark Results

Benchmark eseguito incollando `conformance/benchmark_prompt.md` in 4 LLM diversi.
Data: 2026-07-11. Metodo: caratteri, parole, token stimati (chars÷3.7 H2C, chars÷1.3 NL).

## Risultati per modello

=== H2C v1.4 Deterministic Benchmark ===
Date: 2026-07-11
Model: claude-haiku-4.5

| # | Scenario    | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |
|---|-------------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|
| 1 | Hello World |       471 |      681 |     31% |        20 |      122 |     84% |         127 |        524 |       76% |
| 2 | Calculator  |      1067 |     1447 |     26% |        44 |      258 |     83% |         288 |       1113 |       74% |
| 3 | Clean Arch  |      2191 |     2914 |     25% |        71 |      520 |     86% |         592 |       2242 |       74% |
| 4 | RAG Pipe    |      3038 |     4013 |     24% |       104 |      717 |     85% |         821 |       3087 |       73% |
| 5 | Stress      |      9323 |     3941 |   -137% |       267 |      704 |     62% |        2520 |       3032 |       17% |

TOTAL: H2C chars=16090 | NL chars=12996 | Avg token save=57%

v1.4 Features:
  CTX:NEGOTIATE [✓]  STATE:ACK [✓]  BUILD:NACK [✓]  STATE:FINDINGS [✓]
  CTX:PRUNE     [✓]  CTX:COMPACT [✓]  CTX:FREEZE [✓]  Fix cycle [✓]
  DAG closure   [✓]

Message Counts: 1=8 | 2=13 | 3=27 | 4=32 | 5=103 msg



=== H2C v1.4 Deterministic Benchmark ===
Date: 2026-07-11
Model: Kimi K2.6

| # | Scenario    | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |
|---|-------------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|
| 1 | Hello World | 466       | 681      | 31.6%   | 21        | 110      | 80.9%   | 125.9       | 523.8      | 76.0%    |
| 2 | Calculator  | 952       | 1447     | 34.2%   | 32        | 227      | 85.9%   | 257.3       | 1113.1     | 76.9%    |
| 3 | Clean Arch  | 1850      | 2914     | 36.5%   | 52        | 409      | 87.3%   | 500.0       | 2241.5     | 77.7%    |
| 4 | RAG Pipe    | 2478      | 4013     | 38.3%   | 70        | 584      | 88.0%   | 669.7       | 3086.9     | 78.3%    |
| 5 | Stress      | 6871      | 3941     | -74.3%  | 220       | 563      | 60.9%   | 1857.0      | 3031.5     | 38.7%    |

TOTAL: H2C chars=12617 | NL chars=12996 | Avg char save=2.9% | Avg token save=65.9%

v1.4 Features:
  CTX:NEGOTIATE [X]  STATE:ACK [X]  BUILD:NACK [X]  STATE:FINDINGS [X]
  CTX:PRUNE     [X]  CTX:COMPACT [X]  CTX:FREEZE [X]  Fix cycle [X]
  DAG closure   [X]


  