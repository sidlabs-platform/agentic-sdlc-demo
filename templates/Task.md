# Task: [Title]

| Field | Value |
| --- | --- |
| Task ID | TASK-001 |
| Story / Epic | STORY-001 / EPIC-001 |
| Type | implementation or frontend |
| Status / Estimate | [Values; delivery requires verified merge] |
| BRD / Component | BRD-FR-001 / COMP-001 |

## Description & Scope
[One bounded deliverable, why it is needed and explicit exclusions.]

## Implementation Details
[Files to create/modify under design-selected roots; relevant LLD sections,
approach, compatibility and constraints the assigned developer needs.]

## Interface / API Changes
[Operations, request/response examples, authentication, errors and versioning,
or N/A with reason.]

## Data Model Changes
[Schema/index/migration and rollback implications, or N/A with reason.]

## Dependencies
| Prerequisite task | Reason / consumed interface |
| --- | --- |
| [Known TASK ID, or None] | [Reason] |

Keep these identical to the manifest's `dependencies` array. No curated waves,
`depends_on` field, fixed branches or issue-closure completion claims.

## Acceptance Criteria
- [ ] [Nonempty, specific, testable outcome matching the manifest]
- [ ] [Relevant failure/boundary outcome]

## Test Requirements
[Unit, interface/integration, applicable UI/accessibility, security and
regression cases; fixtures and exact configured validation commands.]

## Parent References
[Story, epic, BRD and HLD/LLD links.]

## Routing & Definition of Done
`implementation` → 4-develop-agent; `frontend` → 5-ui-develop-agent.
IDs use `TASK-` plus at least three digits; a matching
`backlog/tasks/<ID>.md` must exist for each canonical manifest entry.
The complete run must contain at most 100 tasks.

- [ ] Only assigned scope implemented; actual prerequisites merged
- [ ] Tests, lint, build/typecheck where applicable, and security gates pass
- [ ] Acceptance evidence and documentation recorded
- [ ] Single platform-owned PR has `Closes #<assigned issue>` footer
- [ ] Human review/merge complete; do not close the triggering issue manually
