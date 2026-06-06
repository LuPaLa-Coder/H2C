# Prompt to test H2C independently

**Instructions for the AI:**

Read the official **H2C** repository and run 5 tests completely independently.

### Repository to consult:
- **URL**: https://github.com/LuPaLa-Coder/H2C
- Read in particular:
  - `README.md`
  - `SPEC.md`
  - `examples/` folder
  - `skills/` folder

---

### Task:

Run **5 independent tests** simulating H2C communication chains with increasing complexity.  
Act as a receiving agent and respond **exclusively in H2C format** respecting the **v1.4** specification.

### The 5 tests to execute:

**Test 1 – Simple Level**  
A simple "Hello World" project.  
Must start with:
- `CTX:NEGOTIATE` block (version handshake, REQUIRED first block)
- `STATE:ACK` with `protocol:h2c_v1.4`

**Test 2 – Medium Level**  
A CLI calculator with implementation, test, and a fix (`cycle_id` required in `TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS` cycle).  
Use v1.4 fields: `cycle_id`, `retry_n:1`, `fail_count`, `pass_count`, `base_rev`, `rev`.

**Test 3 – Advanced Level**  
Refactoring towards Clean Architecture with context management (`CTX:PRIMITIVES` / `CTX:UPDATE`).  
Use v1.4 features:
- `CTX:PRIMITIVES` with `~task`, `~constraint`, `~goal`, `~form`
- `STATE:FINDINGS` with formal fields: `cause:`, `action:`, `impact:`, `components:`

**Test 4 – Very Complex Level**  
A long chain (minimum 10-12 messages) for a mini RAG pipeline (research, implementation, multiple tests, fixes, context management, and closure).  
Exercise independent fix cycles with distinct `cycle_id` values.

**Test 5 – Stress Test v1.4**  
Chain of 60+ messages to validate all v1.4 features. Verify:
- `CTX:NEGOTIATE` emitted as first block — mandatory handshake
- `STATE:ACK` with `protocol:h2c_v1.4` immediately after
- `CTX:PRUNE` emitted every 5 messages (follow the pruning table in `SPEC.md` §5.3)
- `CTX:COMPACT` emitted every 20 messages
- `CTX:FREEZE` emitted beyond msg 100 when COMPACT is no longer sufficient
- `BUILD:NACK` emitted on at least one malformed block (with `ref_id`, `error`, `hint`)
- `STATE:FINDINGS` uses formal fields: `cause:`, `action:`, `impact:`, `risk:`, `components:`, `pattern:`
- DAG `after:` transitive closure validated (no cycles across N nodes)
- v1.4 fields used correctly: `rev:`, `after:`, `notes:`, `base_rev:`, `fail_count:`, `pass_count:`, `cycle_id:`, `retry_n:`
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

3. **Main observations** (strengths and weaknesses observed, especially on long chains):
   - How does CTX:NEGOTIATE affect multi-agent compatibility?
   - Is BUILD:NACK effective for error recovery?
   - Are formal STATE:FINDINGS fields parseable by the receiver?

4. **v1.3 vs v1.4 comparison** with data on:
   - Version negotiation (absent vs CTX:NEGOTIATE)
   - Error recovery (silent discard vs BUILD:NACK)
   - FINDINGS structure (free-form vs formal fields)
   - DAG cycle detection (2-node vs transitive closure)
   - Break point and stability

5. **Conclusion** on the behavior of H2C v1.4.

---

**Important rules:**
- Really run the tests independently (don't simulate results, generate real chains).
- Use only the H2C v1.4 format for internal test responses.
- Every chain must start with `CTX:NEGOTIATE` followed by `STATE:ACK`.
- On malformed blocks, emit `BUILD:NACK` instead of silent discard.
- For Test 5, apply PRUNE every 5 messages and COMPACT every 20 messages, FREEZE beyond msg 100.
- `STATE:FINDINGS` should use formal fields: `cause:`, `action:`, `impact:`.
- Be objective and technical in the results.
- At the end of the report indicate the test date.

---

Start when ready.
