# ADR-0002: Pull-request workflow, with CI checks as the gate

## Status
Accepted (2026-10-07).

## Context
The repository started with one commit pushed straight to `main`, because
it was empty. From here on, code lands with a review step, the same way it
does on FleetAlert AI: Claude pushes branches, Michael merges, and the
merge is what deploys.

## Decision
- **Every change goes through a pull request** from a short-lived branch.
  Nothing is pushed to `main` directly.
- **CI on the pull request is the gate.** The `CI` workflow runs ruff
  (lint and format), mypy in strict mode, bandit and pytest for the
  backend. Frontend build and Terraform plan jobs are added when those
  directories exist.
- **A merge to `main` is a deploy.** Deploy workflows run on push to
  `main` once there is something to deploy (ADR to follow with the
  walking skeleton).
- **Decision records travel with the change** that makes the decision, in
  the same pull request.
- **Branch protection on `main`** requiring the `backend` check to pass
  is Michael's step in the GitHub settings. Until it is set, the rule
  above is convention.

## Consequences
- Every change has a reviewable diff and a green check before it lands.
- A commit pushed to a branch after its pull request is merged is lost
  unless it gets its own pull request. The rule is: never push to a branch
  whose pull request may already be merged. Open a new one.
- Branches are deleted after merge, once their tip is confirmed to be an
  ancestor of `origin/main`.
