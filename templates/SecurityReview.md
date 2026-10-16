# Security Review — [Application]

| Field | Value |
| --- | --- |
| Version / Date / Reviewer / Status | [Values] |
| BRD / HLD / LLD / Reviewed commit | [References] |

## 1. Review Scope & Methods
[Actual source roots, interfaces, frontend, configuration, workflows,
dependencies and infrastructure reviewed; exclusions, tools/versions, commands,
results and licensing/coverage limitations. Unrun scanners are not clean scans.]

## 2. Threat Model Summary
[Assets/sensitivity, threat actors/capabilities, data flows and trust-boundary
diagram. Include application integrations and CI/token boundaries.]

## 3. OWASP Top 10 Assessment
Document the OWASP edition used; update categories when using a later edition.

| Category (2021 reference) | Applicability / evidence | Finding / control |
| --- | --- | --- |
| A01 Broken Access Control | [Assessment] | [Reference] |
| A02 Cryptographic Failures | [Assessment] | [Reference] |
| A03 Injection | [Assessment] | [Reference] |
| A04 Insecure Design | [Assessment] | [Reference] |
| A05 Security Misconfiguration | [Assessment] | [Reference] |
| A06 Vulnerable and Outdated Components | [Assessment] | [Reference] |
| A07 Identification and Authentication Failures | [Assessment] | [Reference] |
| A08 Software and Data Integrity Failures | [Assessment] | [Reference] |
| A09 Security Logging and Monitoring Failures | [Assessment] | [Reference] |
| A10 Server-Side Request Forgery | [Assessment] | [Reference] |

## 4. Interface, Frontend & Data Security
[Authentication/session expiry, authorization/tenant isolation, input schemas,
output escaping, injection, traversal, CSRF/CSP as applicable, request limits,
rate limiting, errors, logging and storage/transmission/retention controls.]

## 5. Secret Management & CI
[No embedded/client-exposed/logged secrets, ignored local env files, credential
scope/rotation, trusted control vs untrusted validation, permissions and OIDC.]

## 6. Dependency & Scanner Security
[Manifests/lockfiles, advisories, Dependency policy evidence, CodeQL actual
language coverage/build mode or alternative scanner, Dependabot ecosystems.
Do not imply unavailable security features are enabled.]

## 7. Findings Summary & Machine-readable Record
| Finding | Severity | Description / component / BRD ID | Remediation / tests | Status / evidence |
| --- | --- | --- | --- | --- |
| SEC-001 | [critical/high/medium/low/info] | [Issue] | [Action] | [open/fixed/accepted] |

Write `docs/security/findings.json` exactly as:

```json
{
  "version": 1,
  "findings": [
    {
      "id": "SEC-001",
      "severity": "low",
      "status": "accepted",
      "description": "Describe a real, assessed residual risk.",
      "acceptance_reason": "Explicit rationale for this actual residual risk.",
      "accepted_by": "WRITER_LOGIN",
      "decision_url": "https://github.com/OWNER/REPO/issues/N#issuecomment-ID"
    }
  ]
}
```

This is an illustration, not a pre-accepted finding. Use stable unique IDs.
Every open finding blocks completion. Critical/high cannot be accepted.
Lower-severity acceptance requires a writer's explicit decision and rationale;
record it here and in `acceptance_reason`, with the writer's login in
`accepted_by` and the real issue-comment URL in `decision_url`. The controller
verifies the linked writer comment includes exact text `Accept risk SEC-xxx`
using the finding's actual ID. Replace illustrative URL/login placeholders;
do not invent evidence or treat a PR review URL as an issue-comment URL.
Fix findings with tests in this PR
where practical. An empty array requires actual assessment evidence.

## 8. Recommendations & Completion Decision
[Immediate remediation, follow-up hardening, ownership and deadlines.
Distinguish blockers from recommendations. Do not report completion while open
findings, unaccepted risk, or failed required gates remain.]

## 9. Traceability & Retest Evidence
[Finding → component → BRD NFR → remediation/test mapping, exact results and
remaining limitations. Final completion is controller-verified after merge.]
