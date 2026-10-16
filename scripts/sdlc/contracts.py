"""Strict contracts shared by cloud agents, CI, and the controller."""

import json
import re
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty_strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def validate_graph(graph, root=None):
    require(isinstance(graph, dict) and set(graph) == {"version", "tasks"}, "Invalid backlog fields")
    require(type(graph["version"]) is int and graph["version"] == 1, "Unsupported backlog version")
    tasks = graph["tasks"]
    require(isinstance(tasks, dict) and 0 < len(tasks) <= 100, "Backlog must contain 1-100 tasks")
    known_requirements = None
    if root is not None:
        brd = (root / "docs/requirements/BRD.md").read_text(encoding="utf-8")
        known_requirements = set(re.findall(r"\bBRD-(?:FR|NFR|INT)-[0-9]{3,}\b", brd))
        require(known_requirements, "BRD has no requirement IDs")
    covered = set()
    for task_id, task in tasks.items():
        require(re.fullmatch(r"TASK-[0-9]{3,}", task_id), f"Invalid task ID: {task_id}")
        require(isinstance(task, dict) and set(task) == {
            "title", "type", "dependencies", "requirements", "acceptance_criteria"
        }, f"{task_id}: invalid fields; use dependencies, not depends_on")
        require(isinstance(task["title"], str) and 0 < len(task["title"].strip()) <= 150,
                f"{task_id}: invalid title")
        require(task["type"] in ("implementation", "frontend"), f"{task_id}: invalid type")
        for field in ("dependencies", "requirements", "acceptance_criteria"):
            require(nonempty_strings(task[field]), f"{task_id}: invalid {field}")
            require(len(task[field]) == len(set(task[field])), f"{task_id}: duplicate {field}")
        require(task["requirements"], f"{task_id}: missing requirements")
        require(0 < len(task["acceptance_criteria"]) <= 20, f"{task_id}: unbounded acceptance criteria")
        require(all(re.fullmatch(r"BRD-(FR|NFR|INT)-[0-9]{3,}", x) for x in task["requirements"]),
                f"{task_id}: invalid requirement IDs")
        require(task_id not in task["dependencies"], f"{task_id}: self dependency")
        require(set(task["dependencies"]) <= tasks.keys(), f"{task_id}: undefined dependency")
        covered.update(task["requirements"])
        if root is not None:
            task_file = root / "backlog/tasks" / f"{task_id}.md"
            require(task_file.is_file() and 0 < task_file.stat().st_size <= 24000,
                    f"{task_id}: task document missing, empty, or too large")
    if known_requirements is not None:
        require(covered == known_requirements,
                f"Requirement coverage mismatch: missing={sorted(known_requirements - covered)}, "
                f"unknown={sorted(covered - known_requirements)}")
    remaining, done, waves = set(tasks), set(), []
    while remaining:
        ready = sorted(t for t in remaining if set(tasks[t]["dependencies"]) <= done)
        require(ready, f"Dependency cycle: {sorted(remaining)}")
        waves.append(ready)
        done.update(ready)
        remaining.difference_update(ready)
    return waves


GATES = ("setup", "build", "lint", "typecheck", "test", "security")


def safe_relative(value):
    return (isinstance(value, str) and bool(value.strip()) and "\\" not in value
            and not any(ord(char) < 32 or ord(char) == 127 for char in value)
            and not Path(value).is_absolute() and ".." not in Path(value).parts
            and value not in (".", "") and ".git" not in Path(value).parts)


def application_files(root):
    ignored = {".git", ".github", "scripts", "tests", "docs", "templates", "backlog",
               ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
               ".ruff_cache", ".mypy_cache", ".idea", ".vscode"}
    template_files = {"README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE",
                      "CODE_OF_CONDUCT.md", "CHANGELOG.md", ".gitignore", ".editorconfig"}
    found = []
    for path in root.iterdir():
        if path.name in ignored or path.name in template_files:
            continue
        if path.is_file() or (path.is_dir() and any(path.rglob("*"))):
            found.append(path.name)
    return sorted(found)


