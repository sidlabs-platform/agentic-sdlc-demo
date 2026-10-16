# Integration contracts

These contracts join the agent documents, controller, planner and validation.
Changes must update all consumers and tests together.

## Workflow, identity and state

- **SDLC Controller**, `.github/workflows/sdlc-controller.yml`: `issues`
  opened/labeled/edited/reopened; `pull_request_target`
  opened/edited/closed/synchronize; scheduled reconciliation every 15 minutes;
  manual input `action` = `reconcile`, `resume` or `pause`, and `root_issue`
  containing the root issue number.
- **SDLC Setup**, `.github/workflows/sdlc-setup.yml`: initializes `sdlc:start`,
  `sdlc:managed`, `sdlc:needs-human`, `sdlc:paused`, `sdlc:complete`.
- A repository writer applies `sdlc:start` to a manually created brief.
  `SDLC_ENABLED` must equal the string `true`; additional briefs queue.
- `SDLC_REQUIRE_DEPENDENCY_REVIEW` and `SDLC_CODEQL_ENABLED` must each equal
  exactly `true` or `false`; unset or other values fail policy validation.
  False requires the corresponding `docs/dependency-policy.md` or
  `docs/code-scanning-policy.md` alternative, not silent gate removal.
- Assignment uses `copilot-swe-agent[bot]` with
  `agent_assignment.custom_agent`. Agent identities are filenames without
  `.agent.md`; no fixed branches or textual agent-mention dispatch.
- `SDLC_TOKEN` is a fine-grained **user** PAT with Metadata, Checks and Commit
  statuses read, and Actions, Contents, Issues and Pull requests read/write
  for the target repository.
  It is an environment secret in `sdlc-control`, restricted to the exact
  default branch with no tags, never a repository/organization secret. Both
  privileged jobs select this environment; no PR validation job does.
  `GITHUB_TOKEN` and GitHub App installation tokens cannot assign Copilot.
  Rotation must retain the **same user owner**: ledger provenance is bound to
  the PAT owner. A different-owner migration is deliberate manual work, never
  an automatic token swap.
- Runtime state is a versioned, controller-owned tracker comment with explicit
  root/stage/task/issue/PR links and persisted transition intent. No state commits
  to the default branch. All control runs share repository-wide concurrency
  serialization with `cancel-in-progress: false`; comments alone are not locks.
- One pipeline and one active task PR at a time. Agents never mutate the
  controller ledger. Reconciliation re-fetches API state and recovers partial
  writes instead of blindly recreating resources.
  Each run is limited to **100 tasks** to keep the durable comment bounded.
- An agent blocked on missing material requirements posts a comment starting
  `SDLC_BLOCKED:` on its **assignment issue or PR**. The controller recognizes
  bot/writer comments and pauses. After resolving, a writer must post a later
  comment starting `SDLC_UNBLOCKED:` on the **same assignment issue or PR**,
  then manually resume. Resume alone never clears blocker evidence;
  deleting labels or editing the ledger is not proof of resolution.
- A stage PR must have the footer `Closes #<assigned issue>` using its real
  number. PR discovery uses API **closing-issue references only**, then verifies
  bot author, same repository and expected base. Arbitrary body mentions,
  titles, labels, newest timestamps and manual closure are not identity proof.
- Only verified merged PRs advance; dependencies require merged evidence.
  Before advancing, the controller also requires an actual current-head
  Copilot PR review from the review API, not internal cloud-agent self-review
  or a stale review from a previous head.
  Agents must not close triggering issues manually. The controller owns
  completion; the root brief/tracker is not done just because one issue closes.

## Phase order and outputs

| Phase | Custom agent | Required work |
| --- | --- | --- |
| requirements | 1-requirement-agent | Preserve `docs/requirements/application-brief.md`; produce `docs/requirements/BRD.md` |
| design | 2-plan-and-design-agent | `docs/design/HLD.md`, `docs/design/LLD/*.md`, justified architecture/stack decision |
| backlog | 3-epic-and-tasks-agent | Epics/stories/tasks and canonical dependency manifest |
| plan | 3.5-build-orchestrator-agent | Run planner, commit deterministic `backlog/execution-plan.md` and `backlog/waves.json` in its own assigned PR |
| bootstrap | 4-develop-agent | Real application toolchain, CI/scanners/setup/Dependabot configuration |
| TASK-xxx | 4-develop-agent or 5-ui-develop-agent | One explicit implementation/frontend task and its tests |
| qa | 6-automation-test-agent | Requirement-level tests and `docs/testing/TestPlan.md` |
| security | 7-security-agent | Remediation/tests, findings JSON, `docs/testing/security-review.md` |
| completed | controller | Verify merges, final artifacts, passing gates and no blocking findings |

## Canonical task manifest

`backlog/dependency-graph.json`:

```json
{
  "version": 1,
  "tasks": {
    "TASK-001": {
      "title": "A bounded, requirement-derived deliverable",
      "type": "implementation",
      "dependencies": [],
      "requirements": ["BRD-FR-001"],
      "acceptance_criteria": ["A specific observable outcome is verified."]
    }
  }
}
```

