"""Single-writer, merge-gated SDLC state machine.

All entry points must use the same Actions concurrency group. The issue comment
is a durable ledger, not an independent lock. Intent is saved before API writes.
"""

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .contracts import load_json, require, validate_findings, validate_graph, validate_toolchain
from .github import APIError

STATE = "<!-- sdlc-ledger:v1 -->\n"
BOT = "copilot-swe-agent[bot]"
COPILOT = {BOT, "Copilot"}
REVIEWERS = COPILOT | {"copilot-pull-request-reviewer[bot]"}
PREFIX = ("requirements", "design", "backlog", "plan", "bootstrap")
SUFFIX = ("qa", "security")
AGENTS = {
    "requirements": "1-requirement-agent",
    "design": "2-plan-and-design-agent",
    "backlog": "3-epic-and-tasks-agent",
    "plan": "3.5-build-orchestrator-agent",
    "bootstrap": "4-develop-agent",
    "qa": "6-automation-test-agent",
    "security": "7-security-agent",
}
OUTPUTS = {
    "requirements": ["docs/requirements/application-brief.md", "docs/requirements/BRD.md"],
    "design": ["docs/design/HLD.md"],
    "backlog": ["backlog/dependency-graph.json"],
    "plan": ["backlog/waves.json", "backlog/execution-plan.md"],
    "bootstrap": [".github/sdlc/toolchain.json"],
    "qa": ["docs/testing/TestPlan.md"],
    "security": ["docs/testing/security-review.md", "docs/security/findings.json"],
}
LABELS = {
    "sdlc:start": ("0052cc", "Writer-approved application brief"),
    "sdlc:managed": ("5319e7", "Controller-managed cloud-agent work"),
    "sdlc:needs-human": ("b60205", "Blocked: read the tracker before resuming"),
    "sdlc:paused": ("fbca04", "Pipeline explicitly paused"),
    "sdlc:complete": ("0e8a16", "Pipeline delivered through merged PRs"),
}


