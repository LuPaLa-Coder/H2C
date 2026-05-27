# Prompt per testare H2C in autonomia

**Istruzioni per l'IA:**

Leggi il repository ufficiale di **H2C** e fai 5 test in completa autonomia.

### Repository da consultare:
- **URL**: https://github.com/PaoEng/H2C
- Leggi in particolare:
  - `README.md`
  - `SPEC.md`
  - Cartella `examples/`
  - Cartella `skills/`

---

### Compito:

Esegui **5 test autonomi** simulando catene di comunicazione H2C con complessità crescente.  
Agisci come agente ricevente e rispondi **esclusivamente in formato H2C** rispettando la specifica **v1.2**.

### I 5 test da eseguire:

**Test 1 – Livello Semplice**  
Un semplice progetto "Hello World".

**Test 2 – Livello Medio**  
Un calculator CLI con implementazione, test e un fix (`cycle_id` obbligatorio nel ciclo `TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS`).

**Test 3 – Livello Avanzato**  
Refactoring verso Clean Architecture con gestione del contesto (`CTX:PRIMITIVES` / `CTX:UPDATE`).

**Test 4 – Livello Molto Complesso**  
Una catena lunga (minimo 10-12 messaggi) per una mini RAG pipeline (ricerca, implementazione, test multipli, fix, context management e chiusura).

**Test 5 – Stress Test v1.2**  
Catena di 60+ messaggi per validare i blocchi `CTX:PRUNE`, `CTX:COMPACT` e `CTX:FREEZE`. Verificare:
- `CTX:PRUNE` emesso ogni 5 messaggi (seguire la tabella di pruning in `SPEC.md` §3.3)
- `CTX:COMPACT` emesso ogni 20 messaggi
- `CTX:FREEZE` emesso oltre msg 100 quando il COMPACT non basta più
- Campi v1.2 usati correttamente: `rev:`, `after:`, `notes:`, `base_rev:`, `fail_count:`, `pass_count:`, `cycle_id:`, `retry_n:`
- Break point atteso oltre msg 100 (limite modello, non protocollo)

---

### Output richiesto:

Dopo aver eseguito i test, produci un report completo con:

1. **Descrizione breve** di ciascun test
2. **Tabella riassuntiva** con colonne:
   - Test
   - Complessità
   - Risparmio Token stimato (%)
   - Comprensione
   - Stabilità
   - Break point (se raggiunto)

3. **Osservazioni principali** (punti di forza e fragilità osservate, specialmente su catene lunghe)

4. **Confronto v1.1 vs v1.2** con dati su break point e stabilità

5. **Conclusione** sul comportamento di H2C v1.2.

---

**Regole importanti:**
- Fai i test veramente in autonomia (non simulare i risultati, genera catene reali).
- Usa solo il formato H2C v1.2 per le risposte interne ai test.
- Per il Test 5, applica PRUNE ogni 5 msg e COMPACT ogni 20 msg, FREEZE oltre msg 100.
- Sii obiettivo e tecnico nei risultati.
- Alla fine del report indica la data del test.

---

Inizia quando sei pronto.
