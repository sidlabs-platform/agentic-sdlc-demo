#!/usr/bin/env python3
"""Validate the template's executable contracts and workflow safety invariants."""

import ast
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

from sdlc.contracts import load_json, require, validate_findings, validate_graph, validate_toolchain


def workflows(root):
    files = sorted((root / ".github/workflows").glob("*.yml"))
    require(files, "Missing GitHub workflows")
    for path in files:
        source = path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(source)
        # PyYAML follows YAML 1.1, where GitHub's YAML 1.2 key "on" is boolean.
        require(isinstance(workflow, dict) and ("on" in workflow or True in workflow) and "jobs" in workflow,
                f"{path}: invalid workflow")
        require("permissions" in workflow, f"{path}: explicit token permissions required")
        if path.name not in ("sdlc-controller.yml", "sdlc-setup.yml"):
            require("SDLC_TOKEN" not in source, f"{path}: privileged credential in validation workflow")
        for job in workflow["jobs"].values():
            require("timeout-minutes" in job, f"{path}: job timeout required")
            require("continue-on-error" not in job, f"{path}: non-blocking validation forbidden")
            for step in job.get("steps", []):
                if "uses" in step:
                    require(re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", step["uses"]),
                            f"{path}: pin actions to full commit SHAs")
                if "run" in step:
                    require("${{ github.event." not in step["run"] and "${{ inputs." not in step["run"],
                            f"{path}: untrusted shell interpolation")
        if path.name.startswith("sdlc-"):
            require(workflow["concurrency"] == {
                "group": "sdlc-control-${{ github.repository }}", "cancel-in-progress": False
            }, f"{path}: all privileged controllers must share serialization")
            for job in workflow["jobs"].values():
                require(job.get("environment") == "sdlc-control",
                        f"{path}: privileged credentials require the default-branch-only environment")
                for step in job["steps"]:
                    if step.get("uses", "").startswith("actions/checkout@"):
                        require(step.get("with", {}).get("ref") == "${{ github.event.repository.default_branch }}"
                                and step["with"]["persist-credentials"] is False,
                                f"{path}: controller must use trusted default branch without persisted token")


def main():
    root = Path.cwd()
    for directory in ("scripts", "tests"):
        for path in (root / directory).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in (root / ".github/sdlc").glob("*.json"):
        load_json(path)
    validate_toolchain(load_json(root / ".github/sdlc/toolchain.json"), root)
    graph = root / "backlog/dependency-graph.json"
    if graph.exists():
        validate_graph(load_json(graph), root)
    if (root / "backlog/waves.json").exists():
        spec = importlib.util.spec_from_file_location("waves", root / "scripts/compute-waves.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, content in module.artifacts(root).items():
            require((root / name).read_text(encoding="utf-8") == content, f"{name}: stale plan")
    report = root / "docs/security/findings.json"
    if report.exists():
        validate_findings(load_json(report), allow_accepted=True)
    agents = {p.stem.removesuffix(".agent") for p in (root / ".github/agents").glob("*.agent.md")}
    require(len(agents) == 8, "Expected eight SDLC custom agents")
    from sdlc.controller import AGENTS
    require(set(AGENTS.values()) | {"5-ui-develop-agent"} == agents, "Controller/agent identity mismatch")
    workflows(root)
    subprocess.run([sys.executable, "-m", "ruff", "check", "--config", "scripts/ruff.toml",
                    "scripts", "tests"], check=True, timeout=120)
    print("Template contracts, Python quality, and workflow invariants passed.")


if __name__ == "__main__":
    main()
