#!/usr/bin/env python3
"""Check pinned template Python packages against GitHub's public advisory database."""

import os
import re
from pathlib import Path
from urllib.parse import urlencode

from sdlc.contracts import require
from sdlc.github import GitHub


def pinned_packages(path, directory, seen=None):
    seen = set() if seen is None else seen
    path = path.resolve()
    require(path.is_relative_to(directory.resolve()), "Requirements include escapes the tooling directory")
    require(path not in seen, "Repeated or circular requirements include")
    seen.add(path)
    text = path.read_text(encoding="utf-8").replace("\\\n", " ")
    packages = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            packages += pinned_packages(path.parent / line[3:].strip(), directory, seen)
            continue
        match = re.fullmatch(r"([A-Za-z0-9._-]+)==([A-Za-z0-9.!+_-]+)", line.split()[0])
        require(match, "Template tooling dependencies must use explicit package==version pins")
        packages.append(match.groups())
    return packages


def audit(api, packages):
    blockers = []
    for name, version in sorted(set(packages)):
        query = urlencode({"ecosystem": "pip", "affects": f"{name}@{version}"})
        advisories = list(api.pages("/advisories?" + query))
        for advisory in advisories:
            if advisory.get("withdrawn_at"):
                continue
            if advisory["severity"] not in ("low",):
                blockers.append((name, version, advisory["ghsa_id"], advisory["severity"]))
        print(f"Checked public advisories for {name}=={version}.")
    require(not blockers, f"Template dependency advisory policy failed: {blockers}")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    require(token, "A read-only GitHub job token is required for public advisory queries")
    directory = Path("scripts")
    packages = pinned_packages(directory / "requirements-checks.txt", directory)
    require(packages, "No pinned template dependencies discovered")
    audit(GitHub(token), packages)


if __name__ == "__main__":
    main()
