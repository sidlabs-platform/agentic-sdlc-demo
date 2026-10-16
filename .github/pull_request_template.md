## Summary and assignment

<!-- Identify stage/task, root tracker and assigned issue. Titles are not identity. -->

## Artifacts and acceptance evidence

<!-- Map requirements/task criteria to changed files and verified results. -->

## Validation

<!-- Exact commands/results, including failures, skipped checks and limitations.
Template: python scripts/check.py
Template automation: python -m unittest discover -s tests -v
Planning artifacts when present: python scripts/compute-waves.py --check
Application: python scripts/toolchain.py --gate all -->

## Risks, security and recovery

<!-- Configuration/dependency changes, findings, migrations and rollback.
Do not include secrets. Open findings block completion; high/critical cannot
be accepted. Lower risk acceptance needs an explicit writer decision/rationale. -->

<!-- Accepted findings also require accepted_by and an actual decision_url:
https://github.com/OWNER/REPO/issues/N#issuecomment-ID. The writer comment must
include exact "Accept risk SEC-xxx" using the actual finding ID. Missing
material requirements: post a separate comment starting SDLC_BLOCKED: on this
assignment PR or issue; a body note alone does not signal the controller. -->

## Human review

- [ ] Scope and acceptance evidence reviewed
- [ ] Required checks pass on the current head
- [ ] No unresolved blockers or unauthorized risk acceptance
- [ ] Mark ready and merge manually; no auto-approval or auto-merge

<!-- For a managed cloud-agent assignment, replace the number placeholder below
with its actual assigned issue. A tracker mention alone is not a closing
reference. Do not close the triggering issue manually or add closing keywords
for unrelated issues. Non-managed contributions may remove the placeholder. -->

Closes #<assigned issue>
