# CoverageIQ: Project Scope (v2)

A health-plan coverage assistant built on retrieval-augmented generation.

Third portfolio project, after PlayIT and FleetAlert AI.
Revised 2026-10-02. Replaces `HealthPlan_RAG_Assistant_Scope.docx` (v1).

## What changed from v1
- **Free-text questions are allowed**, with bounds. v1 copied FleetAlert's
  "no free-text input" rule, which left nothing for retrieval or the scope
  guardrail to prove.
- **Real public documents**, not synthetic ones.
- **Two retrieval backends**: BigQuery vector search for the always-on demo,
  Vertex AI Vector Search deployed on demand
  ([ADR-0001](docs/decisions/ADR-0001-two-retrieval-backends.md)).
- **A reranker and an ablation table** are in scope.
- **Plan and plan-year filtering**, boundary cases, abstention and judge
  calibration are named explicitly.
- **The schedule starts with a deployed walking skeleton**, not with
  infrastructure on days 11-12.

## What it does
A member-facing assistant that answers coverage questions grounded in real
health plan documents: Summary of Benefits and Coverage (SBC) forms,
formulary (drug coverage) lists and prior-authorization rules.

It stays in the "what does my plan cover" lane and never gives clinical
advice. That boundary is a guardrail designed on purpose, and it is the
part of the project that sixteen years of healthcare work under HIPAA backs
up.

There is no member identity and no PHI. The visitor picks a plan and a plan
year, then asks a question.

## Requirements and constraints
- **GCP is a requirement.** The stack is Cloud Run, Vertex AI, BigQuery,
  Cloud Logging/Monitoring/Trace.
- **Hands-on Vertex AI Vector Search is a goal.** It appears by name in job
  postings and is new ground. It must not set the monthly bill (ADR-0001).
- **Claude stays the generation model**, for consistency with the other two
  projects.
- **Budget:** assumed to be the same $50 a month ceiling as FleetAlert. To
  confirm.

## Core components

### 1. Document ingestion
- **Real public documents.** SBCs are public by federal law, so a small set
  of real SBC, formulary and prior-authorization PDFs is used: 3-5 plans,
  two plan years for at least one of them. Real PDFs have the messy benefit
  tables and footnotes that make chunking hard. Documents written for the
  demo would be documents the chunker handles easily.
- **Chunking by section, preserving table structure.** A benefit-table row
  keeps its column headers and its footnotes.
- **Embeddings from Vertex AI.**
- **Every chunk carries metadata:** plan, plan year, document type, document
  version, section, page.
- **Freshness.** When a plan year's document is revised, it is re-ingested
  and re-embedded as a new version. Retrieval only sees the current version,
  so an answer is never served against a superseded document.

### 2. Hybrid retrieval
- **Semantic search** over the embeddings.
- **Keyword (BM25) search** in parallel, for exact terms: plan names,
  procedure codes, drug names.
- **Reciprocal rank fusion** to combine the two.
- **A reranker** over the fused candidates.
- **Filtering by plan and plan year before ranking.** Answering from the
  wrong plan's document is the most realistic failure in this domain.
- **One retriever interface, two backends** (ADR-0001):
  - BigQuery vector search plus in-process BM25 serves the public demo.
  - Vertex AI Vector Search, with its built-in dense plus sparse hybrid
    search, is deployed on demand for evals and benchmarks.

### 3. Grounded answer generation
- Every answer cites the document, section and page it came from.
- If retrieval finds nothing relevant, or confidence is low, the assistant
  says so and routes to "contact your plan". It does not guess.

### 4. Guardrails
- **Scope boundary: coverage and benefits only, never clinical advice.**
  A classifier checks the question's intent before retrieval or generation
  runs. It is a separate step, not a line in the answer prompt.
- **The boundary cases are the test set.** "Is Ozempic covered for weight
  loss?" is in scope. "Should I take Ozempic?" is not. Prior-authorization
  rules contain clinical criteria, so the assistant can quote what the plan
  requires without advising on it.
- **Bounded free text.** Visitors can type their own question. The bounds:
  - a per-visitor rate limit,
  - a length cap on the question,
  - a daily cost guard that turns generation off when the budget is spent
    (the FleetAlert pattern),
  - the scope classifier runs on a cheap model first.
- **Seeded sample questions stay** as one-click examples, including ones
  that should be refused.

### 5. Evaluation harness (the most important piece)
- **A golden set** of questions with known-correct source citations,
  written against the real documents. It includes:
  - answerable questions, tagged by type (benefit table, drug name,
    procedure code, prior authorization),
  - unanswerable questions, where the right response is to abstain,
  - out-of-scope clinical questions, where the right response is to refuse,
  - wrong-plan traps, where another plan's document has a tempting answer.
- **Retrieval quality:** recall@k, MRR and citation correctness.
- **The ablation table:** vector only, BM25 only, hybrid, hybrid plus
  reranker, broken out by question type. This is what shows that hybrid
  retrieval earns its place.
- **Faithfulness:** does the answer claim only what the retrieved source
  says. Scored by a model judge that is calibrated against a small
  hand-labelled set first.
- **Abstention and refusal** are scored separately (precision and recall).
- **Backend comparison:** the same golden set through both retrieval
  backends, for recall, latency and monthly cost (ADR-0001).
- **Gates every change**, as in FleetAlert.
- **Optional:** Gemini as a second generation model, run through the same
  harness. First thing cut if time is short.

### 6. Observability
Cloud Logging, Cloud Monitoring and Cloud Trace. Kept thin: a trace per
question (classify, retrieve, rerank, generate), cost per question, and the
cost guard. This repeats FleetAlert on a different cloud, so it gets the
least time.

## Stack
Python, Cloud Run, Vertex AI (embeddings, Vector Search), BigQuery (chunks,
embeddings, document metadata, eval history), Terraform, GitHub Actions,
React, Claude API.

Python is used for the whole back end (ingestion, the serving API and the
eval harness) and React for the front end.

## Two-week shape
| Days | Work |
|---|---|
| 1-2 | Walking skeleton: GCP project, Terraform, GitHub Actions auth to GCP, a Cloud Run endpoint and a stub frontend deployed, budget alert set |
| 3-5 | Collect real documents, chunking pipeline (tables), embeddings, BigQuery store with plan, year and version metadata |
| 6-7 | Hybrid retrieval on BigQuery plus BM25, fusion, reranker. Golden set and retrieval evals, first ablation table |
| 8-9 | Grounded generation with citations, scope classifier, abstention. Faithfulness evals and judge calibration |
| 10 | Vertex AI Vector Search backend, on-demand deploy workflow and its safeguards, first backend comparison run |
| 11-12 | Frontend with bounded free text, cost guard, thin observability |
| 13-14 | Stress test with ambiguous and edge-case documents, document the failure, ADRs and the site page |

Two weeks is tight for a new cloud. If it slips, cut in this order: the
Gemini comparison, observability depth, frontend polish. Do not cut the
eval harness or the Vector Search comparison.

## Open questions
- Which plans, and whether insurers are named or masked on the public demo.
  Either way the demo carries source links and a "not for real coverage
  decisions" notice.
- Monthly budget ceiling (assumed $50).
- Which reranker: Vertex AI's ranking API or a small cross-encoder in Cloud
  Run. Gets its own ADR.
- Frontend hosting on GCP.
- Which posting(s) this is aimed at, to check the scope against their
  wording.
