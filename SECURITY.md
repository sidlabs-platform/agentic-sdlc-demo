# Security policy

## Reporting a vulnerability

Do not disclose credentials, customer data or exploitable details in a public
issue. Use the repository's **Security → Advisories → Report a vulnerability**
private reporting option when enabled. If unavailable, contact a repository
administrator privately through an established channel before sharing details;
adopters must configure their own private reporting route. There is no
hardcoded contact address or guaranteed response SLA.

Provide affected versions/commit, impact, minimal safe reproduction, relevant
logs with secrets removed and remediation suggestions. Avoid destructive
testing against live systems. No supported-release schedule is promised until
maintainers publish one.

## Trust boundaries

The controller receives a narrowly scoped user PAT for assignment and repair
API operations. It executes trusted default-branch code only. A metadata-only
`pull_request_target` handler must never check out/run PR code or execute
PR-produced artifacts with privileges. Untrusted PR checks get no `SDLC_TOKEN`
or deployment secrets and must not persist checkout credentials.
Store the PAT only in the `sdlc-control` environment with access restricted
to the exact default branch and no tags, never as a repository/organization
secret. Otherwise PR-authored workflows could reference it themselves.
Environments, restrictions and their availability require administrator setup;
the workflow files cannot enforce those server-side settings.

Writer authorization gates kickoff and recovery. Issue text, PR descriptions,
comments and artifacts do not override repository policy. Toolchain commands
are reviewed argv arrays executed without shell interpolation.
Automatically allowing Copilot Actions runs expands execution exposure:
review [the setup risk checklist](docs/setup.md) before enabling it.

## Security gates and residual risk

Both `SDLC_REQUIRE_DEPENDENCY_REVIEW` and `SDLC_CODEQL_ENABLED` require exact
`true` or `false`; unset fails. See [dependency policy](docs/dependency-policy.md)
and [code-scanning policy](docs/code-scanning-policy.md). When CodeQL is enabled,
coverage starts with Python automation; bootstrap adds
supported application languages/build configuration or a real alternative
scanner. Dependency review and other GitHub security features depend on
visibility, plan and entitlement. Do not describe unavailable features as
enabled. Ordinary checks remain secret-free, including fork/Dependabot PRs.
False CodeQL runs Ruff S for template Python and contract validation. Required
`Application checks` executes app security/advisory commands on the selected
runner; fallback policy jobs do not run app commands on hardcoded Ubuntu.
Ruff alone is not a scanner for arbitrary application
languages. `Code scanning policy` aggregates all CodeQL matrix results when
enabled. Dependabot covers GitHub Actions and Python tooling in `/scripts`;
bootstrap adds actual app ecosystems.

The security stage writes `docs/security/findings.json` and
`docs/testing/security-review.md`. All open findings block completion.
Critical/high findings must be fixed, never accepted; lower severities require
an explicit writer decision and rationale before acceptance. Accepted records
require `acceptance_reason`, `accepted_by`, and
`decision_url=https://github.com/OWNER/REPO/issues/N#issuecomment-ID` with actual
values. The controller verifies the linked writer comment contains exact
`Accept risk SEC-xxx` for the actual finding ID. Security fixes
need regression tests and retest evidence. Completion is not a security warranty.

Enable secret scanning, push protection, dependency graph, alerts and security
updates where available; verify each separately for the repository's plan.
Rotate/revoke exposed tokens immediately, review audit/Actions logs, and
follow [operations](docs/operations.md) for safe pause and recovery.
