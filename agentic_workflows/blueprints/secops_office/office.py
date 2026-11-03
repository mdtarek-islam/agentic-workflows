"""Multi-agent SecOps office: triage, audits, reviewer. Offline and deterministic.

Event shape: {"files": {path: text}}. Each agent is a plain function.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

SECRET_PATTERNS = {
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic-token": re.compile(r"""(?i)(?:api[_-]?key|token|secret)\s*[=:]\s*['"][A-Za-z0-9_\-]{20,}['"]"""),
}
# Local advisory table: package -> versions below this are vulnerable.
ADVISORIES = {"examplelib": ("2.0.0", "EX-2024-001"), "oldparser": ("1.5.0", "EX-2023-017")}
LICENCE_ALLOW = {"MIT", "BSD-3-Clause", "Apache-2.0", "ISC", "BSD-2-Clause"}
DEP_FILES = ("requirements.txt",)


@dataclass
class Finding:
    agent: str
    severity: str  # "block", "warn"
    message: str


@dataclass
class Report:
    plan: list[str]
    findings: list[Finding] = field(default_factory=list)
    verdict: str = "approve"


def _ver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v))


def triage(event: dict) -> list[str]:
    """Decide which audits to run from the changed files."""
    files = event.get("files", {})
    plan = ["secret_scan"] if files else []
    if any(p.endswith(DEP_FILES) for p in files):
        plan += ["dependency_audit", "licence_check"]
    return plan


def secret_scan(event: dict) -> list[Finding]:
    out = []
    for path, text in event.get("files", {}).items():
        for name, rx in SECRET_PATTERNS.items():
            if rx.search(text):
                out.append(Finding("secret_scan", "block", f"{name} in {path}"))
    return out


def _requirements(event: dict):
    for path, text in event.get("files", {}).items():
        if path.endswith("requirements.txt"):
            for line in text.splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*(?:==\s*([\w.]+))?", line)
                if m and not line.strip().startswith("#"):
                    yield path, m.group(1).lower(), m.group(2)


def dependency_audit(event: dict) -> list[Finding]:
    out = []
    for path, pkg, ver in _requirements(event):
        if pkg in ADVISORIES:
            fixed, ident = ADVISORIES[pkg]
            if ver is None:
                out.append(Finding("dependency_audit", "warn", f"{pkg} unpinned in {path}"))
            elif _ver(ver) < _ver(fixed):
                out.append(Finding("dependency_audit", "block", f"{pkg} {ver} affected by {ident}, fix in {fixed}"))
    return out


def licence_check(event: dict) -> list[Finding]:
    """Check declared licences from event['licences'] (package -> SPDX id)."""
    out = []
    for pkg, lic in event.get("licences", {}).items():
        if lic not in LICENCE_ALLOW:
            out.append(Finding("licence_check", "block", f"{pkg} uses {lic}, not on the allowlist"))
    return out


AGENTS = {"secret_scan": secret_scan, "dependency_audit": dependency_audit, "licence_check": licence_check}


def reviewer(findings: list[Finding]) -> str:
    if any(f.severity == "block" for f in findings):
        return "block"
    return "request_changes" if findings else "approve"


def run_office(event: dict) -> Report:
    plan = triage(event)
    findings: list[Finding] = []
    for step in plan:
        findings += AGENTS[step](event)
    return Report(plan=plan, findings=findings, verdict=reviewer(findings))
