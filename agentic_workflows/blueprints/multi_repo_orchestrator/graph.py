"""LangGraph backend: scout, plan, approval interrupt, Send fan-out, QA, receipt."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt

from . import nodes


class State(TypedDict, total=False):
    request: str
    repos: list[str]
    tasks: list[dict]
    approved: bool
    results: Annotated[list, operator.add]  # builders append in parallel
    qa: dict
    receipt: dict


class LangGraphOrchestrator:
    backend = "langgraph"

    def __init__(self, llm):
        self.llm = llm
        g = StateGraph(State)
        g.add_node("scout", lambda s: nodes.scout(s, llm))
        g.add_node("plan", lambda s: nodes.plan(s, llm))
        g.add_node("approval", self._approval)
        g.add_node("builder", lambda t: nodes.build(t, llm))
        g.add_node("qa", nodes.qa)
        g.add_node("receipt", nodes.receipt)
        g.add_edge(START, "scout")
        g.add_edge("scout", "plan")
        g.add_conditional_edges("plan", lambda s: "approval" if s["tasks"] else END)
        g.add_conditional_edges("approval", self._fan_out)
        g.add_edge("builder", "qa")
        g.add_edge("qa", "receipt")
        g.add_edge("receipt", END)
        self.graph = g.compile(checkpointer=InMemorySaver())

    @staticmethod
    def _approval(state: State) -> dict:
        decision = interrupt({"tasks": state["tasks"]})
        return {"approved": bool(decision)}

    @staticmethod
    def _fan_out(state: State):
        if not state.get("approved"):
            return END
        return [Send("builder", task) for task in state["tasks"]]

    def _outcome(self, config) -> dict:
        snap = self.graph.get_state(config)
        state = dict(snap.values)
        if snap.next:
            status = "awaiting_approval"
        elif state.get("approved") is False:
            status = "rejected"
        else:
            status = "done"
        return {"status": status, "state": state}

    def start(self, request: str, thread_id: str = "t1") -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        self.graph.invoke({"request": request, "results": []}, config)
        return self._outcome(config)

    def approve(self, thread_id: str, decision: bool) -> dict:
        config = {"configurable": {"thread_id": thread_id}}
        self.graph.invoke(Command(resume=decision), config)
        return self._outcome(config)
