"""Pure node functions shared by both runners.

Each node takes the state dict and returns a partial update.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json


def in_scope(path: str, scope: list[str]) -> bool:
    """True when path matches one scope glob. `**` crosses folders."""
    return any(fnmatch.fnmatch(path, pat) for pat in scope)


def scout(state: dict, llm) -> dict:
    return {"repos": llm.scout(state["request"])}


def plan(state: dict, llm) -> dict:
    if not state["repos"]:
        return {"tasks": []}
    return {"tasks": llm.plan(state["request"], state["repos"])}


def build(task: dict, llm) -> dict:
    """Run one scoped builder. Writes outside the scope count as violations."""
    wanted = llm.build(task)
    allowed = [p for p in wanted if in_scope(p, task["scope"])]
    rejected = [p for p in wanted if p not in allowed]
    return {
        "results": [
            {"repo": task["repo"], "written": allowed, "rejected": rejected, "ok": not rejected}
        ]
    }


def qa(state: dict) -> dict:
    results = state.get("results", [])
    planned = {t["repo"] for t in state.get("tasks", [])}
    done = {r["repo"] for r in results}
    problems = []
    if planned - done:
        problems.append("missing results: " + ", ".join(sorted(planned - done)))
    for r in results:
        if not r["ok"]:
            problems.append(f"{r['repo']} wrote outside scope: {', '.join(r['rejected'])}")
    return {"qa": {"passed": not problems, "problems": problems}}


def receipt(state: dict) -> dict:
    body = {
        "request": state["request"],
        "tasks": state["tasks"],
        "results": sorted(state.get("results", []), key=lambda r: r["repo"]),
        "qa": state["qa"],
    }
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return {"receipt": {"sha256": digest, "passed": state["qa"]["passed"], "repos": len(body["results"])}}
