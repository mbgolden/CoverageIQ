# Backlog

Deferred work and open decisions, with what would re-open each one. Items
leave this list by becoming a pull request (and, for decisions, an ADR).

## Open decisions
- **Which plans, and whether insurers are named** on the public demo.
  Needed before ingestion starts (SCOPE.md day 3).
- **Monthly budget ceiling.** Assumed $50, as on FleetAlert. Needed before
  the GCP budget alert is created.
- **Reranker:** Vertex AI's ranking API or a small cross-encoder in Cloud
  Run. Decide when the first ablation table exists, so the choice is
  measured against vector-only, BM25-only and hybrid.
- **Frontend hosting on GCP.** Decide with the walking skeleton.
- **Target postings.** Check the scope's wording against them.

## Deferred work
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
