# ADR-0003: GitHub Actions reaches GCP through Workload Identity Federation, as a planner or a deployer

## Status
Accepted (2026-10-07). The results section is filled in once the
bootstrap has run and the first plan and apply have gone through.

## Context
Everything on GCP is Terraform, applied from CI, never from a laptop: the
FleetAlert AI arrangement (its ADR-0005), on a different cloud. That needs
CI to authenticate to GCP, and two FleetAlert lessons apply:

- **Long-lived keys are the wrong tool.** FleetAlert used GitHub OIDC
  into an AWS role; GCP's equivalent is Workload Identity Federation.
- **Bind on immutable ids, not names** (FleetAlert ADR-0004). GitHub
  embeds account and repository ids into the OIDC `sub` claim, and a
  renamed repository or account would otherwise silently lose access, or
  a re-created one with the same name silently gain it.

Terraform also cannot create the credentials it runs with, so some part
of the setup has to happen by hand, once.

## Decision
- **Workload Identity Federation, no keys.** One pool (`github`), one
  provider (`coverageiq`) trusting `token.actions.githubusercontent.com`,
  with an attribute condition that only accepts tokens whose
  `repository_owner_id` is Michael's account id.
- **Two service accounts, bound by numeric ids:**
  - `coverageiq-planner` has `roles/viewer` on the project and
    `roles/storage.objectUser` on the state bucket (enough to read state
    and take the lock). Any job in the repository (matched on
    `repository_id`) may use it. It cannot read secret values: `viewer`
    does not include `secretAccessor`.
  - `coverageiq-deployer` has the admin roles for the services the
    environment uses. Only a job running in the GitHub Environment
    `gcp-apply` may use it, matched on a mapped attribute `repo_env` =
    `repository_id:environment`. The environment's required reviewer is
    the human gate.
- **Wide by action, narrow by resource** for the deployer, as on
  FleetAlert: admin roles, but on a project whose only purpose is this
  system. `roles/resourcemanager.projectIamAdmin` is the broad one. It is
  there so Terraform can grant the Cloud Run runtime account its roles,
  and it means the deployer could grant itself anything in this project.
  Accepted for a single-purpose demo project; the alternative (the
  bootstrap pre-creating the runtime account and its grants) splits one
  service account's definition across two places.
- **Plan on pull requests, apply on merge.** `terraform-plan` runs as the
  planner on every pull request once the bootstrap has happened;
  `terraform-validate` (format and validate, no credentials) runs always.
  `Terraform Apply (demo)` runs as the deployer on push to `main`, inside
  `gcp-apply`.
- **One-time bootstrap by hand**, as a script (`infra/bootstrap/
  bootstrap.sh`): the state bucket, the two service accounts, the pool,
  the provider and the bindings. It is idempotent, so it can be re-run
  after a partial failure, which the FleetAlert bootstrap could not.
- **Two things stay manual on purpose.** The budget alert, because
  `google_billing_budget` needs billing-account permissions that do not
  belong on a project deployer. The Anthropic key value, which Terraform
  never holds: the secret exists in Terraform, the value is typed into
  the console.
- **Terraform does not own what workflows own.** The Cloud Run image is
  set by the deploy workflow and ignored by Terraform (`ignore_changes`).
  The deployed Vector Search index is created and removed by the eval
  workflow (ADR-0001); Terraform owns the index and the endpoint, which
  cost nothing while nothing is deployed.

## Consequences
- No credential to rotate or leak. A token is valid for one job.
- A renamed repository or account keeps working; a re-created one does
  not get in.
- The planner's permission list is expected to grow in the same
  "plan needs one more read permission after the first real apply" tail
  FleetAlert hit. `roles/viewer` is broad enough that it should be short.
- `projectIamAdmin` on the deployer is the known soft spot, documented
  above.
- GitHub repository variables (`GCP_PROJECT_ID`, `GCP_REGION`,
  `GCP_WIF_PROVIDER`, `GCP_PLAN_SA`, `GCP_APPLY_SA`) and the `gcp-apply`
  environment are configuration outside the repository. The bootstrap
  prints their values.

## Results
To be filled after the first plan and apply: how many permission rounds
the planner needed, how long the apply took, and anything the Vector
Search resources needed that the provider docs did not mention.
