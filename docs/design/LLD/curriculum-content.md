# Low-Level Design: Curriculum Content and Verification

| Field | Value |
| --- | --- |
| Component / HLD ID | Curriculum content and verification / COMP-002, COMP-003 |
| Version / Date / Author | 1.0 / 2026-10-16 / 2-plan-and-design-agent |
| BRD references | BRD-FR-001, BRD-FR-003–004, BRD-FR-007, BRD-FR-009–010; BRD-NFR-002, BRD-NFR-005, BRD-NFR-007–009; BRD-INT-001 |

## 1. Component Purpose & Scope

Define the repository format and validation for the ordered lessons, quiz
questions and guided lab, plus the CI contract that verifies and builds the
static client. Maintainers edit data files through reviewed pull requests. Tests
reject incomplete or unsafe data before it is shipped.

This component does not implement the learner UI, content authoring interface,
deployment, or network-backed content services.

## 2. Detailed Design

Suggested layout:

```text
content/
  lessons/
    01-agentic-ai.json
    02-copilot-agents.json
    03-issues-and-instructions.json
    04-review-and-governance.json
    05-safety-and-trust.json
  lab/
    guided-lab.json
src/content/
  schema.ts
  validate.ts
  index.ts
tests/unit/content/
  validate.test.ts
```

The exact filenames may change, but order is explicit in data rather than
inferred from directory enumeration. Import all content into the application
bundle. `validateContent` checks the entire set before build/test success and at
the browser boundary before it is rendered. The validator is deterministic,
side-effect free, and reports a path/field and reason without logging content
answer keys unnecessarily.

Use a finite content-block union: heading (level 2–3 and plain text), paragraph
(plain text), ordered/unordered list (plain-text items), code (plain text and
optional language label), and link (plain label and validated URL). No raw HTML,
script, style, iframe, event handler, or arbitrary markdown is allowed. The
client renders strings as escaped framework text. Link validation allows only
absolute HTTPS URLs with host exactly `docs.github.com`; reject credentials,
non-default ports, `javascript:`, `data:`, protocol-relative URLs and other
hosts.

## 3. Data Models

### Lesson and question contract

```json
{
  "id": "lesson-agentic-ai",
  "order": 1,
  "title": "What is agentic AI",
  "summary": "Understand agents, tools, planning and autonomy.",
  "estimatedMinutes": 8,
  "blocks": [
    { "type": "heading", "level": 2, "text": "Agents and assistants" },
    { "type": "paragraph", "text": "Conceptual explanation." }
  ],
  "quiz": {
    "questions": [
      {
        "id": "question-agentic-ai-01",
        "prompt": "Question text",
        "options": [
          { "id": "option-a", "text": "Answer A", "isCorrect": true },
          { "id": "option-b", "text": "Answer B", "isCorrect": false }
        ],
        "explanation": "Why the correct answer is right."
      }
    ]
  }
}
```

Each lesson has a nonempty unique ID/title/summary, integer positive order,
positive estimated minutes, and nonempty supported blocks. The complete set
contains exactly five lessons, ordered 1–5 and matching the brief's specified
topics. Each lesson has exactly three questions. IDs are nonempty and globally
unique across lesson, question, option and lab-step records. Each question has
at least two unique options, nonempty prompt/explanation, and exactly one
`isCorrect: true` option.

### Guided lab contract

The lab JSON has a unique lab ID, positive integer `estimatedMinutes`, and an
ordered array of five unique steps:
write a well-scoped issue, assign it to Copilot, review the resulting PR, request
changes with a comment, and merge manually. Each step has a title, explanatory
content blocks, and one or more official GitHub documentation links using the
same URL validation rule. Step data contains no operation or executable command
that automates a GitHub action. The five lesson estimates plus the lab estimate
must total under 60 minutes.

These files are public static learning material and contain no learner data.
Validation errors fail CI; content changes have no database migration or runtime
data migration.

## 4. Interface Specifications

| Operation / interface | Input | Output | Auth / errors | Compatibility |
| --- | --- | --- | --- | --- |
| `validateContent` | Loaded lesson and lab JSON values | Validated typed content or field-addressed validation errors | No auth/I/O; reject malformed fields, duplicate IDs, invalid counts/order and links | Content schema v1 |
| Content import | Validated JSON module set | Ordered lessons, questions and lab steps for COMP-001 | No auth; invalid bundle prevents build or safe runtime render | Static bundle; schema v1 |
| CI setup/build | Repository lockfile and source | `dist/` static artifact | No app secrets; dependency installation may use npm registry; app/test commands require no external AI/GitHub API | Node.js 22 LTS, npm lockfile |
| Test report | Test runner results | Fresh `test-results/junit.xml` with at least 15 non-skipped cases and no failures/errors | Missing, stale, empty or failing report is a gate failure | Repository toolchain v1 |
| Security evidence | npm dependency graph and TypeScript source | Advisory and code-scanning results or documented policy-approved alternatives | No secrets in app; required stable policy checks remain | npm ecosystem; CodeQL JavaScript/TypeScript where enabled |

## 5. Sequence Diagrams

### Validate content and build