class Controller:
    def __init__(self, api, repo, root, summary=print):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo), "Invalid repository identity")
        self.api, self.repo, self.root, self.summary = api, repo, Path(root), summary
        self.path = f"/repos/{repo}"
        self.login = api.request("GET", "/user")["login"]
        self.repository = api.request("GET", self.path)
        self.branch = self.repository["default_branch"]
        self.comments = {}

    def writer(self, login):
        from urllib.parse import quote
        try:
            permission = self.api.request(
                "GET", f"{self.path}/collaborators/{quote(login, safe='')}/permission"
            )
        except APIError as error:
            if error.status == 404:
                return False
            raise
        return permission["permission"] in ("admin", "maintain", "write")

    def setup(self):
        existing = {x["name"] for x in self.api.pages(f"{self.path}/labels")}
        for name, (color, description) in LABELS.items():
            from urllib.parse import quote
            endpoint = f"{self.path}/labels"
            if name in existing:
                endpoint += "/" + quote(name, safe="")
            self.api.request("PATCH" if name in existing else "POST", endpoint,
                             {"name": name, "color": color, "description": description})
        self.summary("SDLC labels initialized.")

    def issue_comments(self, number):
        if number not in self.comments:
            self.comments[number] = list(self.api.pages(f"{self.path}/issues/{number}/comments"))
        return self.comments[number]

    def ledger(self, issue):
        matches = [c for c in self.issue_comments(issue["number"])
                   if c["user"]["login"] == self.login and c.get("body", "").startswith(STATE)]
        require(len(matches) <= 1, f"Tracker #{issue['number']} has conflicting ledgers")
        if not matches:
            return None, None
        comment = matches[0]
        state = json.loads(comment["body"][len(STATE):])
        require(state["version"] == 1 and state["root"] == issue["number"]
                and state["repository"] == self.repo and state["branch"] == self.branch,
                "Ledger identity/default branch changed; explicit migration required")
        require(state["status"] in ("active", "paused", "blocked", "complete"), "Invalid ledger status")
        return comment["id"], state

    def save(self, comment_id, state):
        body = STATE + json.dumps(state, sort_keys=True, indent=2)
        require(len(body.encode()) < 60000, "Ledger is too large; split the application into smaller runs")
        self.api.request("PATCH", f"{self.path}/issues/comments/{comment_id}", {"body": body})

    def new_state(self, issue):
        return {"version": 1, "repository": self.repo, "branch": self.branch,
                "root": issue["number"], "status": "active", "reason": "",
                "steps": {}, "completed": [], "graph_sha": None}

    def trusted_start(self, issue):
        events = [e for e in self.api.pages(f"{self.path}/issues/{issue['number']}/events")
                  if e["event"] == "labeled" and e.get("label", {}).get("name") == "sdlc:start"]
        return bool(events and self.writer(events[-1]["actor"]["login"]))

    def annotate(self, root, label, reason):
        self.api.request("POST", f"{self.path}/issues/{root}/labels", {"labels": [label]})
        self.summary(reason)

    def pause(self, comment_id, state, reason, status="blocked"):
        state.update(status=status, reason=reason)
        self.save(comment_id, state)
        self.annotate(state["root"], "sdlc:paused" if status == "paused" else "sdlc:needs-human", reason)

    def graph(self, state):
        graph_path = self.root / "backlog/dependency-graph.json"
        graph = load_json(graph_path)
        waves = validate_graph(graph, self.root)
        digest = hashlib.sha256(graph_path.read_bytes()).hexdigest()
        require(state["graph_sha"] in (None, digest), "Backlog changed after planning; migrate the run explicitly")
        return graph, waves, digest

    def next_step(self, state):
        for stage in PREFIX:
            if stage not in state["completed"]:
                return stage, AGENTS[stage]
        graph, waves, _ = self.graph(state)
        for task_id in (task for wave in waves for task in wave):
            if task_id not in state["completed"]:
                require(set(graph["tasks"][task_id]["dependencies"]) <= set(state["completed"]),
                        "Task prerequisites have not merged")
                agent = "5-ui-develop-agent" if graph["tasks"][task_id]["type"] == "frontend" else "4-develop-agent"
                return task_id, agent
        for stage in SUFFIX:
            if stage not in state["completed"]:
                return stage, AGENTS[stage]
        return None, None

    def validate_outputs(self, key, state):
        for name in OUTPUTS.get(key, []):
            path = self.root / name
            require(path.is_file() and path.stat().st_size > 0, f"{key}: missing output {name}")
        if key == "design":
            require(any((self.root / "docs/design/LLD").glob("*.md")), "Missing component LLDs")
        if key in ("backlog", "plan"):
            _, waves, digest = self.graph(state)
            if key == "plan":
                require(load_json(self.root / "backlog/waves.json") == {"version": 1, "waves": waves},
                        "Execution waves differ from validated DAG")
                state["graph_sha"] = digest
        if key == "bootstrap" or key.startswith("TASK-") or key in SUFFIX:
            require(validate_toolchain(load_json(self.root / ".github/sdlc/toolchain.json"), self.root),
                    "Application toolchain has not been bootstrapped")
        if key == "security":
            report = load_json(self.root / "docs/security/findings.json")
            validate_findings(report, allow_accepted=True)
            for finding in report["findings"]:
                if finding["status"] == "accepted":
                    self.verify_risk_acceptance(finding)

    def verify_risk_acceptance(self, finding):
        parsed = urlparse(finding["decision_url"])
        match = re.fullmatch(rf"/{re.escape(self.repo)}/issues/([0-9]+)", parsed.path)
        require(parsed.scheme == "https" and parsed.netloc == "github.com" and match
                and re.fullmatch(r"issuecomment-[0-9]+", parsed.fragment),
                "Risk acceptance must link to a comment in this repository")
        comment_id = int(parsed.fragment.removeprefix("issuecomment-"))
        comment = self.api.request("GET", f"{self.path}/issues/comments/{comment_id}")
        require(comment["issue_url"].endswith("/" + match[1]), "Risk decision issue mismatch")
        require(comment["user"]["login"] == finding["accepted_by"]
                and self.writer(finding["accepted_by"]), "Risk acceptance is not from a writer")
        require(f"Accept risk {finding['id']}" in comment["body"], "Writer must explicitly accept this finding ID")

    def dispatch(self, comment_id, state, key, agent):
        step = state["steps"].setdefault(key, {"issue": None, "agent": agent, "attempts": [],
                                               "pr": None, "dispatch": "pending"})
        require(step["agent"] == agent, "Task agent changed mid-run")
        marker = f"<!-- sdlc-task:{state['root']}:{key} -->"
        if step["issue"] is None:
            self.save(comment_id, state)
            matches = [i for i in self.api.pages(f"{self.path}/issues?state=all&labels=sdlc%3Amanaged")
                       if "pull_request" not in i and i["user"]["login"] == self.login
                       and marker in (i.get("body") or "")]
            require(len(matches) <= 1, "Conflicting managed issues; reconcile manually")
            if matches:
                issue = matches[0]
            else:
                requirements = "\n".join(f"- `{p}`" for p in OUTPUTS.get(key, []))
                body = (f"{marker}\n# SDLC assignment: {key}\n\n"
                        f"Root application brief: #{state['root']}\n"
                        f"Agent profile: `.github/agents/{agent}.agent.md`\n\n"
                        "Read the root brief, accepted requirements/design and repository instructions. "
                        "Use your existing cloud-agent branch and PR. Do not create a second PR, "
                        "switch branches, close this issue manually, edit the controller ledger, "
                        "or approve/merge any PR.\n\n"
                        f"Include `Closes #ISSUE_NUMBER` in the PR body, replacing ISSUE_NUMBER "
                        "with this assignment issue's number.\n\n"
                        f"Required outputs:\n{requirements or '- Implement the assigned task, with tests.'}\n\n"
                        "Report missing material requirements as blockers, not invented decisions. "
                        "Do not weaken CI or mark failing verification successful.\n")
                if key == "plan":
                    body += "\nRun `python scripts/compute-waves.py` and commit its deterministic outputs.\n"
                if key == "bootstrap":
                    body += ("\nConfigure `.github/sdlc/toolchain.json`, real build/lint/typecheck/test/security gates, "
                             "scanner language/build setup, Dependabot ecosystems, and cloud setup. "
                             "Include a working skeleton and meaningful smoke tests. No feature task may start first.\n")
                if key.startswith("TASK-"):
                    body += f"\nImplement ONLY `backlog/tasks/{key}.md` and its manifest acceptance criteria.\n"
                issue = self.api.request("POST", f"{self.path}/issues", {
                    "title": f"[SDLC #{state['root']}] {key}", "body": body,
                    "labels": ["sdlc:managed"],
                })
            step["issue"] = issue["number"]
            self.save(comment_id, state)
        issue = self.api.request("GET", f"{self.path}/issues/{step['issue']}")
        self.check_blockers(step["issue"])
        require(issue["state"] == "open" or step["dispatch"] == "assigned",
                "Assignment issue was closed before dispatch")
        if any(a["login"] in COPILOT for a in issue["assignees"]):
            step["dispatch"] = "assigned"
            self.save(comment_id, state)
            return step
        require(step["dispatch"] != "assigning",
                "Assignment outcome uncertain; inspect agent sessions before explicitly resuming")
        require(step["dispatch"] != "assigned",
                "Copilot was unassigned; inspect the task before explicitly resuming")
        step["dispatch"] = "assigning"
        self.save(comment_id, state)
        result = self.api.request("POST", f"{self.path}/issues/{step['issue']}/assignees", {
            "assignees": [BOT],
            "agent_assignment": {"target_repo": self.repo, "base_branch": self.branch,
                                 "custom_agent": agent,
                                 "custom_instructions": "Follow the assignment and report blockers; never merge."},
        })
        require(any(a["login"] in COPILOT for a in result["assignees"]),
                "GitHub did not confirm Copilot assignment; check token and repository access")
        step["dispatch"] = "assigned"
        self.save(comment_id, state)
        self.summary(f"Assigned #{step['issue']} ({key}) to {agent}.")
        return step

    def find_pr(self, step):
        if step["pr"] is not None:
            candidates = [self.api.request("GET", f"{self.path}/pulls/{step['pr']}")]
        else:
            candidates = (self.api.request("GET", f"{self.path}/pulls/{number}")
                          for number in self.api.associated_prs(self.repo, step["issue"]))
        matches = []
        for candidate in candidates:
            if candidate["user"]["login"] not in COPILOT or candidate["user"].get("type") != "Bot":
                continue
            if candidate["head"]["repo"] is None or candidate["head"]["repo"]["full_name"] != self.repo:
                continue
            if candidate["base"]["ref"] != self.branch:
                continue
            if step["issue"] in self.api.closing_issues(self.repo, candidate["number"]):
                matches.append(candidate)
        require(len(matches) <= 1, "Multiple PRs close the same assignment; human reconciliation required")
        if not matches:
            require(step["pr"] is None, "Recorded PR provenance or closing reference changed")
            return None
        pr = self.api.request("GET", f"{self.path}/pulls/{matches[0]['number']}")
        require(pr["user"]["login"] in COPILOT and pr["user"].get("type") == "Bot" and pr["head"]["repo"]
                and pr["head"]["repo"]["full_name"] == self.repo and pr["base"]["ref"] == self.branch,
                "PR provenance changed")
        return pr

    def feedback(self, pr):
        sha = pr["head"]["sha"]
        checks = list(self.api.pages(f"{self.path}/commits/{sha}/check-runs?filter=latest", "check_runs"))
        statuses = list(self.api.pages(f"{self.path}/commits/{sha}/statuses"))
        latest = {}
        for status in statuses:
            latest.setdefault(status["context"], status)
        pending = any(c["status"] != "completed" for c in checks) or any(
            s["state"] == "pending" for s in latest.values())
        failures = [f"check:{c['id']}:{c.get('conclusion')}" for c in checks
                    if c["status"] == "completed" and c.get("conclusion") in
                    ("failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure")]
        failures += [f"status:{s['id']}" for s in latest.values() if s["state"] in ("failure", "error")]
        reviews = list(self.api.pages(f"{self.path}/pulls/{pr['number']}/reviews"))
        # A review must explicitly request changes; comments alone are handled below.
        latest_reviews = {}
        for review in reviews:
            if review.get("commit_id") == sha and review["state"] != "PENDING":
                latest_reviews[review["user"]["login"]] = review
        failures += [f"review:{r['id']}" for r in latest_reviews.values()
                     if r["state"] == "CHANGES_REQUESTED"
                     and (r["user"]["login"] in REVIEWERS or self.writer(r["user"]["login"]))]
        for comment in self.api.review_comments(self.repo, pr["number"], sha):
            if comment["author"]["login"] in REVIEWERS:
                failures.append(f"inline:{comment['databaseId']}")
        return sorted(set(failures)), pending, checks

    def check_blockers(self, number):
        blockers = [c for c in self.api.pages(f"{self.path}/issues/{number}/comments")
                    if (c.get("body") or "").startswith("SDLC_BLOCKED:")
                    and (c["user"]["login"] in COPILOT or self.writer(c["user"]["login"]))]
        if not blockers:
            return
        latest = max(blockers, key=lambda c: c["id"])
        decisions = [c for c in self.api.pages(f"{self.path}/issues/{number}/comments")
                     if c["id"] > latest["id"] and (c.get("body") or "").startswith("SDLC_UNBLOCKED:")
                     and self.writer(c["user"]["login"])]
        require(decisions, f"Assignment/PR #{number} reports SDLC_BLOCKED; a writer must resolve it "
                "with SDLC_UNBLOCKED: evidence before resuming.")

    def repair(self, comment_id, state, step, pr):
        failures, pending, _ = self.feedback(pr)
        if pending or not failures:
            return
        sha = pr["head"]["sha"]
        digest = hashlib.sha256(json.dumps(failures).encode()).hexdigest()[:16]
        key = f"{sha}:{digest}"
        if any(a["key"] == key for a in step["attempts"]):
            return
        if len(step["attempts"]) >= 3:
            self.pause(comment_id, state, f"PR #{pr['number']} exhausted three automated repair attempts.")
            return
        # Persist intent; if the response is lost, reconcile the marker before posting again.
        marker = f"<!-- sdlc-repair:{state['root']}:{step['issue']}:{key} -->"
        step["attempts"].append({"key": key, "sent": False})
        self.save(comment_id, state)
        self.send_repair(comment_id, state, step, pr, marker)

    def send_repair(self, comment_id, state, step, pr, marker=None):
        attempt = step["attempts"][-1]
        if attempt["sent"]:
            return
        marker = marker or f"<!-- sdlc-repair:{state['root']}:{step['issue']}:{attempt['key']} -->"
        existing = [c for c in self.api.pages(f"{self.path}/issues/{pr['number']}/comments")
                    if c["user"]["login"] == self.login and marker in (c.get("body") or "")]
        if not existing:
            fresh = self.api.request("GET", f"{self.path}/pulls/{pr['number']}")
            if (fresh["merged"] or fresh["state"] != "open"
                    or fresh["head"]["sha"] != attempt["key"].split(":")[0]):
                attempt.update(sent=True, superseded=True)
                self.save(comment_id, state)
                return
            self.api.request("POST", f"{self.path}/issues/{pr['number']}/comments", {
                "body": (f"{marker}\n@copilot Address the current-head failing checks and actionable "
                         "review feedback on this PR. Reproduce failures, fix root causes, add regression "
                         "tests, and report verification. Do not weaken gates, auto-accept risks, merge, "
                         "or change unrelated code. Stop and report material blockers."),
            })
        attempt["sent"] = True
        self.save(comment_id, state)

    def reconcile(self, action="reconcile", root_number=None, actor=None):
        if action in ("resume", "pause"):
            require(root_number and actor and self.writer(actor), "Pause/resume requires a repository writer")
        roots = {i["number"]: i for i in self.api.pages(f"{self.path}/issues?state=all&labels=sdlc%3Astart")
                 if "pull_request" not in i and "sdlc:start" in {label["name"] for label in i["labels"]}}
        # Discover existing ledgers independently of mutable labels/issue closure.
        for comment in self.api.pages(f"{self.path}/issues/comments"):
            if comment["user"]["login"] == self.login and comment.get("body", "").startswith(STATE):
                ledger = json.loads(comment["body"][len(STATE):])
                number = ledger["root"]
                require(type(number) is int and number > 0, "Invalid ledger root")
                expected = f"https://api.github.com{self.path}/issues/{number}"
                require(comment["issue_url"] == expected, "Ledger is attached to the wrong issue")
                if number not in roots:
                    roots[number] = self.api.request("GET", f"{self.path}/issues/{number}")
        roots = list(roots.values())
        roots.sort(key=lambda i: i["number"])
        tracked = [(issue, *self.ledger(issue)) for issue in roots]
        unfinished = [item for item in tracked if item[2] and item[2]["status"] != "complete"]
        require(len(unfinished) <= 1, "Multiple active pipeline ledgers; resolve before dispatch")
        if action in ("resume", "pause"):
            target = next((item for item in unfinished if item[0]["number"] == root_number), None)
            require(target, "No unfinished pipeline for that root")
            issue, comment_id, state = target
            if action == "pause":
                self.pause(comment_id, state, f"Paused by {actor}.", "paused")
                return
            state.update(status="active", reason="")
            # An explicit resume acknowledges an uncertain assignment, not an automatic retry.
            for step in state["steps"].values():
                if step["dispatch"] == "assigning":
                    step["dispatch"] = "pending"
            self.save(comment_id, state)
            for label in ("sdlc:needs-human", "sdlc:paused"):
                from urllib.parse import quote
                if label in {x["name"] for x in issue["labels"]}:
                    self.api.request("DELETE", f"{self.path}/issues/{root_number}/labels/{quote(label, safe='')}")
        if unfinished:
            issue, comment_id, state = unfinished[0]
        else:
            queued = [i for i, _, state in tracked if state is None and i["state"] == "open"
                      and self.trusted_start(i)]
            if not queued:
                self.summary("No eligible application brief.")
                return
            issue = queued[0]
            state = self.new_state(issue)
            comment = self.api.request("POST", f"{self.path}/issues/{issue['number']}/comments",
                                       {"body": STATE + json.dumps(state)})
            comment_id = comment["id"]
        if state["status"] != "active":
            self.summary(f"Tracker #{state['root']} is {state['status']}: {state['reason']}")
            return
        try:
            require(bool((issue.get("body") or "").strip()), "Application brief is empty; fill it before resuming")
            require(issue["state"] == "open", "Root brief was closed before completion; reopen then resume")
            require("sdlc:start" in {label["name"] for label in issue["labels"]},
                    "Root kickoff label was removed; restore it before resuming")
            key, agent = self.next_step(state)
            if key is None:
                self.validate_outputs("security", state)
                state.update(status="complete", reason="All stages delivered through merged PRs.")
                self.save(comment_id, state)
                self.annotate(state["root"], "sdlc:complete", state["reason"])
                self.api.request("PATCH", f"{self.path}/issues/{state['root']}",
                                 {"state": "closed", "state_reason": "completed"})
                return
            step = self.dispatch(comment_id, state, key, agent)
            pr = self.find_pr(step)
            if pr is None:
                assignment = self.api.request("GET", f"{self.path}/issues/{step['issue']}")
                require(assignment["state"] == "open", "Assignment issue was closed without a delivery PR")
                self.summary(f"Waiting for cloud-agent PR for #{step['issue']}.")
                return
            step["pr"] = pr["number"]
            self.save(comment_id, state)
            self.check_blockers(pr["number"])
            if pr["merged"]:
                require(pr["merged_by"] and pr["merged_by"]["type"] == "User",
                        "Only a human merge can advance this pipeline")
                failures, pending, checks = self.feedback(pr)
                require(not failures and not pending, "Merged PR has failing/pending current-head checks or feedback")
                successful = {c["name"] for c in checks if c.get("conclusion") == "success"}
                require({"Template checks", "Application checks", "Dependency policy", "Code scanning policy"} <= successful,
                        "Merged PR lacks required successful quality/scanning evidence")
                reviews = self.api.pages(f"{self.path}/pulls/{pr['number']}/reviews")
                require(any(r.get("commit_id") == pr["head"]["sha"] and r["state"] in ("COMMENTED", "APPROVED")
                            and r["user"]["login"] in REVIEWERS for r in reviews),
                        "Merged PR lacks a current-head Copilot PR review; check automatic-review settings")
                self.validate_outputs(key, state)
                state["completed"].append(key)
                self.save(comment_id, state)
                self.summary(f"Verified human merge of PR #{pr['number']} for {key}; next run advances.")
                return
            require(pr["state"] == "open", "Assignment PR was closed without merging")
            if step["attempts"] and not step["attempts"][-1]["sent"]:
                self.send_repair(comment_id, state, step, pr)
            self.repair(comment_id, state, step, pr)
        except (ValueError, KeyError, OSError, RuntimeError) as error:
            self.pause(comment_id, state, f"{type(error).__name__}: {error}")
            raise
