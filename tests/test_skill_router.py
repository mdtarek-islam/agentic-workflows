from pathlib import Path

import pytest

from agentic_workflows.blueprints.skill_router import SkillRouter, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1] / "agentic_workflows/blueprints/skill_router/example_skills"


@pytest.fixture
def router():
    return SkillRouter.from_dir(ROOT)


def test_frontmatter():
    meta, body = parse_frontmatter("---\nname: x\nkeywords: a, b\n---\nBody")
    assert meta == {"name": "x", "keywords": "a, b"} and body == "Body"


def test_index_reads_no_bodies(router):
    assert set(router.entries) == {"ci-debug", "readme-writer", "db-migration"}
    assert router.body_reads == 0


@pytest.mark.parametrize("query,expected", [
    ("my pipeline build is failing", "ci-debug"),
    ("refresh the readme diagram", "readme-writer"),
    ("write a schema migration with rollback", "db-migration"),
])
def test_routes_to_best_skill(router, query, expected):
    assert router.route(query)[0][0] == expected


def test_no_match_returns_empty(router):
    assert router.route("bake a sourdough loaf") == []


def test_load_on_demand_and_cache(router):
    loaded = router.load_for("fix the failing workflow")
    assert list(loaded) == ["ci-debug"] and "Read the failing job log" in loaded["ci-debug"]
    router.load("ci-debug")
    assert router.body_reads == 1


def test_scores_deterministic(router):
    assert router.route("sql migration") == router.route("sql migration")
