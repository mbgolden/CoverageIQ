# CoverageIQ

A health-plan coverage assistant. It answers "what does my plan cover"
questions from real plan documents, cites the section each answer came
from, and never gives clinical advice.

**Status:** scaffolding. The retrieval interface, in-process BM25,
reciprocal rank fusion and the retrieval half of the eval harness exist
with tests. The GCP environment is defined in Terraform; nothing is
deployed until the bootstrap below has run.

- [Project scope](SCOPE.md)
- [Backlog](docs/BACKLOG.md)
- [Decision log](docs/decisions/)
  - [ADR-0001: Two retrieval backends, with Vertex AI Vector Search deployed on demand](docs/decisions/ADR-0001-two-retrieval-backends.md)
  - [ADR-0002: Pull-request workflow, with CI checks as the gate](docs/decisions/ADR-0002-pull-request-workflow.md)
  - [ADR-0003: GitHub Actions reaches GCP through Workload Identity Federation](docs/decisions/ADR-0003-gcp-workload-identity-federation.md)

## Layout

- `backend/` is the Python package `coverageiq`, managed with uv.
  `retrieval/` holds the shared retriever interface, the one tokenizer,
  BM25 and reciprocal rank fusion.
- `infra/` is Terraform for GCP: `envs/demo` wires the `modules/`
  (project services, Artifact Registry, BigQuery, Vertex AI Vector
  Search, Secret Manager, Cloud Run). `bootstrap/bootstrap.sh` is the
  one-time, by-hand setup that Terraform cannot do for itself.
- `docs/` holds the scope, the backlog and the decision records.

## Developing

```bash
cd backend
uv sync --group dev
uv run pytest
```

## Deploying

Once, by hand, as a project owner (Cloud Shell works):

```bash
bash infra/bootstrap/bootstrap.sh
```

It prints the GitHub repository variables to set and the Environment to
create. After that, Terraform plans on every pull request and applies on
merge to `main` through the `gcp-apply` environment (ADR-0003).
