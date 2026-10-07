# CoverageIQ

A health-plan coverage assistant. It answers "what does my plan cover"
questions from real plan documents, cites the section each answer came
from, and never gives clinical advice.

**Status:** scaffolding. The retrieval interface, in-process BM25 and
reciprocal rank fusion exist with tests. Nothing is deployed yet.

- [Project scope](SCOPE.md)
- [Backlog](docs/BACKLOG.md)
- [Decision log](docs/decisions/)
  - [ADR-0001: Two retrieval backends, with Vertex AI Vector Search deployed on demand](docs/decisions/ADR-0001-two-retrieval-backends.md)
  - [ADR-0002: Pull-request workflow, with CI checks as the gate](docs/decisions/ADR-0002-pull-request-workflow.md)

## Layout

- `backend/` is the Python package `coverageiq`, managed with uv.
  `retrieval/` holds the shared retriever interface, the one tokenizer,
  BM25 and reciprocal rank fusion.
- `docs/` holds the scope, the backlog and the decision records.

## Developing

```bash
cd backend
uv sync --group dev
uv run pytest
```
