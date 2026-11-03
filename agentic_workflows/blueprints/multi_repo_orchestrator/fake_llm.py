"""Deterministic stand-in for a language model.

Real deployments swap this class for a client with the same three methods.
"""
from __future__ import annotations


class FakeLLM:
    """Answers scout, plan and build calls from a fixed catalogue."""

    def __init__(self, catalogue: dict[str, list[str]] | None = None, rogue_repo: str | None = None):
        # catalogue maps repo name to the keywords that select it.
        self.catalogue = catalogue or {
            "alpha-api": ["api", "endpoint"],
            "beta-web": ["web", "ui", "page"],
            "gamma-docs": ["docs", "readme"],
        }
        self.rogue_repo = rogue_repo  # test hook: this repo writes outside its scope
        self.calls: list[str] = []

    def scout(self, request: str) -> list[str]:
        self.calls.append("scout")
        words = request.lower().split()
        hits = [r for r, keys in self.catalogue.items() if any(k in words for k in keys)]
        return sorted(hits)

    def plan(self, request: str, repos: list[str]) -> list[dict]:
        self.calls.append("plan")
        return [
            {"repo": r, "scope": [f"{r}/src/**", f"{r}/tests/**"], "task": f"{request} ({r})"}
            for r in repos
        ]

    def build(self, task: dict) -> list[str]:
        """Return the file paths this builder wants to write."""
        self.calls.append(f"build:{task['repo']}")
        repo = task["repo"]
        files = [f"{repo}/src/change.py", f"{repo}/tests/test_change.py"]
        if repo == self.rogue_repo:
            files.append(f"{repo}/.claude/settings.json")
        return files
