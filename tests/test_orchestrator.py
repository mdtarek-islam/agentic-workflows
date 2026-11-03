import pytest

from agentic_workflows.blueprints.multi_repo_orchestrator import FakeLLM, LocalOrchestrator, make_orchestrator
from agentic_workflows.blueprints.multi_repo_orchestrator.nodes import in_scope


def backends():
    out = [lambda llm: LocalOrchestrator(llm)]
    try:
        import langgraph  # noqa: F401
        out.append(lambda llm: make_orchestrator(llm))
    except ImportError:
        pass
    return out


@pytest.fixture(params=backends())
def factory(request):
    return request.param


def test_pauses_at_approval_gate(factory):
    orch = factory(FakeLLM())
    out = orch.start("update the api and web page", "a")
    assert out["status"] == "awaiting_approval"
    assert out["state"]["repos"] == ["alpha-api", "beta-web"]
    assert not out["state"].get("results")


def test_approved_run_builds_every_repo_and_signs_receipt(factory):
    orch = factory(FakeLLM())
    orch.start("update the api and web page", "b")
    out = orch.approve("b", True)
    assert out["status"] == "done"
    assert {r["repo"] for r in out["state"]["results"]} == {"alpha-api", "beta-web"}
    assert out["state"]["qa"]["passed"]
    assert len(out["state"]["receipt"]["sha256"]) == 64


def test_rejection_runs_no_builders(factory):
    llm = FakeLLM()
    orch = factory(llm)
    orch.start("update the api", "c")
    out = orch.approve("c", False)
    assert out["status"] == "rejected"
    assert not any(c.startswith("build:") for c in llm.calls)


def test_scope_violation_fails_qa(factory):
    orch = factory(FakeLLM(rogue_repo="alpha-api"))
    orch.start("update the api", "d")
    out = orch.approve("d", True)
    assert not out["state"]["qa"]["passed"]
    assert ".claude/settings.json" in out["state"]["qa"]["problems"][0]


def test_no_matching_repo_ends_without_gate(factory):
    out = factory(FakeLLM()).start("something unrelated", "e")
    assert out["status"] == "done"
    assert out["state"]["tasks"] == []


def test_local_fallback_when_langgraph_disabled():
    assert make_orchestrator(prefer_langgraph=False).backend == "local"


def test_in_scope():
    assert in_scope("r/src/a/b.py", ["r/src/**"])
    assert not in_scope("r/.claude/x", ["r/src/**"])
