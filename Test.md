# Prompt to test H2C independently

**Instructions for the AI:**

Read the official **H2C** repository and run 5 tests completely independently.

### Repository to consult:
- **URL**: https://github.com/PaoEng/H2C
- Read in particular:
  - `README.md`
  - `SPEC.md`
  - `examples/` folder
  - `skills/` folder

---

### Task:

Run **5 independent tests** simulating H2C communication chains with increasing complexity.  
Act as a receiving agent and respond **exclusively in H2C format** respecting the **v1.3** specification.

### The 5 tests to execute:

**Test 1 – Simple Level**  
A simple "Hello World" project.

**Test 2 – Medium Level**  
A CLI calculator with implementation, test, and a fix (`cycle_id` required in `TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS` cycle).

**Test 3 – Advanced Level**  
Refactoring towards Clean Architecture with context management (`CTX:PRIMITIVES` / `CTX:UPDATE`).

**Test 4 – Very Complex Level**  
A long chain (minimum 10-12 messages) for a mini RAG pipeline (research, implementation, multiple tests, fixes, context management, and closure).

**Test 5 – Stress Test v1.3**  
Chain of 60+ messages to validate `CTX:PRUNE`, `CTX:COMPACT`, and `CTX:FREEZE` blocks. Verify:
- `CTX:PRUNE` emitted every 5 messages (follow the pruning table in `SPEC.md` §3.3)
- `CTX:COMPACT` emitted every 20 messages
- `CTX:FREEZE` emitted beyond msg 100 when COMPACT is no longer sufficient
- v1.3 fields used correctly: `rev:`, `after:`, `notes:`, `base_rev:`, `fail_count:`, `pass_count:`, `cycle_id:`, `retry_n:`
- Expected break point beyond msg 100 (model limit, not protocol limit)

---

### Required output:

After executing the tests, produce a complete report with:

1. **Brief description** of each test
2. **Summary table** with columns:
   - Test
   - Complexity
   - Estimated Token Savings (%)
   - Comprehension
   - Stability
   - Break point (if reached)

3. **Main observations** (strengths and weaknesses observed, especially on long chains)

4. **v1.2 vs v1.3 comparison** with data on break point and stability

5. **Conclusion** on the behavior of H2C v1.3.

---

**Important rules:**
- Really run the tests independently (don't simulate results, generate real chains).
- Use only the H2C v1.3 format for internal test responses.
- For Test 5, apply PRUNE every 5 messages and COMPACT every 20 messages, FREEZE beyond msg 100.
- Be objective and technical in the results.
- At the end of the report indicate the test date.

---

Start when ready.
