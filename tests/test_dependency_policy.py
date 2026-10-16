import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class DependencyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load(
            (ROOT / ".github/workflows/dependency-review.yml").read_text(encoding="utf-8"))
        self.job = self.workflow["jobs"]["dependency-policy"]

    def test_required_check_runs_on_every_pr_without_path_filters(self):
        events = self.workflow.get("on", self.workflow.get(True))
        self.assertIn("pull_request", events)
        self.assertIsNone(events["pull_request"])
        self.assertEqual(self.job["name"], "Dependency policy")
        self.assertNotIn("if", self.job)
        self.assertNotIn("continue-on-error", self.job)

    def test_dependency_review_blocks_all_severities_and_scopes(self):
        review, = [step for step in self.job["steps"]
                   if step.get("uses", "").startswith("actions/dependency-review-action@")]
        self.assertEqual(review["if"], "vars.SDLC_REQUIRE_DEPENDENCY_REVIEW == 'true'")
        options = review["with"]
        self.assertEqual(options["fail-on-severity"], "low")
        self.assertEqual({scope.strip() for scope in options["fail-on-scopes"].split(",")},
                         {"runtime", "development", "unknown"})
        self.assertIs(options["vulnerability-check"], True)
        self.assertIs(options["warn-only"], False)
        self.assertNotIn("continue-on-error", review)
        self.assertNotIn("allow-ghsas", options)
        self.assertEqual(options["comment-summary-in-pr"], "never")

    def test_baseline_audit_and_read_only_permissions_are_preserved(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        audit, = [step for step in self.job["steps"]
                  if step.get("run") == "python scripts/audit-template-deps.py"]
        self.assertNotIn("if", audit)
        self.assertEqual(audit["env"], {"GITHUB_TOKEN": "${{ github.token }}"})
        checkout, = [step for step in self.job["steps"]
                     if step.get("uses", "").startswith("actions/checkout@")]
        self.assertIs(checkout["with"]["persist-credentials"], False)

    def test_dependabot_covers_existing_manifests_and_actions(self):
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        self.assertEqual(config["version"], 2)
        updates = {(item["package-ecosystem"], item["directory"]): item
                   for item in config["updates"]}
        for key in (("github-actions", "/"), ("pip", "/scripts")):
            with self.subTest(ecosystem=key):
                self.assertEqual(updates[key]["schedule"]["interval"], "weekly")
                self.assertGreater(updates[key]["open-pull-requests-limit"], 0)


if __name__ == "__main__":
    unittest.main()
