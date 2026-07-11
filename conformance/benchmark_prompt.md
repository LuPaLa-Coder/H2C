# H2C Protocol — Deterministic Benchmark

Generate H2C v1.4 chains for 5 scenarios. Compare each against a FIXED reference NL text (provided below). Produce a benchmark report.

## Counting Method (IDENTICAL on any model)

- **Characters**: count `len(text)` — always the same across all models
- **Words**: count `len(text.split())` — standard space tokenization
- **Tokens (estimated)**: `chars / 3.7` for H2C, `chars / 1.3` for NL
- Use these EXACT formulas. Do not use your native tokenizer.

## H2C v1.4 Format

```
[TYPE:SUBTYPE]
key:val|key:val|...
```

Block on 2 lines. Lists: `[a,b,c]`. Revisions: `file~N`. CTX: `~key:val`.
Every chain MUST start with CTX:NEGOTIATE + STATE:ACK and end with ORCH:END.

---

## Scenario 1 — Hello World (Simple)

**Reference NL (FIXED — do not modify):**
```
Create a simple Hello World project in Python using FastAPI. This is a Python 3 project with no external libraries beyond the standard library. The structure is a single file called main.py. The pattern is a simple script. No authentication needed, no external dependencies. The constraint is to use only the standard library. Now implement the main.py file that prints Hello World and serves a basic FastAPI endpoint at the root path returning a greeting. After implementation, I need you to run the test: execute python main.py and verify it starts without errors. The test passed successfully with 1 assertion passing. This completes the development workflow. The chain is done.
```

Generate the H2C chain (8-10 blocks: NEGOTIATE, ACK, ARCH:PLAN, BUILD:EXEC, BUILD:DONE, TEST:RUN, TEST:PASS, ORCH:END).

---

## Scenario 2 — Calculator CLI (Medium)

**Reference NL (FIXED — do not modify):**
```
I need a command-line calculator in Python supporting addition, subtraction, multiplication, and division. Architecture plan: Python 3 with the argparse library for CLI argument parsing. The pattern is a command-line tool. Tools needed are python and pytest for testing. The structure has two files: calc.py for the calculator logic and test_calc.py for unit tests. Constraints: use standard library where possible, full unit test coverage for all four operations. Task 1: implement calc.py to parse command-line arguments including two numbers and an operator, then dispatch to the correct arithmetic operation handling all four operations. Task 1 is done, calc.py created at revision 1 using argparse with four operations. Task 2: write unit tests in test_calc.py for all four operations, depends on task 1. Task 2 is done, test_calc.py created at revision 1 with six test cases. Run the tests with pytest test_calc.py. The tests failed with ZeroDivisionError in the division by zero test case. Five tests passed, one failed. This opens fix cycle fix-div-zero. I need a fix for calc.py starting from revision one: add a guard against division by zero that raises a ValueError. This is fix cycle fix-div-zero, first retry attempt. The fix is applied, calc.py updated to revision two with the guard added. Run the tests again with pytest test_calc.py. All six tests pass now. Fix cycle fix-div-zero is closed. The development workflow is complete.
```

Generate the H2C chain with fix cycle (TEST:FAIL → BUILD:FIX with cycle_id + retry_n → BUILD:DONE → TEST:PASS).

---

## Scenario 3 — Clean Architecture (Advanced)

**Reference NL (FIXED — do not modify):**
```
I need to refactor a monolithic FastAPI application toward Clean Architecture with four layers: domain, use cases, adapters, and infrastructure. Architecture plan: FastAPI framework with Pydantic for data validation and SQLAlchemy for database persistence. The pattern is Clean Architecture using ports and adapters. Tools include python, pytest, and mypy for type checking. The target directory structure has five directories: domain for entities, use_cases for application logic, adapters for external interfaces, infra for wiring, and tests. Important constraints: the dependency rule must be respected where dependencies point inward, and dependency injection should be used throughout. Initial context: the task is to refactor a monolith into clean architecture layers. The constraint is to keep the existing test suite green throughout the refactoring. The goal is to achieve clean separation across all four layers with proper dependency direction. First, create domain/user.py with a User entity as a frozen dataclass value object with no ORM dependencies. Domain user complete at revision one. Next, create domain/order.py with an Order entity that validates business invariants in its constructor. Domain order complete at revision one. Context update: the domain layer is finished, next step is use cases. Create use_cases/place_order.py to orchestrate order creation, depending on both domain entities, using Python Protocol classes as repository ports. Use case complete at revision one. Context prune: keeping the active entities, no superseded blocks yet. Create adapters/repo_sql.py implementing the repository ports with SQLAlchemy, implementing the adapter pattern. Adapters complete at revision one. Context update: adapters layer done, next is infrastructure wiring. Create infra/main.py with FastAPI dependency injection container wiring all layers together. Infrastructure complete at revision one. Run the full test suite with pytest. Tests failed with three failures: there is an import cycle where domain/user.py imports from adapters/repo_sql, violating the Clean Architecture dependency rule. Fourteen tests passed, three failed. This opens fix cycle fix-import-cycle. Analysis finding: the root cause is that domain/user.py directly imports the SQLAlchemy adapter concrete implementation. The fix is to replace this with a typing.Protocol abstraction. The impact is that the dependency rule is currently broken where domain depends on adapters. Fix domain/user.py from revision one: remove the adapter type hint and use a Protocol class from the typing module instead. This is fix cycle fix-import-cycle, retry number one. Fix applied: domain/user.py updated to revision two, now using typing.Protocol for repository abstraction. Run tests again. All seventeen tests pass now. Fix cycle fix-import-cycle is closed. Final context update: all layers are complete. The refactoring is done.
```

