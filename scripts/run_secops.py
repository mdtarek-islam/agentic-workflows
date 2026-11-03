"""Run the SecOps office on files changed against a base ref. Exit 1 on block."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from agentic_workflows.blueprints.secops_office import run_office


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    args = ap.parse_args()
    names = subprocess.run(["git", "diff", "--name-only", args.base], capture_output=True, text=True, check=True).stdout.split()
    files = {n: Path(n).read_text(encoding="utf-8", errors="ignore") for n in names if Path(n).is_file()}
    report = run_office({"files": files})
    for f in report.findings:
        print(f"{f.severity.upper()} {f.agent}: {f.message}")
    print(f"verdict: {report.verdict}")
    return 1 if report.verdict == "block" else 0


if __name__ == "__main__":
    sys.exit(main())
