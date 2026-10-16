# Administrator setup

Repository files are only part of adoption. Perform this checklist on each new
repository; no live settings, secrets, labels or cloud resources are provisioned
by copying the template.

## 1. Repository and account prerequisites

- Mark the source repository as a template if offering template creation; create
  an adopter repository and confirm its actual default branch. No `main` name
  is assumed. Keep Issues and Actions enabled.
- Confirm account/organization plan, Copilot cloud-agent availability, seats,
  repository access, organization policy, billing and usage limits.
- Enable Actions and the pinned actions/runners used by the workflows. Review
  organizational restrictions, fork policies, retention and spending limits.
- Give the user performing assignment repository write access and any needed
  organization/SSO authorization. Review preview API changes if assignment fails.

## 2. Token and repository variables

Create a fine-grained **user personal access token**, restricted to this
repository, with:

| Repository permission | Access |
| --- | --- |
| Metadata | Read |
| Actions | Read and write |
| Contents | Read and write |
| Issues | Read and write |
| Pull requests | Read and write |
| Checks | Read |
| Commit statuses | Read |

Checks and Commit statuses are required to verify current-head CI evidence;
without them every reconcile pauses with `APIError: GitHub API 403: Forbidden`.

Create an Actions environment named **`sdlc-control`**. Under its deployment
branch/tag restrictions, choose **Selected branches and tags**, permit a
**branch rule matching only the actual default branch**, and permit no tags.
Do not use an unrestricted environment or a rule allowing all protected
branches. Store **`SDLC_TOKEN` as a secret in this environment only**, never as
a repository/organization secret or in the cloud agent's `copilot` environment.
The two control jobs explicitly select `sdlc-control`; PR validation jobs do not.
Leave required reviewers and wait timers off if unattended control is desired.
This environment protects control credentials; it does not deploy the application.

**Verify your visibility/plan supports these environment branch restrictions
before enabling automation.** If not, keep `SDLC_ENABLED` off; do not downgrade
to a repository secret. A PR-authored workflow could otherwise request the PAT,
even when the supplied validation workflows themselves never reference it.
In the smoke run, verify a PR-ref job cannot access the control environment.
Reconfigure its exact allowed branch when renaming the default branch.

This workflow needs a
user token: `GITHUB_TOKEN` and GitHub App installation tokens cannot assign
Copilot. Complete organization approval/SSO requirements if applicable. Set an
expiry, record its owner and a rotation date, and use least repository scope.
Never expose the token to PR validation, app processes or deployment.
Retain the **same user owner** on rotation: ledger provenance is bound to the
PAT owner. Different-owner migration requires deliberate manual handling, not
an automatic replacement.

Set repository Actions variables:

| Variable | Value / effect |
| --- | --- |
| `SDLC_ENABLED` | Exact string `true` to permit controller operation |
| `SDLC_REQUIRE_DEPENDENCY_REVIEW` | Required exact `true` or `false`; prefer true where entitled |
| `SDLC_CODEQL_ENABLED` | Required exact `true` or `false`; prefer true where entitled |

Unset or any value other than the exact strings above fails policy validation.
For repositories without dependency-review entitlement, explicitly set
`SDLC_REQUIRE_DEPENDENCY_REVIEW=false`; `docs/dependency-policy.md` is required.
The initial alternative covers pinned/hashed pip tooling with a public-advisory
check and reviewed, SHA-pinned Actions with Dependabot updates. **Bootstrap must configure a real
dependency-security alternative in the mandatory nonempty application security
command**, including advisory scanning of actual manifests/lockfiles and a
reviewed vulnerability policy. Before application bootstrap this is only a
template-level baseline, not application dependency coverage. Do not present
absence of entitlement as a clean dependency scan or silently disable security.
For CodeQL, set `SDLC_CODEQL_ENABLED=true` where entitled. Explicit `false`
requires `docs/code-scanning-policy.md`, Ruff S analysis of template Python and
contract validation. Required `Application checks` executes the configured app
security/advisory commands on the selected app runner; fallback policy jobs do
not execute app commands on hardcoded Ubuntu. Ruff alone does not cover
arbitrary application languages.

## 3. Copilot execution and review settings

- In Copilot cloud-agent settings, to automate trusted runs, disable **Require
  approval for workflow runs** as documented by GitHub. This is an explicit
  administrator choice, not a workflow approval bypass.
- **Risk:** agent-authored changes can execute Actions automatically, including
  malicious changes resulting from prompt injection or compromised dependencies.
  Keep privileged control isolated on trusted default-branch code and the
  branch-restricted `sdlc-control` environment, ordinary
  checks secret-free, checkout credentials unpersisted, and deploy credentials
  unavailable. Review workflows, tokens and allowed actions carefully. If the
  risk is unacceptable, retain approval and accept a manual workflow step.
