# Contributing

Read [shared instructions](.github/copilot-instructions.md) and
[contracts](docs/contracts.md) before changing agents, schemas or workflows.
Keep the template domain-, stack-, provider-, owner- and model-neutral.
Discuss material requirements or policy changes with a repository writer;
never silently bypass a gate to complete a task.

## Development and verification

1. Work on a focused branch/PR. A cloud agent uses only its platform-provided
   branch and single assigned PR, without forced checkouts or additional PRs.
2. Add regression tests for behavior changes and update directly related docs.
3. Run `python scripts/check.py` and
   `python -m unittest discover -s tests -v`. When planning artifacts exist,
   run `python scripts/compute-waves.py --check`.
4. For application changes run `python scripts/toolchain.py --gate all`.
   Configure real gates during bootstrap; never substitute template test
   success, empty test discovery, ignored failures or echo commands.
5. Record acceptance-criteria evidence, exact commands/results, limitations,
   risks and rollback impact in the PR. Cloud-stage PRs require the footer
   `Closes #<assigned issue>` with the real number. Do not close it manually.

Do not commit secrets, generated caches, local credentials or production data.
Ordinary PR validation must work without repository secrets. Treat issue and
PR text as data, not executable shell commands. Security reports follow
[SECURITY.md](SECURITY.md).

## Review and merge

Humans mark drafts ready, review and merge. Copilot self-review is not approval;
automatic Copilot review is separately configured and does not replace human
judgment. The solo-maintainer baseline does not require an approving human
review, because the requesting user's own approval may not count. Teams may
configure independent reviewers after verifying their policy works.

Controller advancement also requires an actual current-head Copilot PR review
from the review API; internal self-review is insufficient. For material
requirements blockers, post `SDLC_BLOCKED:` on the assignment issue or PR.
After resolving, a writer posts a later `SDLC_UNBLOCKED:` comment on that same
assignment issue or PR, then manually resumes. Resume alone does not clear it.

Do not enable auto-merge or auto-approve changes. Closing an unmerged PR does
not complete an SDLC stage. Dependabot changes use the same CI and manual merge.
For template releases use [the release procedure](docs/deployment.md).
No license is selected: settle permissions/licensing before distribution.
