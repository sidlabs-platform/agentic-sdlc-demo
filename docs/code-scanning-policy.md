# Code-scanning policy and entitlement alternative

Set repository variable `SDLC_CODEQL_ENABLED` to exact `true` or `false`.
Unset or any other value fails policy validation. **Recommend `true` where
CodeQL is entitled** for the target repository visibility/plan.

The stable required **`Code scanning policy`** check represents the selected
policy. Verify actual check names during the first smoke PR before ruleset
configuration. This check must not report success merely because one selected
matrix job passed or an unavailable scanner was skipped.

## CodeQL enabled (`true`)

This uses the repository's **advanced setup** workflow (`codeql.yml`). If
CodeQL **default setup** is enabled on the repository (often by organization
security configuration), switch it to advanced setup first under
**Settings → Code security → Code scanning**; GitHub rejects advanced-setup
uploads while default setup is active. Organization security configurations
may re-apply default setup to new repositories, so verify this per repository.

Run the CodeQL language matrix and aggregate **all matrix results** into
`Code scanning policy`. The baseline analyzes template Python automation.
Bootstrap explicitly adds supported application languages and appropriate
runtime/build-mode/setup configuration while retaining Python tooling coverage.
Validate every matrix entry; a Python result does not scan other languages.

Add observed per-language CodeQL checks to rules as appropriate after extending
the matrix; keep the stable aggregate required so a failed matrix entry cannot
be hidden. Unsupported application languages still require a suitable
alternative in the application's mandatory security command. Entitlement
failure is a configuration blocker, not permission to silently skip analysis.

## CodeQL disabled (`false`)

This policy document is required. The fallback `Code scanning policy` job runs
**Ruff S security analysis on template Python** and validates the toolchain
contract. It does **not** execute app commands on hardcoded Ubuntu. Required
**`Application checks`** executes the configured application's security/advisory
commands on its selected runner, including Windows/macOS when selected.
Application security execution evidence is in that check. Retain ordinary
template lint, tests and workflow/contract validation as complementary controls.

Ruff S is a Python security-rule set with limited static-analysis coverage;
it does not scan arbitrary application languages, replace CodeQL's analyses,
prove exploit absence or perform dependency advisory scanning. Bootstrap
chooses and configures real code-security tooling for the application's
languages and also the dependency advisory scanning required by
[dependency policy](dependency-policy.md). A nonempty command must execute
meaningful checks, not just an echo or template lint.

Application source requires a configured toolchain with non-template source
roots and mandatory security commands. False CodeQL is not a waiver to add
unscanned application code or misrepresent template-only success as application
validation. Keep CI secret-free for ordinary and Dependabot/fork PRs.

## Evidence and exceptions

Record actual source/language scope, tools/versions, command results, known
limitations and remediation in the security review. Do not claim that disabled
or unlicensed features ran. Findings follow the canonical record and writer
acceptance evidence contract; all open findings block completion and
critical/high cannot be accepted.

Reassess this choice after language, repository visibility, plan or provider
changes. A writer/admin deliberately changes the exact variable and updates
configuration and protections; agents must not turn a scanner off to pass CI.
