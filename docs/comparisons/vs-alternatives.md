# H2C vs Alternative

**Versione:** 1.0
**Stato:** COMPLETO
**Scopo:** Confronto strutturato tra H2C e altri formati/approcci per comunicazione AI-to-AI.

---

## 1. Linguaggio Naturale

| Dimensione | NL | H2C |
|------------|:--:|:---:|
| Token | ~5.000/ciclo | ~200/ciclo |
| Analizzabilità | Nessuna | Completa |
| Parsing automatico | Impossibile | EBNF formale |
| Versioning | Assente | rev/base_rev |
| Cicli fix | Impliciti | Espliciti (cycle_id) |
| Cross-modello | Fragile | Zero-shot |
| Overhead protocollo | 30-50% | 5-10% |

**Conclusione:** NL è il baseline — flessibile ma inadatto per automazione agente.

---

## 2. JSON / JSON Schema

| Dimensione | JSON | H2C |
|------------|:----:|:---:|
| Token (piano architetturale) | ~1.200 | ~50 |
| Schema formale | JSON Schema | EBNF |
| Tipi nativi | string, number, bool, null, array, object | string, list, revision, int |
| Semantiche agente | Nessuna | cycle_id, retry_n, PRUNE/COMPACT/FREEZE |
| Versioni file | Manuale | Nativo (file~N) |
| Supporto liste | [] | [] |
| Densità semantica | Media | Molto Alta |

**Conclusione:** JSON è più verboso (+40-60% token) e non ha semantiche agente. Utile come target di transpiler per interoperabilità.

---

## 3. YAML

| Dimensione | YAML | H2C |
|------------|:----:|:---:|
| Token | ~9.500/ciclo 3 ag | ~200/ciclo |
| Leggibilità umana | Alta | Alta |
| Parsing | Ambiguo (indentazione) | Non ambiguo (separatori \|) |
| Densità | 5 file, 20 righe per blocco | 1 riga per blocco |
| Semantiche agente | Nessuna | Native |

**Conclusione:** YAML è il più verboso tra i formati strutturati. L'indentazione complica il parsing LLM.

---

## 4. MCP (Model Context Protocol)

| Dimensione | MCP | H2C |
|------------|:---:|:---:|
| Ruolo | Trasporto | Semantica |
| Tipo | Tool call protocol | Agent communication protocol |
| Token (tool call) | ~300 | — |
| Overhead | JSON-RPC + protocollo | Zero |
| Agenti nativi | No | Sì |
| Stato | No | Sì (cycle_id, rev, findings) |
| Gestione contesto | No | Sì (PRUNE/COMPACT/FREEZE) |

**Conclusione:** MCP e H2C sono **complementari**. MCP definisce come trasportare, H2C definisce cosa trasportare.

---

## 5. Tabella Riepilogativa

| Feature | NL | JSON | YAML | MCP | H2C |
|---------|:--:|:----:|:----:|:---:|:---:|
| Zero dipendenze | ✓ | ~ | ~ | ✗ | ✓ |
| LLM-native | ✓ | ✗ | ✗ | ✗ | ✓ |
| Token efficiente | ✗ | ✗ | ✗ | ✗ | ✓ |
| Parsing formale | ✗ | ✓ | ✓ | ✓ | ✓ |
| Semantiche agente | ✗ | ✗ | ✗ | ~ | ✓ |
| Gestione contesto | ✗ | ✗ | ✗ | ✗ | ✓ |
| Retrocompatibilità | N/A | N/A | N/A | Per versione | ✓ |
| Ecosistema maturo | N/A | ✓ | ✓ | ✓ | ✗ |
| Implementazione ref | N/A | ✓ | ✓ | ✓ | ✗ |

---

## 6. Quando Usare Cosa

| Scenario | Scegli |
|----------|--------|
| Prompt umano singolo | NL |
| Archiviazione dati strutturati | JSON |
| Configurazione leggibile | YAML |
| Tool call standardizzato | MCP |
| Comunicazione AI-to-AI efficiente | H2C |
| Interoperabilità con sistemi esistenti | H2C → JSON (transpiler) |
| Produzione con MCP | H2C + MCP |
| Debug e audit | H2C + NL commenti |
