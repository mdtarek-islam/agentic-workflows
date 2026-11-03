"""Multi-repo orchestrator blueprint.

make_orchestrator picks LangGraph when installed and a local runner otherwise.
Both expose start(request, thread_id) and approve(thread_id, decision).
"""
from __future__ import annotations

from .fake_llm import FakeLLM
from .local_runner import LocalOrchestrator


def make_orchestrator(llm=None, prefer_langgraph: bool = True):
    llm = llm or FakeLLM()
    if prefer_langgraph:
        try:
            from .graph import LangGraphOrchestrator
        except ImportError:
            pass
        else:
            return LangGraphOrchestrator(llm)
    return LocalOrchestrator(llm)


__all__ = ["FakeLLM", "LocalOrchestrator", "make_orchestrator"]