- Configure native automatic Copilot code review through repository
  settings/rules, including **draft PRs and new pushes** where supported.
  Verify it actually runs on the smoke PR; cloud-agent self-review is separate
  and is not approval.
  The controller requires a current-head Copilot PR review from the actual
  review API before advancing; a previous-head review does not qualify.
- GitHub may still require the requesting human to mark a draft ready or perform
  platform actions. Never promise every readiness/review operation is automatic.
- Keep auto-merge disabled; do not add automatic approval or merge workflows.

## 4. Security and maintenance

- Enable code scanning/CodeQL if available for the visibility and plan and set
  the required CodeQL variable explicitly. With `SDLC_CODEQL_ENABLED=true`,
  switch any CodeQL **default setup** to advanced setup; the two conflict.
  Baseline CodeQL scans template Python only. Bootstrap adds supported app
  languages, appropriate build setup and additional checks. Unsupported
  languages require an alternative security command.
- Verify dependency graph, Dependabot alerts/security updates, secret scanning
  and push protection individually. Availability differs across public/private
  repositories and paid security products. Do not assume these transfer or
  claim blanket security enablement.
- `.github/dependabot.yml` includes GitHub Actions and known Python template
  tooling in `/scripts`. Bootstrap adds
  actual application ecosystems/directories and lockfiles. Dependabot/fork PRs
  run the same secret-free CI and are manually reviewed/merged.
- Enable private vulnerability reporting or configure a private contact route.
- `.github/CODEOWNERS.example` is inert. Copy it to `CODEOWNERS` only after
  replacing placeholders with actual users/teams and checking team access.

## 5. Initialize and smoke-test before branch protections

1. Run **SDLC Setup** in `.github/workflows/sdlc-setup.yml`; verify labels
   `sdlc:start`, `sdlc:managed`, `sdlc:needs-human`, `sdlc:paused`,
   `sdlc:complete` exist. Labels are not inherited working state.
2. Run **SDLC Controller** in `.github/workflows/sdlc-controller.yml` manually
   with action `reconcile` and the intended `root_issue` when recovering an
   existing pipeline. For first kickoff, create a brief issue and have a writer
   apply `sdlc:start`.
3. Verify successful assignment to the intended custom agent, one tracker
   ledger, and one platform-created PR with a closing-issue footer. Confirm
   API permissions, expected base, author and same-repository provenance.
4. Confirm automatic workflow execution/review settings, actual checks and
   manual readiness/merge behavior on this real PR. Observe a merged stage
   advancing and a closed-unmerged PR **not** advancing. Verify queued briefs.
5. Only now configure a ruleset for the actual default branch. Require PRs and
   observed checks; block force pushes/deletion and direct pushes as appropriate.
   Intended names: `Template checks`, `Application checks`, `Dependency policy`,
   `Code scanning policy`. Check-run names may differ: use observed names.
   When enabled, the code-scanning aggregate includes **all** CodeQL matrix
   results; add observed language checks to rules as appropriate after bootstrap.
6. For a solo maintainer, do not require an approving review by default: the
   requestor's own approval may not count. A team can require independent
   reviewers/CODEOWNERS once tested. Neither AI review nor self-review should
   be claimed to satisfy human approval requirements.
7. Do a complete small end-to-end run including bootstrap, task ordering,
   bounded repair, QA/security and final completion before relying on it.
   Local mocked tests do not verify live GitHub platform behavior.

## Copied files versus administrator configuration

An inert ruleset import example is provided at
[`ruleset.example.json`](../.github/sdlc/ruleset.example.json). It targets the
repository's actual default branch, has no bypass actors and starts
**disabled**. Verify observed check names and ruleset availability, adjust
reviewer requirements for your team, then enable it explicitly through GitHub.
Importing this file does not disable repository auto-merge: keep that separate
setting off. Never activate rules before the corresponding checks work.

| Copied through template | Must configure or verify separately |
| --- | --- |
| Agents, instructions, templates, scripts, workflow files | Copilot plan/access/policies and Actions approvals |
| Toolchain default contract, Dependabot baseline | Runtime-specific gates, ecosystems and scanner entitlements |
| Issue/PR templates and CODEOWNERS example | Labels, ownership identities, branch rules and checks |
| Security and deployment guides | PAT/secrets/variables, security settings, environments and OIDC |

Recheck settings after transfers, visibility/plan changes, default-branch
changes or template updates. See [operations](operations.md) for token rotation
and [adapting](adapting.md) for application bootstrap.

## Official references verified during planning

- [Cloud-agent API assignment, custom agents and user-token requirements](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api)
- [Cloud-agent settings and automatic workflow execution](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/configuring-agent-settings)
- [Cloud-agent risks, boundaries and mitigations](https://docs.github.com/en/copilot/concepts/security-governance-and-network-settings/risks-and-mitigations)
- [Configuring automatic Copilot code review](https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-code-review)
- [Reviewing cloud-agent output and human responsibilities](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/review-copilot-output)

Feature names, entitlement and preview APIs may change; verify these official
pages against the target account during the first smoke run.