Generate the H2C chain with at least 15 messages including CTX:PRIMITIVES, CTX:UPDATE, CTX:PRUNE, STATE:FINDINGS.

---

## Scenario 4 — Mini RAG Pipeline (Very Complex)

**Reference NL (FIXED — do not modify):**
```
I need to build a mini RAG retrieval augmented generation pipeline with six stages: document loading, text chunking, embedding generation, vector indexing, retrieval, and LLM query. Architecture plan: Python 3 with sentence_transformers for generating embeddings, FAISS for vector similarity indexing, PyPDF for PDF document parsing, and FastAPI to expose the query endpoint. The pattern is a modular RAG pipeline. Tools include python and pytest. The directory structure spans six modules: ingest for document loading, embed for embedding generation, index for vector storage, retrieve for search, query for LLM interaction, and tests. Notes: this is an MVP prototype, use local file-based index only, retrieve top five most relevant chunks. Initial context: build a complete RAG pipeline with all six stages functioning end to end. Constraint: everything must run locally with no external API calls. Goal: functional document retrieval with LLM-based query answering using retrieved context. First, create ingest/pdf_loader.py to load PDF files and extract text content page by page using PyPDF. Done at revision one. Create ingest/chunker.py with a sliding window chunker using five hundred token windows and fifty token overlap, depends on pdf_loader. Done at revision one. Context prune: keep first two ingest modules, no superseded blocks yet. Create embed/encoder.py wrapping sentence_transformers for batch encoding, depends on chunker. Done at revision one with batch size thirty two. Create index/faiss_store.py to build a flat L2 index and persist to disk, depends on encoder. Done at revision one using pickle for persistence. Run tests on the index module. Tests failed: dimension mismatch, the encoder produced seven hundred sixty eight dimensional vectors but the index expects three hundred eighty four dimensions. Zero tests passed, one failed. This opens fix cycle fix-dim-mismatch. Analysis finding: the root cause is that the wrong sentence transformers model was loaded, specifically mpnet base which produces 768-dimensional embeddings instead of all-MiniLM-L6-v2 which produces 384-dimensional embeddings. The fix is to hardcode the model identifier to all-MiniLM-L6-v2 in the encoder. The impact is that embedding dimensionality is wrong, breaking the FAISS index entirely. Fix embed/encoder.py from revision one: pin the model to all-MiniLM-L6-v2 explicitly. Fix cycle fix-dim-mismatch, retry one. Fix applied: embed/encoder.py at revision two with hardcoded correct model identifier. Run tests again. All three index tests pass. Fix cycle closed. Context update: index layer complete, next are retrieval and query stages. Create retrieve/topk.py for top-K similarity search with cosine distance normalization, depends on index. Done at revision one with L2 normalization before cosine distance. Context prune: keep index and retrieval modules, prune the earlier ingest modules as superseded. Create query/llm_call.py to assemble retrieved context and call a local LLM for answer generation, depends on retrieval. Done at revision one using Ollama locally with Gemma two billion parameter model. Run full pipeline tests. Tests failed: retrieved chunks show high redundancy because there is no diversification in the retrieval step. Two tests failed, eight passed. This opens fix cycle fix-mmr. Analysis finding: the root cause is the absence of Maximal Marginal Relevance diversification in the top-K retrieval function. The fix is to add MMR with lambda equal to zero point five to the retrieval. The impact is duplicate paragraphs in the LLM context window, reducing answer quality significantly. Fix retrieve/topk.py from revision one: add MMR diversification with lambda zero point five. Fix cycle fix-mmr, retry one. Fix applied: retrieve/topk.py at revision two with MMR implementation. Run tests again. All ten pipeline tests pass. Fix cycle closed. Final context update: all pipeline stages complete across all six modules at their current revisions. The RAG pipeline is complete.
```

Generate the H2C chain with at least 10 messages, 2 independent fix cycles with distinct cycle_id values, and STATE:FINDINGS with formal fields.

---

## Scenario 5 — Microservices Migration (Stress, 60+ messages)

