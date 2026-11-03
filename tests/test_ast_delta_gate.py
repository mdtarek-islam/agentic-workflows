from agentic_workflows.blueprints.ast_delta_gate import DeltaGate, hash_source

BASE = '''
import os

def add(a, b):
    """Add numbers."""
    return a + b

class Box:
    def size(self):
        return 1
'''


def test_formatting_comments_docstrings_ignored():
    other = '''
import os
def add(a,
        b):
    # a comment
    return (a + b)
class Box:
    """new doc"""
    def size(self):

        return 1
'''
    assert hash_source(BASE)["module"] == hash_source(other)["module"]


def test_body_change_is_not_structural(tmp_path):
    (tmp_path / "m.py").write_text(BASE)
    gate = DeltaGate(tmp_path / "g" / "graph.json")
    calls = []
    gate.run(tmp_path, calls.append)
    assert len(calls) == 1  # first run regenerates
    (tmp_path / "m.py").write_text(BASE.replace("a + b", "b + a"))
    res = gate.run(tmp_path, calls.append)
    assert not res.regenerate and len(calls) == 1
    assert res.delta.bodies_changed == ["m.py:add"]


def test_signature_change_triggers(tmp_path):
    (tmp_path / "m.py").write_text(BASE)
    gate = DeltaGate(tmp_path / "graph.json")
    gate.run(tmp_path, lambda d: None)
    (tmp_path / "m.py").write_text(BASE.replace("add(a, b)", "add(a, b, c=0)"))
    res = gate.check(tmp_path)
    assert res.regenerate and res.delta.signatures_changed == ["m.py:add"]


def test_new_symbol_file_and_import_trigger(tmp_path):
    (tmp_path / "m.py").write_text(BASE)
    gate = DeltaGate(tmp_path / "graph.json")
    gate.run(tmp_path, lambda d: None)
    (tmp_path / "m.py").write_text(BASE + "\ndef extra():\n    pass\n")
    assert gate.check(tmp_path).delta.symbols_added == ["m.py:extra"]
    gate.save(tmp_path)
    (tmp_path / "m.py").write_text(BASE.replace("import os", "import sys"))
    assert gate.check(tmp_path).delta.imports_changed == ["m.py"]
    gate.save(tmp_path)
    (tmp_path / "n.py").write_text("x = 1\n")
    assert gate.check(tmp_path).delta.files_added == ["n.py"]


def test_hash_is_deterministic():
    assert hash_source(BASE) == hash_source(BASE)
