import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sdlc.controller import AGENTS, BOT, OUTPUTS, STATE, Controller  # noqa: E402
from sdlc.github import APIError, GitHub  # noqa: E402
from test_contracts import task, toolchain  # noqa: E402


class FakeAPI:
    """In-memory API with real ledger round trips and injectable lost responses."""

    def __init__(self):
        self.calls = []
        self.login = "automation-owner"
        self.issues = {1: {"number": 1, "body": "Build a useful application; no fixed stack.",
                           "user": {"login": "writer"}, "state": "open",
                           "labels": [{"name": "sdlc:start"}], "assignees": []}}
        self.comments = {}
        self.prs = {}
        self.links = {}
        self.checks = {}
        self.inline = {}
        self.reviews = {}
        self.events = [{"event": "labeled", "label": {"name": "sdlc:start"},
                        "actor": {"login": "writer"}}]
        self.fail = None
        self.next_comment = 100
        self.labels = []

    def request(self, method, path, data=None):
        self.calls.append((method, path, copy.deepcopy(data)))
        route = path.removeprefix("/repos/owner/repo")
        if path == "/user":
            return {"login": self.login}
        if route == "" and method == "GET":
            return {"default_branch": "trunk"}
        if route.startswith("/collaborators/"):
            return {"permission": "write" if route.split("/")[2] in ("writer", self.login) else "read"}
        if method == "POST" and route == "/issues":
            number = max(self.issues) + 1
            self.issues[number] = {
                "number": number, "body": data["body"], "title": data["title"],
                "user": {"login": self.login}, "state": "open", "assignees": [],
                "labels": [{"name": name} for name in data["labels"]],
            }
            if self.fail == "lost-issue-response":
                self.fail = None
                raise APIError(0, "Lost response")
            return copy.deepcopy(self.issues[number])
        if route.startswith("/issues/comments/"):
            number = int(route.split("/")[-1])
            if method == "GET":
                return copy.deepcopy(self.comments[number])
            self.comments[number]["body"] = data["body"]
            return copy.deepcopy(self.comments[number])
        if route.startswith("/issues/"):
            parts = route.split("/")
            number = int(parts[2])
            issue = self.issues.get(number)
            if len(parts) == 3:
                if method == "PATCH":
                    issue.update(data)
                return copy.deepcopy(issue)
            if parts[3] == "assignees":
                if self.fail == "assignment":
                    raise APIError(403, "Assignment denied")
                issue["assignees"] = [{"login": BOT}]
                return copy.deepcopy(issue)
            if parts[3] == "labels":
                if method == "POST":
                    for label in data["labels"]:
                        if label not in {x["name"] for x in issue["labels"]}:
                            issue["labels"].append({"name": label})
                return copy.deepcopy(issue["labels"])
            if parts[3] == "comments" and method == "POST":
                self.next_comment += 1
                comment = {"id": self.next_comment, "body": data["body"],
                           "user": {"login": self.login}, "issue": number,
                           "issue_url": f"https://api.github.com/repos/owner/repo/issues/{number}"}
                self.comments[comment["id"]] = comment
                if self.fail == "lost-repair-response" and "@copilot" in data["body"]:
                    self.fail = None
                    raise APIError(0, "Lost response")
                return copy.deepcopy(comment)
        if route.startswith("/pulls/") and method == "GET":
            return copy.deepcopy(self.prs[int(route.split("/")[2])])
        raise AssertionError((method, path, data))

    def pages(self, path, field=None):
        route = urlsplit(path).path.removeprefix("/repos/owner/repo")
        if route == "/issues":
            return iter(copy.deepcopy(list(self.issues.values())))
        if route == "/pulls":
            return iter(copy.deepcopy(list(self.prs.values())))
        if route == "/labels":
            return iter(copy.deepcopy(self.labels))
        if route == "/issues/comments":
            return iter(copy.deepcopy(list(self.comments.values())))
        if route.startswith("/issues/"):
            number = int(route.split("/")[2])
            if route.endswith("/events"):
                return iter(copy.deepcopy(self.events))
            if route.endswith("/comments"):
                return iter(copy.deepcopy([c for c in self.comments.values() if c["issue"] == number]))
        if route.startswith("/commits/"):
            sha = route.split("/")[2]
            return iter(copy.deepcopy(self.checks.get(sha, []))) if field else iter([])
        if route.startswith("/pulls/"):
            number = int(route.split("/")[2])
            collection = self.inline if route.endswith("/comments") else self.reviews
            return iter(copy.deepcopy(collection.get(number, [])))
        raise AssertionError(path)

    def closing_issues(self, repo, number):
        return self.links.get(number, set())

    def associated_prs(self, repo, issue):
        return (number for number, issues in self.links.items() if issue in issues)

    def review_comments(self, repo, number, sha):
        return [c for c in self.inline.get(number, []) if c["commit"]["oid"] == sha and not c.get("resolved")]

    def add_pr(self, issue, number=20, merged=False, **kwargs):
        sha = f"sha-{number}"
        pr = {"number": number, "user": {"login": BOT, "type": "Bot"},
              "head": {"sha": sha, "repo": {"full_name": "owner/repo"}},
              "base": {"ref": "trunk"}, "merged": merged, "state": "closed" if merged else "open",
              "merged_by": {"type": "User", "login": "writer"} if merged else None}
        pr.update(kwargs)
        self.prs[number] = pr
        self.links[number] = {issue}
        self.checks[sha] = [{"id": i, "name": name, "status": "completed", "conclusion": "success"}
                            for i, name in enumerate(("Template checks", "Application checks",
                                                       "Dependency policy", "Code scanning policy"))]
        self.reviews[number] = [{"id": number, "commit_id": sha, "state": "COMMENTED",
                                 "user": {"login": "copilot-pull-request-reviewer[bot]"}}]
        return pr

    def state(self):
        return json.loads(next(c["body"][len(STATE):] for c in self.comments.values()
                               if c["body"].startswith(STATE)))


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.api = FakeAPI()

    def controller(self):
        return Controller(self.api, "owner/repo", self.root, summary=lambda message: None)

    def run_controller(self, **kwargs):
        self.controller().reconcile(**kwargs)

    def write(self, path, content):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")

    def fulfill(self, key):
        for name in OUTPUTS.get(key, []):
            self.write(name, "Accepted stage evidence")
        if key == "requirements":
            self.write("docs/requirements/BRD.md", "BRD-FR-001")
        if key == "design":
            self.write("docs/design/LLD/component.md", "Component contract")
        if key == "backlog":
            self.write("backlog/tasks/TASK-001.md", "Implementation contract")
            self.write("backlog/tasks/TASK-002.md", "Frontend contract")
            self.write("backlog/dependency-graph.json", {"version": 1, "tasks": {
                "TASK-001": task(), "TASK-002": task(["TASK-001"], "frontend")}})
        if key == "plan":
            self.write("backlog/waves.json", {"version": 1, "waves": [["TASK-001"], ["TASK-002"]]})
        if key == "bootstrap":
            (self.root / "app").mkdir()
            self.write(".github/sdlc/toolchain.json", toolchain(True))
        if key == "security":
            self.write("docs/security/findings.json", {"version": 1, "findings": []})

    def test_trusted_kickoff_dispatch_is_idempotent_and_uses_user_assignment_api(self):
        self.run_controller()
        state = self.api.state()
        self.assertEqual(state["steps"]["requirements"]["issue"], 2)
        self.assertEqual(state["branch"], "trunk")
        self.run_controller()
        self.assertEqual(len(self.api.issues), 2)
        assignments = [c for c in self.api.calls if c[1].endswith("/assignees")]
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0][2]["agent_assignment"]["custom_agent"], AGENTS["requirements"])
        self.assertEqual(assignments[0][2]["assignees"], [BOT])

    def test_untrusted_label_and_spoofed_ledger_do_not_start(self):
        self.api.events[0]["actor"]["login"] = "external"
        self.api.comments[90] = {"id": 90, "issue": 1, "body": STATE + "{}",
                                 "user": {"login": "external"}}
        self.run_controller()
        self.assertEqual(len(self.api.issues), 1)

    def test_empty_brief_has_visible_recoverable_blocker(self):
        self.api.issues[1]["body"] = ""
        with self.assertRaisesRegex(ValueError, "Application brief is empty"):
            self.run_controller()
        self.assertEqual(self.api.state()["status"], "blocked")
        self.assertIn("sdlc:needs-human", {x["name"] for x in self.api.issues[1]["labels"]})
        self.api.issues[1]["body"] = "The completed application brief."
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.assertEqual(self.api.state()["steps"]["requirements"]["dispatch"], "assigned")

    def test_lost_issue_creation_response_recovers_without_duplicate(self):
        self.api.fail = "lost-issue-response"
        with self.assertRaises(APIError):
            self.run_controller()
        self.assertEqual(self.api.state()["status"], "blocked")
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.assertEqual(len(self.api.issues), 2)
        self.assertEqual(self.api.state()["steps"]["requirements"]["dispatch"], "assigned")

    def test_assignment_failure_is_not_success(self):
        self.api.fail = "assignment"
        with self.assertRaises(APIError):
            self.run_controller()
        self.assertEqual(self.api.state()["steps"]["requirements"]["dispatch"], "assigning")
        self.assertEqual(self.api.state()["status"], "blocked")
        self.api.fail = None
        self.run_controller()
        self.assertFalse(self.api.issues[2]["assignees"])
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.assertEqual(self.api.issues[2]["assignees"], [{"login": BOT}])

    def test_issue_closure_and_unrelated_pr_do_not_advance(self):
        self.run_controller()
        self.api.issues[2]["state"] = "closed"
        self.api.add_pr(99, merged=True)
        with self.assertRaisesRegex(ValueError, "closed without a delivery PR"):
            self.run_controller()
        self.assertEqual(self.api.state()["completed"], [])

    def test_closed_unmerged_pr_blocks(self):
        self.run_controller()
        self.api.add_pr(2, state="closed")
        with self.assertRaisesRegex(ValueError, "without merging"):
            self.run_controller()
        self.assertEqual(self.api.state()["status"], "blocked")

    def test_fork_wrong_base_and_non_copilot_prs_ignored(self):
        self.run_controller()
        self.api.add_pr(2, head={"sha": "x", "repo": {"full_name": "external/repo"}})
        self.api.add_pr(2, number=21, base={"ref": "other"})
        self.api.add_pr(2, number=22, user={"login": "external"})
        self.run_controller()
        self.assertIsNone(self.api.state()["steps"]["requirements"]["pr"])

    def test_duplicate_prs_require_reconciliation(self):
        self.run_controller()
        self.api.add_pr(2)
        self.api.add_pr(2, number=21)
        with self.assertRaisesRegex(ValueError, "Multiple PRs"):
            self.run_controller()

    def test_missing_outputs_or_bot_merge_cannot_advance(self):
        self.run_controller()
        pr = self.api.add_pr(2, merged=True)
        with self.assertRaisesRegex(ValueError, "missing output"):
            self.run_controller()
        self.fulfill("requirements")
        pr["merged_by"] = {"type": "Bot", "login": "bot"}
        with self.assertRaisesRegex(ValueError, "human merge"):
            self.run_controller(action="resume", root_number=1, actor="writer")

    def test_missing_check_evidence_cannot_advance(self):
        self.run_controller()
        pr = self.api.add_pr(2, merged=True)
        self.api.checks[pr["head"]["sha"]] = []
        self.fulfill("requirements")
        with self.assertRaisesRegex(ValueError, "quality/scanning evidence"):
            self.run_controller()

    def test_repair_dedup_budget_and_lost_response_recovery(self):
        self.run_controller()
        pr = self.api.add_pr(2)
        self.api.checks[pr["head"]["sha"]][0]["conclusion"] = "failure"
        self.api.fail = "lost-repair-response"
        with self.assertRaises(APIError):
            self.run_controller()
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.run_controller()
        sent = [c for c in self.api.comments.values() if "@copilot" in c["body"]]
        self.assertEqual(len(sent), 1)
        for index in range(1, 4):
            pr["head"]["sha"] = f"new-sha-{index}"
            self.api.checks[pr["head"]["sha"]] = [
                {"id": index + 100, "name": "Template checks", "status": "completed", "conclusion": "failure"}]
            self.run_controller()
        self.assertEqual(len(self.api.state()["steps"]["requirements"]["attempts"]), 3)
        self.assertEqual(self.api.state()["status"], "blocked")

    def test_pending_checks_do_not_trigger_repairs(self):
        self.run_controller()
        pr = self.api.add_pr(2)
        self.api.checks[pr["head"]["sha"]][0].update(status="in_progress", conclusion=None)
        self.run_controller()
        self.assertEqual(self.api.state()["steps"]["requirements"]["attempts"], [])

    def test_current_copilot_bot_alias_and_review_evidence(self):
        self.run_controller()
        pr = self.api.add_pr(2, merged=True, user={"login": "Copilot", "type": "Bot"})
        self.fulfill("requirements")
        self.api.reviews[pr["number"]] = []
        with self.assertRaisesRegex(ValueError, "current-head Copilot"):
            self.run_controller()
        self.api.reviews[pr["number"]] = [{"id": 99, "commit_id": pr["head"]["sha"], "state": "COMMENTED",
                                         "user": {"login": "copilot-pull-request-reviewer[bot]"}}]
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.assertEqual(self.api.state()["completed"], ["requirements"])

    def test_resolved_and_outdated_review_feedback_does_not_repair(self):
        self.run_controller()
        pr = self.api.add_pr(2)
        self.api.inline[pr["number"]] = [
            {"databaseId": 1, "author": {"login": "Copilot"}, "commit": {"oid": "old-sha"}},
            {"databaseId": 2, "author": {"login": "Copilot"}, "commit": {"oid": pr["head"]["sha"]},
             "resolved": True},
        ]
        self.run_controller()
        self.assertEqual(self.api.state()["steps"]["requirements"]["attempts"], [])
        self.api.inline[pr["number"]].append(
            {"databaseId": 3, "author": {"login": "Copilot"}, "commit": {"oid": pr["head"]["sha"]}})
        self.run_controller()
        self.assertEqual(len(self.api.state()["steps"]["requirements"]["attempts"]), 1)

    def test_blocker_requires_explicit_writer_resolution_and_resume(self):
        self.run_controller()
        self.api.comments[200] = {"id": 200, "issue": 2, "body": "SDLC_BLOCKED: missing business decision",
                                  "user": {"login": "Copilot"}}
        with self.assertRaisesRegex(ValueError, "SDLC_BLOCKED"):
            self.run_controller()
        self.api.comments[201] = {"id": 201, "issue": 2, "body": "SDLC_UNBLOCKED: use accepted BRD",
                                  "user": {"login": "external"}}
        with self.assertRaisesRegex(ValueError, "SDLC_BLOCKED"):
            self.run_controller(action="resume", root_number=1, actor="writer")
        self.api.comments[202] = {"id": 202, "issue": 2, "body": "SDLC_UNBLOCKED: approved decision recorded",
                                  "user": {"login": "writer"}}
        self.run_controller(action="resume", root_number=1, actor="writer")
        self.assertEqual(self.api.state()["status"], "active")

    def test_removing_start_label_does_not_start_a_second_pipeline(self):
        self.run_controller()
        self.api.issues[1]["labels"] = []
        self.api.issues[10] = {"number": 10, "body": "Another brief", "user": {"login": "writer"},
                               "state": "open", "labels": [{"name": "sdlc:start"}], "assignees": []}
        with self.assertRaisesRegex(ValueError, "label was removed"):
            self.run_controller()
        self.assertEqual(len([c for c in self.api.comments.values() if c["body"].startswith(STATE)]), 1)

    def test_backlog_mutation_after_planning_blocks_dispatch(self):
        self.fulfill("requirements")
        self.fulfill("backlog")
        state = {"graph_sha": None}
        _, _, digest = self.controller().graph(state)
        state["graph_sha"] = digest
        self.write("backlog/dependency-graph.json", {"version": 1, "tasks": {"TASK-001": task()}})
        with self.assertRaisesRegex(ValueError, "changed after planning"):
            self.controller().graph(state)

    def test_risk_acceptance_requires_same_repository_writer_comment(self):
        finding = {"id": "SEC-001", "accepted_by": "writer",
                   "decision_url": "https://github.com/owner/repo/issues/1#issuecomment-99"}
        self.api.comments[99] = {"id": 99, "issue": 1, "body": "Accept risk SEC-001 with rationale",
                                 "issue_url": "https://api.github.com/repos/owner/repo/issues/1",
                                 "user": {"login": "writer"}}
        self.controller().verify_risk_acceptance(finding)
        finding["accepted_by"] = "external"
        with self.assertRaisesRegex(ValueError, "writer"):
            self.controller().verify_risk_acceptance(finding)
        finding["decision_url"] = "https://malicious.invalid/owner/repo/issues/1#issuecomment-99"
        with self.assertRaisesRegex(ValueError, "repository"):
            self.controller().verify_risk_acceptance(finding)

    def test_pause_and_resume_require_writer(self):
        self.run_controller()
        with self.assertRaisesRegex(ValueError, "writer"):
            self.run_controller(action="pause", root_number=1, actor="external")
        self.run_controller(action="pause", root_number=1, actor="writer")
        self.run_controller()
        self.assertEqual(self.api.state()["status"], "paused")

    def test_entire_merge_gated_lifecycle_and_queue(self):
        self.api.issues[10] = copy.deepcopy(self.api.issues[1])
        self.api.issues[10]["number"] = 10
        stages = ["requirements", "design", "backlog", "plan", "bootstrap",
                  "TASK-001", "TASK-002", "qa", "security"]
        self.run_controller()
        for index, key in enumerate(stages):
            with self.subTest(stage=key):
                state = self.api.state()
                issue_number = state["steps"][key]["issue"]
                self.assertNotEqual(issue_number, 10)
                self.fulfill(key)
                self.api.add_pr(issue_number, number=20 + index, merged=True)
                self.run_controller()
                self.assertIn(key, self.api.state()["completed"])
                self.run_controller()
        state = self.api.state()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(self.api.issues[1]["state"], "closed")
        self.assertEqual(state["steps"]["TASK-002"]["agent"], "5-ui-develop-agent")
        for _method, path, _data in self.api.calls:
            self.assertNotIn("/merge", path)
            self.assertNotIn("/git/refs", path)

    def test_api_pagination_does_not_truncate(self):
        api = GitHub("not-a-real-token")
        pages = []

        def request(method, path, data=None):
            pages.append(path)
            return list(range(100)) if parse_qs(urlsplit(path).query)["page"] == ["1"] else [100]

        api.request = request
        self.assertEqual(len(list(api.pages("/repos/owner/repo/issues?state=all"))), 101)
        self.assertEqual(len(pages), 2)


if __name__ == "__main__":
    unittest.main()
