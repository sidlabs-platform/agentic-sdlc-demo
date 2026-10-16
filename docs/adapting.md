# Adapting the template to an application

## Select, do not assume, a stack

The requirements/design stages derive the product from the issue. Record the
architecture/stack decision, language/runtime versions, package manager,
source/test layout, supported OS, integrations and quality expectations in
`docs/design/HLD.md` and LLDs. Python remains template tooling even if the
application uses another language. Do not hardcode a model/provider/domain.

The planner generates deterministic advisory waves. The **bootstrap** PR then
establishes executable tooling before any individual feature task is dispatched.

## Bootstrap checklist

1. Configure `.github/sdlc/toolchain.json` using the exact
   [contract](contracts.md#application-toolchain): version 1; configured true;
   nonempty `languages` and repository-relative directory `source_roots`;
   runner `ubuntu-latest`, `windows-latest` or `macos-latest`.
   Application source roots must not be template-owned directories.
2. Set `commands.setup`, `build`, `lint`, `typecheck`, `test`, `security` to
   lists of executable argv arrays. Setup can be empty. Lint/test/security
   cannot be empty; tests must actually execute tests. Build/typecheck need
   commands or substantive `not_applicable.build` /
   `not_applicable.typecheck` rationale. Do not hide failures or use shell
   fragments copied from issues. Keep scripts checked in and reviewable.
   Change unconfigured `test_report: null` to an object such as
   `{"path":"test-results/junit.xml","minimum_tests":1}`. Use a repository-relative
   `.xml` path and a positive minimum chosen from the design. Tests must freshly
   produce JUnit `testcase` elements without failures/errors and at least that
   many non-skipped cases. The runner removes only the designated stale report;
   zero-test/echo-only success fails.
3. Add manifests/lockfiles and a runnable application/test foundation. Record
   real source roots. Template-only mode permits only template-owned content
   under `.github/`, `scripts/`, `tests/`, `templates/`, `docs/`, `backlog/`
   and root template documentation/configuration; it is not a waiver for
   application files in those locations. Adding application files without a
   configured contract must fail. Application source should use clearly
   declared, distinct roots rather than masquerading as template tooling.
4. Install runtime/tool versions and dependencies in both application CI and
   `.github/workflows/copilot-setup-steps.yml`. Use the special job name
   **`copilot-setup-steps`** and supported customization keys. A failed setup
   does not guarantee the cloud agent stops: agent instructions and CI gates
   must still enforce actual validation.
5. Keep `python scripts/check.py` and
   `python -m unittest discover -s tests -v` as template coverage. Application
   CI runs `python scripts/toolchain.py --gate all` after installing runtime
   prerequisites; do not confuse template test success with app test success.
6. Require `SDLC_CODEQL_ENABLED` to be exact `true` or `false`; unset fails.
   Prefer true where entitled and extend `.github/workflows/codeql.yml` with supported application
   languages, runner/build mode and setup. Retain Python automation coverage.
   Unsupported languages require a real alternative scanner in the mandatory
   security gate. Verify every matrix result and add observed names to branch
   protections as appropriate; the stable required `Code scanning policy`
   aggregates **all** enabled CodeQL matrix results. False requires
   `docs/code-scanning-policy.md` and runs Ruff S template-Python analysis plus
   contract validation. Required `Application checks` executes configured app
   security/advisory commands on the selected app runner; fallback policy jobs
   do not execute app commands on hardcoded Ubuntu. Ruff does not scan arbitrary app
   languages; do not assert universal coverage.
7. Keep `Dependency policy` meaningful. Set
   `SDLC_REQUIRE_DEPENDENCY_REVIEW` to exact true or false; unset fails. Use true
   where entitled; false requires `docs/dependency-policy.md`. Bootstrap a
   dependency/advisory scanner and documented vulnerability policy into
   `commands.security`, in addition to appropriate code-security tooling.
8. Extend `.github/dependabot.yml` from its GitHub Actions and Python tooling
   `/scripts` baseline to actual
   ecosystems, directories, schedules and lockfiles. Run the same CI for
   Dependabot/fork PRs without secrets; keep merging manual.
9. Update accepted project conventions and local developer commands. Validate
   a clean runner with no local cache, credentials or production service
   dependency. Record setup/build/lint/typecheck/test/security evidence.

Run individual gates with `python scripts/toolchain.py --gate <gate>`; supported
gates are setup/build/lint/typecheck/test/security/all/validate.

## Scanner and repository administration limits

File changes do not enable paid security products or configure settings.
Check public/private entitlement for CodeQL/code scanning, dependency review,
secret scanning and push protection. Configure secrets, variables, labels,
review settings, rulesets and environments separately in every adopter
repository. See [setup](setup.md).

## Extending lifecycle contracts

Update agent prompts, templates, validators, schema, controller consumers and
tests together. Task routing remains declared `implementation`/`frontend`;
no language/file-path heuristic or `depends_on` alias. Do not turn waves into
runtime state or allow tasks to bypass merged prerequisites.

Deployments remain disabled until a provider, environment protections, OIDC
trust, health checks and rollback procedure are explicitly configured.
See [deployment interface](deployment.md).
