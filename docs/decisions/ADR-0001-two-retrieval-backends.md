# ADR-0001: Two retrieval backends, with Vertex AI Vector Search deployed on demand

## Status
Accepted (2026-10-02), before any code. The results section is empty until
the first comparison run.

## Context
Two goals pull against each other:
- **Hands-on Vertex AI Vector Search is a goal of the project.** It appears
  by name in job postings and is new ground.
- **The demo has to stay cheap while it sits idle.** The working ceiling is
  $50 a month for everything, as on FleetAlert.

Vector Search bills for a deployed index by the node hour, whether or not
anyone queries it. Prices from Google's pricing page on 2026-10-02,
us-central1:

| Item | Price | For this project |
|---|---|---|
| Smallest serving node (e2-standard-2) | $0.0938 per hour | about $68 a month if left on |
| Index build or update | $3.00 per GiB processed | about 5 cents |
| Streaming inserts | $0.45 per GiB | negligible |
| Storage-optimized tier | $2.30 per hour | not for this size |

The build figure assumes about 5,000 chunks at 768 dimensions, which is
roughly 15 MB of vectors.

So an always-on index costs more than the whole budget, and it would be
serving a corpus that is far too small to need approximate search. The
index itself costs almost nothing. The cost is the hours it stays deployed.

## Decision
- **Retrieval sits behind one interface.** It takes a question, a plan and
  a plan year, and returns ranked chunks. The reranker and everything after
  it are the same for both backends.
- **BigQuery vector search serves the public demo.** Chunks, embeddings and
  metadata already live in BigQuery. It bills per query, so an idle demo
  costs close to nothing. Keyword search is BM25 held in memory in the
  Cloud Run service, and the two result lists are fused in code.
- **Vertex AI Vector Search is a second backend, deployed on demand.** A
  GitHub Actions workflow:
  1. deploys the index to an endpoint (e2-standard-2, small shard size),
  2. runs the eval suite and a latency benchmark against it,
  3. writes the results to the eval history,
  4. undeploys the index.
- **The Vector Search backend uses the service's own features** so the
  hands-on time covers what postings ask about:
  - approximate and brute-force indexes,
  - batch and streaming updates (the document-freshness path),
  - filtering by plan and plan year,
  - built-in hybrid search over dense and sparse vectors.
- **Three safeguards against a forgotten endpoint**, which is the one real
  budget risk:
  - the undeploy step runs even when the eval job fails,
  - a nightly scheduled job undeploys anything still deployed,
  - a budget alert on the project. GCP budgets notify. They do not cap
    spend, so this is the last line, not the first.
- **A config flag picks the live backend.** Pointing the public demo at
  Vector Search is a setting, and costs about $68 a month while it is on.

## Consequences
- A three-hour session costs about 30 cents. Forty hours over the build is
  about $4.
- The public demo never depends on an endpoint being up.
- There are two backends to keep working. The shared interface and running
  the same golden set through both keep them honest.
- The backends differ in more than the vector index. BigQuery searches a
  corpus this small exactly, and fusion happens in code. Vector Search is
  approximate, and fuses dense and sparse results itself. The comparison
  has to say which differences come from which cause. A brute-force Vector
  Search index gives the exact baseline to separate them.
- The on-demand workflow is slow to start, because deploying an index takes
  a while. The time is recorded in the first run. It rules out running the
  Vector Search evals on every pull request, so they run on request and
  before a release.
- At this corpus size the comparison will not show Vector Search winning on
  recall or cost. That is the finding. The write-up states where the
  crossover would be (corpus size and query rate) instead of pretending the
  demo needs the service.

## Alternatives considered
- **Vector Search always on.** $68 a month for one idle node, over the
  budget on its own.
- **BigQuery only.** Cheapest, but no experience with the service the
  postings name.
- **Vector Search only, deployed on demand.** The public demo would be down
  most of the time.
- **pgvector on Cloud SQL.** Also billed while idle, and a third store to
  run next to BigQuery.

## Results
To be filled from the first comparison run. Same golden set, both backends:

| | BigQuery + BM25 | Vector Search (approximate) | Vector Search (brute force) |
|---|---|---|---|
| Recall@k | | | |
| MRR | | | |
| Latency p50 / p95 | | | |
| Cost per month, idle | | | |
| Cost per month, always on | | | |
| Time to deploy / undeploy | n/a | | |
