#!/usr/bin/env python3
"""Run explicitly configured application gates without a shell."""

import argparse
import subprocess
from pathlib import Path

from sdlc.contracts import GATES, load_json, require, validate_toolchain


def verify_test_report(path, minimum):
    from defusedxml import ElementTree

    require(path.is_file() and 0 < path.stat().st_size <= 10_000_000, "Missing/oversized JUnit report")
    raw = path.read_bytes()
    require(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "Unsafe XML report")
    root = ElementTree.fromstring(raw, forbid_dtd=True)
    cases = list(root.iter("testcase"))
    executed = [case for case in cases if case.find("skipped") is None]
    require(len(executed) >= minimum, f"Expected at least {minimum} executed tests, found {len(executed)}")
    require(not list(root.iter("failure")) and not list(root.iter("error")), "JUnit report contains failures/errors")
    print(f"Verified {len(executed)} executed application tests.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=(*GATES, "all", "validate"), default="validate")
    args = parser.parse_args()
    root = Path.cwd()
    config = load_json(root / ".github/sdlc/toolchain.json")
    configured = validate_toolchain(config, root)
    if not configured:
        print("Template-only repository: no application code or application gates declared.")
        return
    gates = GATES if args.gate == "all" else (() if args.gate == "validate" else (args.gate,))
    for gate in gates:
        if gate in config["not_applicable"]:
            print(f"{gate}: not applicable: {config['not_applicable'][gate]}")
        report = root / config["test_report"]["path"]
        if gate == "test":
            report.parent.mkdir(parents=True, exist_ok=True)
            report.unlink(missing_ok=True)
        for argv in config["commands"][gate]:
            print(f"Running {gate}: {argv!r}", flush=True)
            subprocess.run(argv, cwd=root, check=True, timeout=900)
        if gate == "test":
            verify_test_report(report, config["test_report"]["minimum_tests"])


if __name__ == "__main__":
    main()
