import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sdlc.contracts import (  # noqa: E402
    GATES, load_json, validate_findings, validate_graph, validate_toolchain,
)


def task(dependencies=None, kind="implementation"):
    return {"title": "Deliver a testable outcome", "type": kind, "dependencies": dependencies or [],
            "requirements": ["BRD-FR-001"], "acceptance_criteria": ["The defined outcome is verified"]}


def toolchain(configured=False):
    return {"version": 1, "configured": configured, "languages": ["example"] if configured else [],
            "source_roots": ["app"] if configured else [], "runner": "ubuntu-latest",
            "commands": {gate: [["python", "--version"]] if configured else [] for gate in GATES},
            "not_applicable": {},
            "test_report": {"path": "test-results/junit.xml", "minimum_tests": 1} if configured else None}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_dependency_order_and_frontend_routing_are_explicit(self):
        graph = {"version": 1, "tasks": {"TASK-003": task(["TASK-002"], "frontend"),
                                        "TASK-002": task(["TASK-001"]), "TASK-001": task()}}
        self.assertEqual(validate_graph(graph), [["TASK-001"], ["TASK-002"], ["TASK-003"]])
        self.assertEqual(graph["tasks"]["TASK-003"]["type"], "frontend")

    def test_invalid_dags_and_old_dependency_field_fail(self):
        cases = []
        old = task()
        old["depends_on"] = old.pop("dependencies")
        cases.append({"TASK-001": old})
        cases.append({"TASK-001": task(["TASK-999"])})
        cases.append({"TASK-001": task(["TASK-001"])})
        cases.append({"TASK-001": task(["TASK-002"]), "TASK-002": task(["TASK-001"])})
        cases.append({"TASK-001": task(), "TASK-002": task(["TASK-001", "TASK-001"])})
        cases.append({"TASK-001": task(kind="backend")})
        cases.append({})
        for tasks in cases:
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                validate_graph({"version": 1, "tasks": tasks})

    def test_json_duplicate_keys_rejected(self):
        path = self.root / "duplicate.json"
        path.write_text('{"version":1,"version":2}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_json(path)

    def test_requirement_coverage_and_missing_documents_fail(self):
        (self.root / "docs/requirements").mkdir(parents=True)
        (self.root / "docs/requirements/BRD.md").write_text("BRD-FR-001 BRD-NFR-001", encoding="utf-8")
        graph = {"version": 1, "tasks": {"TASK-001": task()}}
        with self.assertRaisesRegex(ValueError, "task document"):
            validate_graph(graph, self.root)
        (self.root / "backlog/tasks").mkdir(parents=True)
        (self.root / "backlog/tasks/TASK-001.md").write_text("Bounded implementation", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            validate_graph(graph, self.root)
        graph["tasks"]["TASK-001"]["requirements"].append("BRD-NFR-001")
        self.assertEqual(validate_graph(graph, self.root), [["TASK-001"]])

    def test_template_is_not_a_fake_application_success(self):
        self.assertFalse(validate_toolchain(toolchain(), self.root))
        (self.root / "package.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not configured"):
            validate_toolchain(toolchain(), self.root)

    def test_application_requires_real_gates(self):
        (self.root / "app").mkdir()
        config = toolchain(True)
        self.assertTrue(validate_toolchain(config, self.root))
        for gate in ("lint", "test", "security"):
            broken = copy.deepcopy(config)
            broken["commands"][gate] = []
            with self.subTest(gate=gate), self.assertRaisesRegex(ValueError, gate):
                validate_toolchain(broken, self.root)
        config["commands"]["typecheck"] = []
        config["not_applicable"]["typecheck"] = "The selected language has no static type checker."
        self.assertTrue(validate_toolchain(config, self.root))

    def test_unsafe_roots_and_empty_commands_fail(self):
        config = toolchain(True)
        for source in ("../outside", "/tmp/outside", ".git/config", "app\\escape", "app\nrunner=unsafe"):
            config["source_roots"] = [source]
            with self.subTest(source=source), self.assertRaises(ValueError):
                validate_toolchain(config, self.root)
        (self.root / "app").mkdir()
        config["source_roots"] = ["app"]
        config["commands"]["test"] = [[]]
        with self.assertRaises(ValueError):
            validate_toolchain(config, self.root)

    def test_gate_execution_uses_argv_without_shell(self):
        (self.root / ".github/sdlc").mkdir(parents=True)
        (self.root / "app").mkdir()
        config = toolchain(True)
        config["commands"]["test"] = [["python", "literal;$(touch forbidden)"]]
        (self.root / ".github/sdlc/toolchain.json").write_text(json.dumps(config), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("toolchain_runner",
                                                      Path(__file__).resolve().parents[1] / "scripts/toolchain.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        def generated_report(*args, **kwargs):
            path = self.root / config["test_report"]["path"]
            path.write_text('<testsuite><testcase name="outcome"/></testsuite>', encoding="utf-8")

        with patch.object(module.Path, "cwd", return_value=self.root), \
                patch.object(sys, "argv", ["toolchain.py", "--gate", "test"]), \
                patch.object(module.subprocess, "run", side_effect=generated_report) as run:
            module.main()
        self.assertEqual(run.call_args.args[0], config["commands"]["test"][0])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_no_op_zero_skipped_or_stale_tests_cannot_pass(self):
        spec = importlib.util.spec_from_file_location("report_runner",
                                                      Path(__file__).resolve().parents[1] / "scripts/toolchain.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        path = self.root / "junit.xml"
        reports = ("<testsuite/>",
                   '<testsuite><testcase><skipped/></testcase></testsuite>',
                   '<testsuite><testcase><failure/></testcase></testsuite>',
                   '<testsuite><testcase><error/></testcase></testsuite>',
                   '<!DOCTYPE foo [<!ENTITY x "bad">]><testsuite><testcase>&x;</testcase></testsuite>')
        for report in reports:
            path.write_text(report, encoding="utf-8")
            with self.subTest(report=report), self.assertRaises(ValueError):
                module.verify_test_report(path, 1)
        path.write_text('<testsuite><testcase name="verified"/></testsuite>', encoding="utf-8")
        module.verify_test_report(path, 1)
        with self.assertRaises(ValueError):
            module.verify_test_report(path, 2)
        (self.root / ".github/sdlc").mkdir(parents=True)
        (self.root / "app").mkdir()
        config = toolchain(True)
        config["test_report"]["path"] = "junit.xml"
        (self.root / ".github/sdlc/toolchain.json").write_text(json.dumps(config), encoding="utf-8")
        with patch.object(module.Path, "cwd", return_value=self.root), \
                patch.object(sys, "argv", ["toolchain.py", "--gate", "test"]), \
                patch.object(module.subprocess, "run"), self.assertRaisesRegex(ValueError, "Missing"):
            module.main()
        self.assertFalse(path.exists())

    def test_security_completion_fails_closed(self):
        report = {"version": 1, "findings": []}
        validate_findings(report)
        finding = {"id": "SEC-001", "severity": "high", "status": "open", "description": "A defect"}
        report["findings"] = [finding]
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            validate_findings(report)
        finding.update(status="accepted", acceptance_reason="Business decision", accepted_by="writer",
                       decision_url="https://github.com/owner/repo/issues/1#issuecomment-1")
        with self.assertRaisesRegex(ValueError, "cannot be accepted"):
            validate_findings(report, allow_accepted=True)
        finding["severity"] = "low"
        with self.assertRaisesRegex(ValueError, "controller verification"):
            validate_findings(report)
        validate_findings(report, allow_accepted=True)
        finding["status"] = "fixed"
        validate_findings(report)

    def test_wave_output_is_deterministic_and_complete(self):
        (self.root / "docs/requirements").mkdir(parents=True)
        (self.root / "docs/requirements/BRD.md").write_text("BRD-FR-001", encoding="utf-8")
        (self.root / "backlog/tasks").mkdir(parents=True)
        for task_id in ("TASK-001", "TASK-002"):
            (self.root / f"backlog/tasks/{task_id}.md").write_text(task_id, encoding="utf-8")
        graph = {"version": 1, "tasks": {"TASK-002": task(["TASK-001"]), "TASK-001": task()}}
        (self.root / "backlog/dependency-graph.json").write_text(json.dumps(graph), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("waves",
                                                      Path(__file__).resolve().parents[1] / "scripts/compute-waves.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        artifacts = module.artifacts(self.root)
        self.assertEqual(artifacts, module.artifacts(self.root))
        self.assertEqual(json.loads(artifacts["backlog/waves.json"])["waves"], [["TASK-001"], ["TASK-002"]])


if __name__ == "__main__":
    unittest.main()
