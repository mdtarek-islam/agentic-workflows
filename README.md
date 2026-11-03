<p align="center"><img src="docs/readme-cover-img.webp" alt="agentic-workflows cover" width="100%"></p>

# agentic-workflows

## 1. Overview

Executable reference blueprints for agentic engineering. Each blueprint is a small Python module with tests. Everything runs offline with fake model stubs, so no API key is needed.

The patterns come from running a fleet of repositories with Claude Code, LangGraph, MCP servers, hooks and multi-agent roles. The code here is a clean, generic rewrite.

## 2. Architecture

![Architecture overview](assets/architecture.svg)

| Blueprint | Diagram |
|---|---|
| Multi-repo orchestrator | ![Orchestrator](assets/multi-repo-orchestrator.svg) |
| AST delta gate | ![Delta gate](assets/ast-delta-gate.svg) |
| PreToolUse hooks | ![Hooks](assets/pretooluse-hooks.svg) |
| Skill router | ![Router](assets/skill-router.svg) |
| SecOps office | ![SecOps](assets/secops-office.svg) |

Design tokens live in [DESIGN.md](DESIGN.md).

## 3. Features

1. **Orchestrator**: scout, plan, approval interrupt, parallel scoped builders through `Send`, QA, signed receipt. Falls back to a local runner when LangGraph is absent.
2. **AST delta gate**: hashes normalised syntax trees. Docstrings, comments and formatting never change a hash. Only structural change triggers regeneration.
3. **Hook pipeline**: blocks secret paths, deletions, prose rule breaks and attribution trailers. Ships in shell and Python.
4. **Skill router**: indexes frontmatter only. Scores by keywords and token overlap. Loads a body on demand.
5. **SecOps office**: triage, secret scan, dependency audit, licence check and a reviewer verdict.

## 4. Quick start

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev,langgraph]"
.venv/bin/pytest -q
```

On Windows use `.venv/Scripts/` in place of `.venv/bin/`. Skip the `langgraph` extra to test the local runner only.

## 5. Configuration

| Item | Where | Note |
|---|---|---|
| Python | `pyproject.toml` | 3.12 or later |
| LangGraph | optional extra `langgraph` | Local runner used when absent |
| Hook wiring | `blueprints/pretooluse_hooks/settings.example.json` | Copy into your own settings |
| Hook scripts | `blueprints/pretooluse_hooks/hooks/` | Need `bash` and `jq` |
| SecOps workflow | `blueprints/secops_office/example-workflow.yml` | Copy to `.github/workflows/` |
| Diagram tokens | `DESIGN.md` | Regenerate with `scripts/generate_svgs.py` |

## 6. Usage

```python
from agentic_workflows.blueprints.multi_repo_orchestrator import make_orchestrator

orch = make_orchestrator()
paused = orch.start("update the api and web page", thread_id="run1")
done = orch.approve("run1", True)
print(done["state"]["receipt"])
```

```python
from agentic_workflows.blueprints.ast_delta_gate import DeltaGate

gate = DeltaGate("graph.json")
gate.run("src", lambda delta: print("regenerate", delta))
```

```bash
echo '{"tool_input":{"command":"rm -rf build"}}' | python -m agentic_workflows.blueprints.pretooluse_hooks.pipeline
```

The last command exits with code 2 and prints the reason.

## 7. Licence and contribution

MIT. See [LICENSE](LICENSE). Open an issue before large changes. Add a failing test first, then the fix.

## 8. Maintenance status

Experimental. The blueprints are reference code and the interfaces may change.
