"""Tiny state-machine runner. Same interface as the LangGraph backend."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from . import nodes


class LocalOrchestrator:
    backend = "local"

    def __init__(self, llm):
        self.llm = llm
        self._paused: dict[str, dict] = {}

    def start(self, request: str, thread_id: str = "t1") -> dict:
        state = {"request": request, "results": []}
        state.update(nodes.scout(state, self.llm))
        state.update(nodes.plan(state, self.llm))
        if not state["tasks"]:
            return {"status": "done", "state": state}
        self._paused[thread_id] = state  # approval gate: stop and wait
        return {"status": "awaiting_approval", "state": state}

    def approve(self, thread_id: str, decision: bool) -> dict:
        state = self._paused.pop(thread_id)
        state["approved"] = bool(decision)
        if not decision:
            return {"status": "rejected", "state": state}
        with ThreadPoolExecutor(max_workers=max(1, len(state["tasks"]))) as pool:
            outs = list(pool.map(lambda t: nodes.build(t, self.llm), state["tasks"]))
        for out in outs:
            state["results"].extend(out["results"])
        state.update(nodes.qa(state))
        state.update(nodes.receipt(state))
        return {"status": "done", "state": state}
