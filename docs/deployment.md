# Release and deployment interface

Deployment is **documentation/interface only and disabled by default**. A
completed SDLC pipeline means reviewed source and verification artifacts, not
a deployed service. No provider, credentials, cloud resources or successful
deployment job is implied.

## Release procedure

1. Verify intended commits are merged, required checks passed on the release
   revision, QA traceability is complete, security findings are fixed or validly
   writer-accepted, and no open blockers remain.
2. Choose a versioning policy suitable for the application; document breaking
   changes, migrations, compatibility and dependency/license obligations.
   No template license is selected; resolve rights before distribution.
3. Build immutable release artifacts from the reviewed revision, recording
   source SHA, dependency locks, build provenance and checksums where applicable.
4. Have a human approve/publish the release/tag according to repository policy.
   Agent execution does not authorize merging, tagging or publishing.
5. Record release notes, validation evidence, known limitations and recovery
   instructions. For template releases rerun contract/automation tests and
   document adopter settings/migrations separately from copied file changes.

## Opt-in deployment contract

Before adding an enabled provider-specific workflow, define and review:

| Interface | Required decision / evidence |
| --- | --- |
| Target | Provider, account/project, region, service, cost owner |
| Inputs | Immutable artifact/revision, version and named environment |
| Authentication | Provider-supported OIDC federation and least-privilege roles; no long-lived deploy secrets by default |
| Trust | Restrict OIDC subject/audience to approved repository/ref/environment; grant `id-token: write` only to the deployment job |
| Environments | Separate test/staging/production; protections and independent approvals where required |
| Configuration | Secret source, schema validation, safe nonproduction defaults |
| Change safety | Migration/backup plan, health/readiness checks, rollout/timeout policy |
| Outputs | Deployment ID, revision, environment, health evidence and redacted logs |
| Recovery | Last known-good artifact, rollback commands, data recovery owner and time targets |

Deployment runs must not receive `SDLC_TOKEN`. Never deploy untrusted PR code
or download/execute PR artifacts in privileged contexts. Ordinary validation
does not need deployment credentials. Configure GitHub environment rules and
provider OIDC trust separately; template file inheritance cannot create them.

## Rollback and incidents

Maintain an immutable previous release and test rollback in a nonproduction
environment. Stop rollout on health failure; a human authorizes production
recovery. Restore the last known-good artifact/configuration, assess database
compatibility and use tested backup/forward-fix procedures for irreversible
migrations. Verify health and critical journeys, record incident/revision
evidence, and add regression tests. Never advertise automatic rollback or a
recovery-time guarantee until it is implemented and exercised.