```mermaid
sequenceDiagram
  participant CI as GitHub Actions
  participant Validator as COMP-002 validator/tests
  participant Bundler as Vite build
  participant Artifact as Static dist/
  CI->>Validator: Load repository JSON
  Validator->>Validator: Check required fields, counts, unique IDs and links
  alt Invalid content
    Validator-->>CI: Field-addressed errors; nonzero test/build result
  else Valid content
    Validator-->>CI: Validated v1 content
    CI->>Bundler: Build application and bundled content
    alt Build fails
      Bundler-->>CI: Failure; no publishable artifact
    else Build succeeds
      Bundler->>Artifact: Emit static HTML, JS, CSS and content
      Artifact-->>CI: Static build ready for artifact-size and smoke checks
    end
  end
```

Content is bundled, so an external link outage, missing content endpoint, or
service rate limit cannot make a lesson unavailable. No HTTP retries or remote
content fallback exist.

## 6. Error Handling & Logging

The validator accumulates actionable errors and exits nonzero; include record
path/ID and field, but avoid echoing full answer content or learner data. Invalid
content does not produce a successful test report. Runtime validation errors are
rendered as a generic accessible content-unavailable message; diagnostic detail
is limited to development/test output.

CI fails for invalid content, failed/no tests, type/lint/build errors, unmet
asset budget, security findings under repository policy, or absent required
entitlement configuration. Do not skip, suppress, or convert those results into
success. Application tests must not invoke AI or GitHub APIs. npm registry access
for installation and advisory access for a dependency scanner are build/security
infrastructure, not application runtime integrations.

## 7. Configuration & Environment

| Variable / setting | Purpose | Required? | Safe default / secret source |
| --- | --- | --- | --- |
| Node.js 22 LTS | Build/test runtime | Yes in CI and local contributor setup | Version pinned to supported major; no secret |
| `package-lock.json` | Reproducible npm dependencies | Yes | `npm ci`; never modify implicitly in CI |
| `SDLC_CODEQL_ENABLED` | Select repository CodeQL or documented alternative policy | Yes; exact `true` or `false` | Repository variable; never infer unset |
| `SDLC_REQUIRE_DEPENDENCY_REVIEW` | Select dependency review or documented alternative policy | Yes; exact `true` or `false` | Repository variable; never infer unset |
| `test-results/junit.xml` | Fresh machine-readable test evidence | Yes when toolchain configured | Generated per test run; not checked in |
| `dist/` | Static build output | Generated | No credentials or environment-specific secrets |

## 8. Dependencies

* JSON is the content interchange format; TypeScript validates it without
  requiring a Markdown parser or HTML sanitizer.
* Vite 6.x, TypeScript 5.x, Node.js 22 LTS and npm manage static compilation and
  build scripts; bootstrap pins exact dependency versions and commits the npm
  lockfile.
* Vitest 3.x and a JUnit reporter produce test evidence; test infrastructure
  must verify fresh, non-skipped cases.
* ESLint and `tsc --noEmit` provide lint and type checks.
* CodeQL JavaScript/TypeScript is preferred where enabled. npm dependency
  advisory checks and dependency review follow the repository's documented
  entitlement policy. If a control is unavailable, bootstrap documents and
  configures an approved alternative; do not claim universal coverage.

No runtime external services are dependencies. The build runner is
`ubuntu-latest`; deployment/hosting is not configured.

## 9. Traceability & Verification

| Element | Component | BRD ID | Test approach |
| --- | --- | --- | --- |
| Five ordered lessons and required metadata | COMP-002 | BRD-FR-001 | Valid fixture passes; missing fields, wrong count/order and duplicate IDs fail. |
| Three questions per lesson and one correct option | COMP-002 | BRD-FR-003, BRD-FR-007 | Test 0, 2 and multiple correct choices, missing answer and duplicate IDs. |
| Guided lab sequence, time estimate and official links | COMP-002 | KPI-001, BRD-FR-004, BRD-NFR-008, BRD-INT-001 | Assert five steps, required activities, total curriculum estimate under 60 minutes, and HTTPS `docs.github.com` host; reject invalid schemes/hosts. |
| Structured content block validation | COMP-002 | BRD-FR-002, BRD-FR-009 | Valid supported blocks pass; raw HTML/script block and missing text fail; rendered markup remains inert. |
| Build/test execution without AI/GitHub APIs | COMP-003 | BRD-FR-010 | Run configured app build/tests with external AI/GitHub API access unavailable; inspect runtime requests. |
| Asset/load targets | COMP-003 | BRD-NFR-002 | Measure production asset bytes excluding images and record repeatable initial-load conditions; fail on target breach. |
| Security and dependency controls | COMP-003 | BRD-NFR-005 | Run configured TypeScript scanning and npm/dependency gate; preserve stable policy checks. |
| Test/lint/typecheck | COMP-003 | BRD-NFR-007 | CI executes unit/component tests, lint and typecheck; require fresh JUnit with >=15 non-skipped cases. |
| Static-hostable output | COMP-003 | BRD-NFR-009 | Inspect build output for static assets; host deployment remains out of scope. |
| No runtime integration | COMP-002 / COMP-003 | BRD-INT-001 | Inspect built app/network requests; external docs links are ordinary learner navigation only. |

The BRD is draft for writer review. Implementation/bootstrap must confirm writer
acceptance before treating this design as an approved application baseline.
