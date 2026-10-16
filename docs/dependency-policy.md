# Dependency policy and entitlement alternative

Set repository variable `SDLC_REQUIRE_DEPENDENCY_REVIEW` to exact `true` or
`false`. Unset, misspelled or other values fail policy validation. Prefer
`true` when the repository is entitled: PR dependency review must complete
successfully under the configured vulnerability policy.

When it is `false`, this policy is required and describes the baseline
alternative; absence of entitlement is not a clean vulnerability scan.

## Template baseline: Python tooling and Actions

- Template Python tooling is declared in `scripts/requirements-checks.txt`.
  Keep direct/transitive resolved requirements pinned and use verified hashes
  with `python -m pip install --require-hashes -r scripts/requirements-checks.txt`.
  Review package identity, version changes, provenance and upstream advisories
  before merging updates. Hash verification establishes artifact integrity,
  **not** absence of vulnerabilities.
- Every PR also runs `scripts/audit-template-deps.py`, querying GitHub's public
  advisory database for the explicitly pinned tooling packages (including the
  runtime requirements include). It fails on non-withdrawn advisories above
  low severity or unknown severity, and fails visibly on API/network errors.
  This uses the job's ephemeral read-only `GITHUB_TOKEN`, never `SDLC_TOKEN`
  or repository secrets. It audits template Python dependencies, not arbitrary
  application manifests or the internals of pinned Actions.
- Dependabot includes the known Python tooling ecosystem in `/scripts` and
  `github-actions`. Keep the requirements path compatible with its configured
  directory and verify update discovery in the adopter repository. Enable
  dependency graph/alerts/security updates where entitled; do not assume
  Dependabot covers vendored or undeclared dependencies.
- Pin external Actions to reviewed immutable full commit SHAs. On updates,
  verify upstream release/commit provenance, changes, permissions and security
  advisories. Template workflow validation checks immutable pinning; pinning
  alone is not an Actions vulnerability scanner.
- Review dependency changes manually with the same required secret-free CI.
  Check current package/Action advisories and record relevant results or risk
  decisions in the PR. Do not auto-merge Dependabot changes or rely on secrets
  unavailable to Dependabot/fork runs.
- Address critical/high vulnerabilities before completion. Any lower-severity
  residual-risk acceptance follows the explicit writer-comment evidence
  contract; a green install or Dependabot's silence is not acceptance.

These are concrete template tooling integrity/update/review controls, not a
claim that this baseline automatically runs a universal dependency scanner.
If upstream advisory access or entitlement is unavailable, record the gap and
resolve it rather than reporting an unperformed scan as clean.

## Application bootstrap is mandatory

Before application feature work, bootstrap must inventory actual manifests and
lockfiles, add each application ecosystem/directory to Dependabot and configure
**real application advisory scanning** in the mandatory nonempty
`.github/sdlc/toolchain.json` `commands.security` gate. Select scanners covering
the actual languages/package managers, define the vulnerability/failure policy,
and test the gate on clean runners. Ordinary PR checks remain secret-free.

When dependency review is false, these advisory scans are the mandatory
application alternative, not optional documentation. When true, they complement
dependency review and the application's wider security checks. Static code
analysis (including Ruff S or CodeQL) does not by itself replace dependency
advisory scanning.
The fallback **`Dependency policy`** job checks the documented selection and
toolchain contract; it does not execute app commands on hardcoded Ubuntu.
Required **`Application checks`** runs actual app security/advisory commands on
the selected application runner. Look there for application execution evidence.

## Administration and evidence

Recheck entitlement on repository transfers, visibility or plan changes.
Keep the stable `Dependency policy` check required after verifying its actual
emitted name. Record manifests reviewed, tool/version, advisory data freshness,
results, exclusions and remediation in stage/PR evidence. See
[setup](setup.md), [adaptation](adapting.md) and
[findings acceptance](contracts.md#security-findings).
