#!/usr/bin/env python3
"""GitHub Actions entry point; do not run with credentials against PR code."""

import argparse
import os
from pathlib import Path

from sdlc.controller import Controller
from sdlc.github import GitHub


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("reconcile", "setup", "pause", "resume"), default="reconcile")
    parser.add_argument("--root", type=int)
    args = parser.parse_args()
    if os.environ.get("SDLC_ENABLED") != "true":
        raise ValueError("Set repository variable SDLC_ENABLED=true after completing docs/setup.md")
    token = os.environ.get("SDLC_TOKEN")
    if not token:
        raise ValueError("Missing SDLC_TOKEN user token; see docs/setup.md")
    controller = Controller(GitHub(token), os.environ["GITHUB_REPOSITORY"], Path.cwd())
    if args.action == "setup":
        controller.setup()
    else:
        controller.reconcile(args.action, args.root, os.environ.get("GITHUB_ACTOR"))


if __name__ == "__main__":
    main()
