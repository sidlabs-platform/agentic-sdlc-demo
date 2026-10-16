# Operations and recovery

## Normal operation

The root brief issue is the durable entry point. A writer applies `sdlc:start`.
The controller maintains a structured tracker comment; agents preserve the
brief in versioned requirements docs and submit each stage in a platform-owned
PR. One active pipeline and one active task PR simplify safe ordering. Additional
briefs queue; do not manually assign the queued pipeline to force parallel work.
Each run is limited to 100 tasks so its durable comment ledger remains bounded.
Resolve excessive scope explicitly rather than truncating the backlog.

The controller runs on issue opened/labeled/edited/reopened events,
`pull_request_target` opened/edited/closed/synchronize, every 15 minutes, and
manual dispatch. Control runs serialize in one repository-wide concurrency
group with `cancel-in-progress: false`. Scheduled reconciliation repairs
missed/coalesced events; schedules can be delayed, disabled for inactivity or
limited by Actions availability. A timer is not a delivery-time guarantee.

Review PR acceptance evidence and actual checks, mark drafts ready if the
platform requires it, and merge manually. GitHub Copilot's built-in self-review,
native repository review and required checks are different mechanisms.
Before advancing, the controller requires a current-head Copilot PR review
verified via the actual review API; internal self-review and stale-head reviews
do not satisfy this requirement.
No auto-approve/auto-merge is supplied. Closed issues or closed-unmerged PRs
do not unlock dependents.

## Labels and manual controls

| Label | Meaning |
| --- | --- |
| `sdlc:start` | Writer-authorized kickoff candidate |
| `sdlc:managed` | Controller-managed pipeline work |
| `sdlc:needs-human` | Explicit blocker or exhausted repair requires a writer |
| `sdlc:paused` | Pipeline intentionally halted |
| `sdlc:complete` | Controller verified final completion |

Use Actions → **SDLC Controller** (`.github/workflows/sdlc-controller.yml`) →
Run workflow, set `action` to `reconcile`, `pause` or `resume`, and set
`root_issue` to the root issue's numeric ID (not a task/PR number).
Only a trusted writer may recover a blocked pipeline. Labels indicate state;
editing/removing a label or manually editing the tracker is not a safe repair.
For missing material requirements, agents post a comment starting
`SDLC_BLOCKED:` on their **assignment issue or PR**, not only on the root
tracker. The controller recognizes bot/writer comments and pauses. A writer
answers/resolves the decision and posts a **later writer comment starting
`SDLC_UNBLOCKED:` on the same assignment issue or PR**, then manually resumes.
Resume alone cannot clear blocker evidence; label removal is not resolution.

- **reconcile:** refresh API evidence and recover pending transitions without
  pretending a blocked decision is resolved.
- **pause:** stop future dispatch for that pipeline. It does not cancel an
  already running cloud-agent session or shell/Actions run.
- **resume:** explicit writer recovery after inspecting and resolving the
  blocker; does not prove requirements, security findings or checks are fixed.
  A requirements blocker also requires the later same-assignment
  `SDLC_UNBLOCKED:` writer comment before manual resume.

Do not rewrite ledger history, reset retry counters by pushing a new commit,
or create duplicate stage issues/PRs. Inspect the workflow summary, ledger links
and live issue/PR/check state first.

## Feedback and retry budget

The controller posts actionable `@copilot` repair comments using the user PAT,
only on verified same-repository pipeline PRs. It deduplicates feedback/check
identity on the current head and ignores stale checks/reviews. There are
**three total attempts per PR across every head SHA**. A new push is not a new
budget. Exhaustion applies `sdlc:needs-human` and halts dependent dispatch until
a writer explicitly resumes. Do not rely on an autonomous infinite repair loop.

After exhaustion, `resume` does **not** authorize a fourth automatic repair.
Resolve the failures yourself or send a deliberate manual `@copilot` request,
obtain fresh passing checks and current-head review, then resume. Resuming a
still-failing PR will block again; the lifetime budget is intentionally retained.
If an assigned PR was closed unmerged, reopen that original PR before resuming.
A replacement PR requires deliberate state migration, not label or title edits.

## Troubleshooting

| Symptom | Inspect / safe response |
| --- | --- |
| No kickoff | Writer authority, start label, exact `SDLC_ENABLED=true`, Actions enabled, active/queued pipeline |
| Assignment failed | PAT type/expiry/approval/repository scope, Copilot access, current API; issue creation is not assignment success |
| PR not linked | Actual closing-issue API reference from footer, bot author, repository and expected base; title or mention alone is insufficient |
| Duplicate/missing event | Reconcile; allow persisted transition intent/resource recovery before creating replacements |
| PR closed without merge | Blocked, not delivered; have a writer inspect and recover explicitly |
| Failed current-head checks | Read logs, fix real failures; do not weaken rules or use stale green checks |
| Missing/failed automatic review | Repository review settings, draft/new-push options, account policy; self-review is not equivalent |
| Stage waiting on draft readiness | Requesting human marks ready as required by the platform |
| Bootstrap fails | Runtime installation, runner, argv commands, nonempty gates, build/typecheck rationale and source roots |
| Security cannot complete | Fix open/high/critical findings; lower acceptance needs reason, writer identity and verified issue-comment decision |
| Policy check fails before scan | Both entitlement variables must be exact true/false; required alternative policy docs and controls must exist |
| Unrelated/fork PR rejected | Expected trust boundary; do not relax provenance checks |
| Schedule absent / timeout | Actions status, billing, runner availability, disabled schedules; explicit reconcile after root cause resolution |

Never run PR code or download/execute its artifacts in privileged recovery.
Metadata-only `pull_request_target` control uses trusted default-branch code.
Validation remains secret-free for forks and Dependabot.

## Token lifecycle, incidents and cost

Before expiry, pause dispatch, create a replacement fine-grained user PAT with
the documented permissions **owned by the same user**, update `SDLC_TOKEN` in
the default-branch-only `sdlc-control` environment, confirm organization approval,
then reconcile/resume and revoke the old token after verifying recovery.
Ledger provenance uses the PAT owner's identity. A different-owner migration
requires deliberate manual review/recovery; it is not an automatic token swap.
Never print either token. For exposure, revoke immediately, disable dispatch
(`SDLC_ENABLED` not true), inspect audit/Actions logs and affected branches,
rotate related credentials, then recover explicitly.

Monitor cloud-agent requests, Actions minutes/storage, security-product charges
and organization budgets. Assignment permission, account access or API behavior
may change independently of repository files. Timeouts/platform failures are
visible blockers, not permission to bypass checks.

Completion requires merged QA/security artifacts and passing final gates, with
no open or illegally accepted security findings. A green mocked test suite
does not establish a live deployment or universal scanner coverage.
Accepted findings require `acceptance_reason`, `accepted_by` and a real
`decision_url=https://github.com/OWNER/REPO/issues/N#issuecomment-ID`. The
controller verifies a writer comment containing exact `Accept risk SEC-xxx`
for the finding's actual ID. See [contracts](contracts.md#security-findings).
