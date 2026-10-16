# A small end-to-end example

This is an illustration of the process, not a preset product or stack.

## Brief

A writer creates an Application brief issue: “Let an authenticated member create
and view their own saved notes. Do not share notes publicly. A keyboard-only
user must complete the journey. Start with local execution; hosting is undecided.”
The writer supplies the required data-retention and authentication constraints
or answers the requirements agent's blocking questions, then labels `sdlc:start`.

## Ordered artifacts and human merges

1. Agent 1 preserves the original brief and produces requirements such as
   `BRD-FR-001` (create/view owned notes) and a testable accessibility NFR.
   A human reviews and merges the requirements PR.
2. Agent 2 chooses a stack with rationale, documents authorization/data
   boundaries and writes component LLDs. No language is predetermined.
3. Agent 3 creates epics/stories/task docs and a manifest; for example:

```json
{
  "version": 1,
  "tasks": {
    "TASK-001": {
      "title": "Implement owned-note persistence and interface",
      "type": "implementation",
      "dependencies": [],
      "requirements": ["BRD-FR-001"],
      "acceptance_criteria": ["A member can save and retrieve only their own notes."]
    },
    "TASK-002": {
      "title": "Build the accessible note interface",
      "type": "frontend",
      "dependencies": ["TASK-001"],
      "requirements": ["BRD-FR-001"],
      "acceptance_criteria": ["The member can save and view a note using only the keyboard."]
    }
  }
}
```

Actual backlog detail must cover all accepted requirements, authorization
foundation and NFRs; this shortened manifest only illustrates routing/ordering.
Both task files must exist; no `depends_on` alias or hand-edited waves.

4. Agent 3.5 runs `python scripts/compute-waves.py`, verifies `--check`, and
   commits both generated planning artifacts in its assigned PR. Human merge.
5. Agent 4 bootstraps the selected runtime, toolchain, CI, real tests/scanners
   and Dependabot ecosystems. Human reviews evidence and merges.
6. The controller assigns TASK-001 to agent 4. Only after its PR is verified
   merged does TASK-002 go directly to agent 5. Every PR ends with the actual
   `Closes #<assigned issue>` footer; no textual downstream dispatch.
7. Agent 6 adds requirement-level ownership/keyboard/error-flow tests and the
   TestPlan. Agent 7 reviews/remediates security with tests and records findings.
   Humans merge both PRs only after evidence is acceptable.
8. The controller verifies all final gates/artifacts and no open findings,
   then marks completion. No deployment occurs.

If a task PR closes unmerged, the next task does not start. If repair exhausts
three attempts, a writer resolves the blocker and explicitly resumes through
SDLC Controller. For a material-requirements blocker, the writer first adds a
later `SDLC_UNBLOCKED:` comment on the same assignment issue or PR; resume alone
does not clear it. A second brief remains queued rather than creating competing
active task PRs.
