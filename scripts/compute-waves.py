#!/usr/bin/env python3
"""Validate the backlog and generate deterministic advisory execution waves."""

import argparse
import json
from pathlib import Path

from sdlc.contracts import load_json, require, validate_graph


def artifacts(root):
    graph = load_json(root / "backlog/dependency-graph.json")
    waves = validate_graph(graph, root)
    machine = json.dumps({"version": 1, "waves": waves}, indent=2) + "\n"
    lines = ["# Execution plan", "", "Advisory waves; only verified merged PRs release dependencies.", ""]
    for i, tasks in enumerate(waves):
        lines += [f"## Wave {i}", "", "| Task | Type | Dependencies |",
                  "| --- | --- | --- |"]
        for task_id in tasks:
            task = graph["tasks"][task_id]
            lines.append(f"| {task_id} | {task['type']} | {', '.join(task['dependencies']) or 'None'} |")
        lines.append("")
    return {"backlog/waves.json": machine, "backlog/execution-plan.md": "\n".join(lines) + "\n"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    for name, content in artifacts(root).items():
        path = root / name
        if args.check:
            require(path.is_file() and path.read_text(encoding="utf-8") == content,
                    f"{name} is missing or stale; run python scripts/compute-waves.py")
        else:
            path.write_text(content, encoding="utf-8")
        print(f"{'Validated' if args.check else 'Generated'} {name}")


if __name__ == "__main__":
    main()
