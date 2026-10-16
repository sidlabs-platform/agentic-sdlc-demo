# Test Plan — [Application]

| Field | Value |
| --- | --- |
| Version / Date / Author / Status | [Values] |
| BRD / Design reference | [Accepted versions] |

## 1. Test Scope & Objectives
[Capabilities and requirements covered, exclusions and rationale, measurable
quality/coverage objectives derived from the accepted requirements.]

## 2. Test Strategy
| Category | Scope | Framework / method | External dependency isolation |
| --- | --- | --- | --- |
| Unit | [Logic / models] | [Selected tooling] | [Mocks / fixtures] |
| Contract / API | [Applicable interfaces] | [Selected tooling] | [Strategy] |
| Integration | [Component collaboration] | [Selected tooling] | [Strategy] |
| End-to-end / UI | [Applicable journeys / accessibility] | [Tool or N/A] | [Strategy] |
| Security / resilience / performance | [Required scenarios] | [Method] | [Strategy] |

Ordinary CI is deterministic, secret-free and uses synthetic data. Document any
separate, opt-in live tests, consent, isolated environment and costs.

## 3. Test Environment
[Runner/OS, runtime versions, dependency installation, services, setup/cleanup,
safe environment variables and exact toolchain gate commands.]
Configured applications require `test_report`, for example
`{"path":"test-results/junit.xml","minimum_tests":1}`. Choose a positive minimum
from design and a repository-relative `.xml` path. The runner removes only the
designated stale report before tests, then requires fresh JUnit `testcase`
elements, no failures/errors, and at least the minimum non-skipped cases.
Zero-test, echo-only and stale-report success must fail.

## 4. Test Cases
| ID | Scenario / type | Input / precondition | Expected output | BRD / Story / Task | Result / evidence |
| --- | --- | --- | --- | --- | --- |
| TC-001 | [Scenario] | [Input] | [Assertion] | BRD-FR-001 / STORY-001 / TASK-001 | [Result] |

Include valid/invalid/boundary data, unauthorized access and dependency failures.

## 5. Test Data Requirements
[Factories/fixtures, synthetic accounts, mocked services, invalid inputs,
privacy, repeatability and cleanup.]

## 6. Entry / Exit Criteria
[Entry: merged prerequisites and reproducible environment.
Exit: required tests/gates and coverage targets pass, blocking defects resolved,
limitations disclosed. Never treat missing tests as success.]

## 7. Defect Management
[Severity, reproduction, owner, remediation, regression test and retest evidence.
New → triaged → fixed → verified; unresolved blockers remain visible.]

## 8. Tools & Commands
[Selected frameworks and versions; setup/build/lint/typecheck/test/security
commands through the adapter and locations of retained test artifacts.]

## 9. Traceability Matrix
| BRD ID | Story / task | Test IDs | Outcome / gaps |
| --- | --- | --- | --- |
| BRD-FR-001 | STORY-001 / TASK-001 | TC-001 | [Evidence] |

## 10. Risks & Assumptions
[Environment limitations, unsupported platforms, flaky tests, live-system
differences, mitigation and writer decisions.]
