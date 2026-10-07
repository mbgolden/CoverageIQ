# Backlog

Deferred work and open decisions, with what would re-open each one. Items
leave this list by becoming a pull request (and, for decisions, an ADR).

## Open decisions
- **Which plans, and whether insurers are named** on the public demo.
  Needed before ingestion starts (SCOPE.md day 3).
- **Monthly budget ceiling.** Assumed $50, as on FleetAlert. The budget
  alert is set by hand in the console (ADR-0003); it needs the number.
- **Reranker:** Vertex AI's ranking API or a small cross-encoder in Cloud
  Run. Decide when the first ablation table exists, so the choice is
  measured against vector-only, BM25-only and hybrid.
- **Frontend hosting on GCP.** Decide with the walking skeleton. Likely
  a GCS bucket behind a load balancer, or served by the Cloud Run service.
- **Target postings.** Check the scope's wording against them.

## Deferred work
- **A brute-force Vector Search index** as the exact baseline for the
  backend comparison (ADR-0001). Create it once there are embeddings to
  load; it is a second `google_vertex_ai_index` with
  `brute_force_config`.
- **Monitoring alerts** (error rate, latency, daily cost). Add with the
  observability pass, days 11-12.
- **Gemini as a second generation model** through the same eval harness.
  First thing cut if time is short.
- **Observability depth.** A trace per question and the cost guard are in
  scope; dashboards beyond that are not, until something needs one.
- **Stemming in the tokenizer.** `tokenize.py` does none. Re-open if the
  golden set shows keyword misses on inflected terms (plural benefit
  names, for example).
- **IDF over the filtered set rather than the whole corpus** in
  `bm25.py`. Re-open if cross-plan term frequencies visibly skew scores
  once there are several plans.