**Reference NL (FIXED — do not modify):**
```
I need to migrate a large e-commerce monolith to event-driven microservices on Kubernetes with Kafka. Architecture: a mix of FastAPI Python services, Go for performance-critical auth, and Node.js for the API gateway. Infrastructure: Kafka for event streaming between all services, Redis for caching, PostgreSQL for persistence, Kubernetes for orchestration with Kustomize and ArgoCD, Istio for the service mesh. The pattern is event-driven microservices with saga-based distributed transactions. The system splits into twelve services: auth for authentication, user for profile management, catalog for product listings, cart for session-based shopping carts, order for order processing with saga pattern, payment for payment processing with Stripe integration, inventory for stock management with optimistic locking, shipping for carrier integration, notifications for multi-channel delivery, analytics for event sourcing, gateway for API routing with rate limiting, and bus for Kafka topic management. The auth service is built first in Go with JWT OIDC and PKCE, serving as the foundation all other services depend on. Build the user service in Python FastAPI for CRUD operations with JWT validation. The catalog service provides product search and filtering. The cart service uses Redis for ephemeral session carts. The order service implements the saga orchestrator for distributed transactions spanning payment, inventory, and shipping. The payment service integrates Stripe with idempotency key handling. The inventory service uses optimistic locking with version-based conflict detection. The shipping service abstracts multiple carrier APIs. The notifications service delivers via email, SMS, and webhooks. The analytics service consumes all Kafka topics for event sourcing. The API gateway handles routing, rate limiting, and authentication passthrough. The event bus defines all Kafka topics and consumer groups. Multiple fix cycles occur during development: an auth token rotation bug where JWK rotation invalidates in-flight tokens during saga transactions requires adding a grace period where both old and new keys are valid, fix cycle fix-jwk-rotation retry one. A user schema migration issue where a required field breaks backward compatibility with the catalog service requires making the field optional with a default value, fix cycle fix-user-migration retry one. An order saga timeout during payment processing requires increasing the timeout and adding a retry mechanism, fix cycle fix-saga-timeout retry two. A payment idempotency bug where duplicate charges could occur requires strict idempotency key enforcement, fix cycle fix-idempotency retry one. An inventory race condition during concurrent order processing requires optimistic lock retry with exponential backoff, fix cycle fix-inventory-race retry one. Context pruning occurs every five messages to keep only the active working set of service revisions. Compaction happens every twenty messages to summarize overall progress across all services. At message one hundred, a context freeze baseline is established with the complete snapshot of all twelve services at their current revisions, and all counters are reset. DAG transitive closure is validated across all twelve services: auth is the root dependency for all other services, user depends on auth, catalog depends on user, cart depends on catalog and user, order depends on cart and payment and inventory with full transitive closure verified to have no cycles. A malformed BUILD:EXEC block missing the required target field is detected and rejected with BUILD:NACK containing the reference identifier, error description, and a hint for how to correct it. The full migration involves over one hundred messages exercising every v1.4 protocol feature. At the end, all twelve services are deployed, tested end-to-end, and running in production across multiple regions with zero downtime migration achieved.
```

Generate the H2C chain with 60+ messages. Must include: CTX:PRUNE every 5 msgs, CTX:COMPACT every 20 msgs, CTX:FREEZE at msg 100, at least one BUILD:NACK with ref_id/error/hint, and DAG transitive closure.

---

## Report Template (fill with ACTUAL counts)

Count characters with a character counter, words with space-splitting. Apply the formulas EXACTLY.

```
=== H2C v1.4 Deterministic Benchmark ===
Date: <YYYY-MM-DD>
Model: <your model name>

| # | Scenario    | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |
|---|-------------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|
| 1 | Hello World |           | FIXED    |         |           | FIXED    |         |             | FIXED      |          |
| 2 | Calculator  |           | FIXED    |         |           | FIXED    |         |             | FIXED      |          |
| 3 | Clean Arch  |           | FIXED    |         |           | FIXED    |         |             | FIXED      |          |
| 4 | RAG Pipe    |           | FIXED    |         |           | FIXED    |         |             | FIXED      |          |
| 5 | Stress      |           | FIXED    |         |           | FIXED    |         |             | FIXED      |          |

TOTAL: H2C chars=<N> | NL chars=<N> | Avg char save=<X>% | Avg token save=<X>%

v1.4 Features:
  CTX:NEGOTIATE [ ]  STATE:ACK [ ]  BUILD:NACK [ ]  STATE:FINDINGS [ ]
  CTX:PRUNE     [ ]  CTX:COMPACT [ ]  CTX:FREEZE [ ]  Fix cycle [ ]
  DAG closure   [ ]
```

## Rules

1. Generate H2C chains FIRST, then count, then fill the table
2. The NL chars/words/tokens are FIXED — count them from the reference text above
3. Use ONLY the counting method specified: `len(text)`, `len(text.split())`, `chars/3.7`, `chars/1.3`
4. Fill ALL cells in the table — do not skip any
5. Report ONLY the table + feature checklist. Zero narrative.
