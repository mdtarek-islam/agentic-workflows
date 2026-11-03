import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from agentic_workflows.blueprints.pretooluse_hooks import (
    ALLOW, BLOCK, archive_path, run_pipeline, strip_trailers)
from agentic_workflows.blueprints.pretooluse_hooks.pipeline import main

HOOKS_DIR = Path(__file__).resolve().parents[1] / "agentic_workflows/blueprints/pretooluse_hooks/hooks"


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def write(path, content):
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": content}}


CASES = [
    (bash("cat .env"), BLOCK),
    (bash("cat .env.example"), ALLOW),
    ({"tool_input": {"file_path": "/x/server.pem"}}, BLOCK),
    (bash("ls secrets/"), ALLOW),  # no leading separator before folder name
    (bash("cat /repo/secrets/a.txt"), BLOCK),
    (bash("rm -rf build"), BLOCK),
    (bash("git clean -fd"), BLOCK),
    (bash("git status"), ALLOW),
    (bash("git commit -m 'x\n\nCo-Authored-By: Bot <b@x.io>'"), BLOCK),
    (bash("git commit -m 'fix parser'"), ALLOW),
    (write("a.md", "plain text"), ALLOW),
    (write("a.md", "bad — dash"), BLOCK),
    (write("a.md", "we leverage it"), BLOCK),
    (write("a.py", "leverage = 1"), ALLOW),
]


@pytest.mark.parametrize("payload,expected", CASES)
def test_python_pipeline(payload, expected):
    assert run_pipeline(payload)[0] == expected


def test_strip_trailers():
    msg = "feat: x\n\nbody\n\nCo-Authored-By: Bot <b@x.io>\n"
    assert strip_trailers(msg) == "feat: x\n\nbody\n"


def test_archive_path_moves_with_timestamp(tmp_path):
    f = tmp_path / "old.txt"
    f.write_text("data")
    dest = archive_path(f, tmp_path / ".dump", "repo", datetime(2026, 1, 2, 3, 4, 5))
    assert not f.exists()
    assert dest.name == "old.txt.20260102-030405.bak"
    assert dest.read_text() == "data"


def test_cli_exit_codes(monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(bash("rm x"))))
    assert main([]) == 2
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert main([]) == 0


def test_settings_example_is_valid_json():
    data = json.loads((HOOKS_DIR.parent / "settings.example.json").read_text())
    assert "PreToolUse" in data["hooks"]


SHELL_CASES = [
    ("block-secret-files.sh", bash("cat .env"), 2),
    ("block-secret-files.sh", bash("cat .env.example"), 0),
    ("archive-destructive.sh", bash("rm -rf x"), 2),
    ("archive-destructive.sh", bash("git log"), 0),
    ("strip-coauthor.sh", bash("git commit -m 'a' -m 'Co-Authored-By: B <b@x.io>'"), 2),
    ("strip-coauthor.sh", bash("git commit -m 'a'"), 0),
    ("guard-prose.sh", write("a.md", "a — b"), 2),
    ("guard-prose.sh", write("a.md", "all good"), 0),
]


@pytest.mark.skipif(not (shutil.which("bash") and shutil.which("jq")), reason="needs bash and jq")
@pytest.mark.parametrize("script,payload,expected", SHELL_CASES)
def test_shell_hooks(script, payload, expected):
    r = subprocess.run(["bash", str(HOOKS_DIR / script)], input=json.dumps(payload), text=True,
                       capture_output=True)
    assert r.returncode == expected, r.stderr
