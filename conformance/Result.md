# H2C — Risultati benchmark (token reali)

H2C **non** è un formato di compressione. Le catene H2C portano stato esplicito
(id, revisioni, cycle_id, handshake) e costano più token di un brief in
linguaggio naturale. Il valore del protocollo è il parsing deterministico e
l'handoff versionato, non la dimensione.

## NL di riferimento vs fixture ufficiali

Tokenizer: tiktoken `o200k_base`. Riproduci con: `python3 conformance/benchmark.py fixtures`

| Scenario | NL (tok) | H2C (tok) | Delta |
|---|--:|--:|--:|
| Hello World | 131 | 204 | +56% |
| Calculator | 300 | 434 | +45% |
| Clean Arch | 536 | 922 | +72% |
| RAG Pipe | 800 | 1323 | +65% |

Lo scenario 5 è escluso: l'NL di riferimento descrive una migrazione a
microservizi, la fixture è uno stress test da 130 messaggi. Non sono
confrontabili.

## Risultati ritirati (2026-07-11)

I risultati pubblicati il 2026-07-11 stimavano i token con divisori fissi
(`chars ÷ 1.3` per l'NL, `chars ÷ 3.7` per H2C). L'NL reale sta a ~5 caratteri
per token, quindi quei "risparmi" del 60–83% erano un artefatto della stima.
Sono stati ritirati.