def validate_toolchain(config, root):
    require(isinstance(config, dict) and set(config) == {
        "version", "configured", "languages", "source_roots", "runner", "commands", "not_applicable", "test_report"
    }, "Invalid toolchain fields")
    require(type(config["version"]) is int and config["version"] == 1, "Invalid toolchain version")
    require(type(config["configured"]) is bool, "configured must be boolean")
    require(config["runner"] in ("ubuntu-latest", "windows-latest", "macos-latest"), "Invalid runner")
    for field in ("languages", "source_roots"):
        require(nonempty_strings(config[field]), f"Invalid {field}")
        require(len(config[field]) == len(set(config[field])), f"Duplicate {field}")
    require(isinstance(config["commands"], dict) and set(config["commands"]) == set(GATES),
            "All six command gates are required")
    for name, commands in config["commands"].items():
        require(isinstance(commands, list), f"{name}: commands must be arrays of argv arrays")
        for argv in commands:
            require(nonempty_strings(argv) and argv, f"{name}: empty/invalid argv")
    na = config["not_applicable"]
    require(isinstance(na, dict) and set(na) <= {"build", "typecheck"}, "Invalid non-applicable gates")
    require(all(isinstance(x, str) and len(x.strip()) >= 10 for x in na.values()),
            "Non-applicable gates need a meaningful rationale")
    for source in config["source_roots"]:
        require(safe_relative(source), f"Unsafe source root: {source}")
        require(Path(source).parts[0] not in {".github", "scripts", "tests", "docs", "templates", "backlog"},
                "Application source roots must be separate from template-owned directories")
        directory = (root / source).resolve()
        require(directory.is_relative_to(root.resolve()) and directory.is_dir(),
                f"Source root missing or outside repository: {source}")
    if not config["configured"]:
        require(not application_files(root), "Application files exist but toolchain is not configured")
        require(not config["languages"] and not config["source_roots"]
                and not any(config["commands"].values()) and not na and config["test_report"] is None,
                "Unconfigured toolchain must not contain executable configuration")
        return False
    require(config["languages"] and config["source_roots"], "Configured application needs languages and roots")
    report = config["test_report"]
    require(isinstance(report, dict) and set(report) == {"path", "minimum_tests"},
            "Configured application requires JUnit test_report evidence")
    require(safe_relative(report["path"]) and Path(report["path"]).suffix == ".xml",
            "test_report.path must be a repository-relative XML file")
    require((root / report["path"]).resolve().is_relative_to(root.resolve()),
            "Test report must remain inside the repository")
    require(type(report["minimum_tests"]) is int and report["minimum_tests"] > 0,
            "test_report.minimum_tests must be positive")
    for name in GATES:
        if name != "setup":
            require(bool(config["commands"][name]) != (name in na),
                    f"{name}: provide commands or an allowed non-applicability rationale, not both")
    return True


def validate_findings(report, allow_accepted=False):
    require(isinstance(report, dict) and set(report) == {"version", "findings"}
            and type(report["version"]) is int and report["version"] == 1, "Invalid security report")
    require(isinstance(report["findings"], list), "findings must be an array")
    ids = set()
    for finding in report["findings"]:
        require(isinstance(finding, dict) and {"id", "severity", "status", "description"} <= finding.keys()
                and finding.keys() <= {"id", "severity", "status", "description",
                                       "acceptance_reason", "accepted_by", "decision_url"},
                "Invalid finding fields")
        require(isinstance(finding["id"], str) and re.fullmatch(r"SEC-[0-9]{3,}", finding["id"])
                and finding["id"] not in ids, "Invalid/duplicate finding ID")
        ids.add(finding["id"])
        require(finding["severity"] in ("critical", "high", "medium", "low", "info"), "Invalid severity")
        require(finding["status"] in ("open", "fixed", "accepted"), "Invalid finding status")
        require(isinstance(finding["description"], str) and finding["description"].strip(),
                "Missing finding description")
        require(finding["status"] != "open", f"Unresolved security finding: {finding['id']}")
        if finding["status"] == "accepted":
            require(finding["severity"] not in ("critical", "high"), "High/critical risk cannot be accepted")
            require(all(isinstance(finding.get(k), str) and finding[k].strip()
                        for k in ("acceptance_reason", "accepted_by", "decision_url")),
                    "Accepted risk requires a documented writer decision")
            require(allow_accepted, "Accepted risk requires controller verification of writer decision")