The only types are `implementation` (4-develop-agent) and `frontend`
(5-ui-develop-agent). IDs match `TASK-` plus at least three digits; each has a
`backlog/tasks/<ID>.md` file. Requirements and acceptance criteria are nonempty.
Dependencies are unique known IDs, without self edges or cycles. No alternative
`depends_on` field, inferred routing, curated wave assignments or mutable wave
state is accepted.

`python scripts/compute-waves.py` defaults to that manifest and writes
`backlog/waves.json` plus `backlog/execution-plan.md`. The same input produces
the same artifacts; every task appears exactly once in stable topological waves.
`python scripts/compute-waves.py --check` validates manifest and deterministic
artifacts **without edits**. Waves are advisory planning output, not runtime
dispatch state; the controller checks actual prerequisite merges.

## Application toolchain

`.github/sdlc/toolchain.json` defaults:

```json
{
  "version": 1,
  "configured": false,
  "languages": [],
  "source_roots": [],
  "runner": "ubuntu-latest",
  "commands": {
    "setup": [],
    "build": [],
    "lint": [],
    "typecheck": [],
    "test": [],
    "security": []
  },
  "not_applicable": {},
  "test_report": null
}
```

Bootstrap sets configured true, nonempty language strings and repository-relative
source directories, and runner to `ubuntu-latest`, `windows-latest` or
`macos-latest`. Each commands value is a list of argv arrays, for example
`[["chosen-tool", "argument"]]`, **not** a shell command string. Setup may be
empty. Lint, test and security commands must be nonempty. Build and typecheck
commands are required unless `not_applicable.build` or
`not_applicable.typecheck` contains a substantive rationale respectively.
Do not copy the illustrative tool name as a real gate.
Application source roots must not be template-owned directories.
`test_report` is null only while unconfigured. A configured application requires
an object such as `{"path":"test-results/junit.xml","minimum_tests":1}`: a
repository-relative `.xml` path and positive integer minimum selected from
design expectations. Before the test gate, the runner removes **only that stale
report**, then requires newly produced JUnit `testcase` elements, no failure or
error elements, and at least `minimum_tests` **non-skipped** tests. A successful
exit with zero tests, a stale report or echo-only command does not pass.

`python scripts/toolchain.py --gate <gate>` supports `setup`, `build`, `lint`,
`typecheck`, `test`, `security`, `all`, `validate`. It runs reviewed argv via
subprocess without issue-derived shell interpolation. Template validation is
`python scripts/check.py`; automation tests are
`python -m unittest discover -s tests -v`.

Template-only mode is allowed only without application files outside documented
template-owned paths: `.github/`, `scripts/`, `tests/`, `templates/`, `docs/`,
`backlog/`, plus root template documentation/configuration. These locations are
not hiding places for application code. Root package manifests, application
source, or other application files require the configured contract; CI must
fail unconfigured application additions. Bootstrap records actual roots and
application test locations, extends coverage and retains template checks.

## Security findings

`docs/security/findings.json`:

```json
{
  "version": 1,
  "findings": [
    {
      "id": "SEC-001",
      "severity": "medium",
      "status": "open",
      "description": "An actual assessed finding."
    }
  ]
}
```

IDs are stable unique finding IDs. Severity is `critical|high|medium|low|info`;
status is `open|fixed|accepted`. All open findings block completion.
Critical/high cannot be accepted. Lower accepted findings need a writer's
explicit decision and rationale in `acceptance_reason` and the review document,
plus `accepted_by` (the writer's login) and
`decision_url=https://github.com/OWNER/REPO/issues/N#issuecomment-ID` using the
actual repository, numeric issue and comment IDs. The controller verifies the
linked writer comment includes exact `Accept risk SEC-xxx` for that finding's
actual ID. A fabricated URL or agent self-acceptance is not evidence.
An empty array requires actual review evidence; do not predeclare a clean scan.

## Repair and required checks

Repair uses user-token `@copilot` comments on verified pipeline PRs. Current-head
feedback/check identity deduplication prevents stale or repeated repairs.
The limit is **three total repair attempts per PR across all head SHAs**, not
three per push. Exhaustion applies `sdlc:needs-human`; a writer must explicitly
resume after resolving the blocker. Resume is not evidence the underlying
problem is fixed.

Intended baseline required checks are `Template checks`, `Application checks`,
`Dependency policy`, `Code scanning policy`. **Verify actual emitted names in
the first smoke PR before creating a ruleset.** When CodeQL is enabled,
`Code scanning policy` aggregates **all** CodeQL matrix results. Add observed
language checks to rules as appropriate after bootstrap. False CodeQL runs
explicit alternative Ruff S analysis of template Python plus configured
application security commands, with `docs/code-scanning-policy.md` required.
Never imply template Python checks scan arbitrary application languages.
The fallback policy jobs do not run application commands on hardcoded Ubuntu:
`Dependency policy` validates documented selection and the toolchain contract;
false-CodeQL `Code scanning policy` runs template Ruff S and validates the
contract. Required **`Application checks`** executes the actual configured app
security/advisory commands on the selected application runner. Application
execution evidence belongs to that check.

Dependabot includes GitHub Actions and known Python template tooling in
`/scripts`; bootstrap adds actual application ecosystems. The initial
dependency alternative covers pip tooling and Actions controls in
`docs/dependency-policy.md`; configured applications also require real advisory
scanning in the mandatory application security command.
