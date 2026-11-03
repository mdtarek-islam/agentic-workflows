"""Delta gate: regenerate README or diagrams only on structural change."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .hashing import hash_repo


@dataclass
class Delta:
    files_added: list[str] = field(default_factory=list)
    files_removed: list[str] = field(default_factory=list)
    symbols_added: list[str] = field(default_factory=list)
    symbols_removed: list[str] = field(default_factory=list)
    signatures_changed: list[str] = field(default_factory=list)
    imports_changed: list[str] = field(default_factory=list)
    bodies_changed: list[str] = field(default_factory=list)  # internal only

    @property
    def structural(self) -> bool:
        return any([self.files_added, self.files_removed, self.symbols_added,
                    self.symbols_removed, self.signatures_changed, self.imports_changed])


def diff_graphs(old: dict, new: dict) -> Delta:
    d = Delta()
    d.files_added = sorted(set(new) - set(old))
    d.files_removed = sorted(set(old) - set(new))
    for f in sorted(set(old) & set(new)):
        o, n = old[f], new[f]
        if o["module"] == n["module"]:
            continue
        if o["imports"] != n["imports"]:
            d.imports_changed.append(f)
        os_, ns = o["symbols"], n["symbols"]
        d.symbols_added += [f"{f}:{s}" for s in sorted(set(ns) - set(os_))]
        d.symbols_removed += [f"{f}:{s}" for s in sorted(set(os_) - set(ns))]
        for s in sorted(set(os_) & set(ns)):
            if os_[s]["sig"] != ns[s]["sig"]:
                d.signatures_changed.append(f"{f}:{s}")
            elif os_[s]["body"] != ns[s]["body"]:
                d.bodies_changed.append(f"{f}:{s}")
    return d


@dataclass
class GateResult:
    regenerate: bool
    delta: Delta


class DeltaGate:
    def __init__(self, graph_path):
        self.graph_path = Path(graph_path)

    def load(self) -> dict:
        if self.graph_path.exists():
            return json.loads(self.graph_path.read_text(encoding="utf-8"))
        return {}

    def check(self, root) -> GateResult:
        old = self.load()
        new = hash_repo(root)
        delta = diff_graphs(old, new)
        # First run (no stored graph) always regenerates.
        return GateResult(regenerate=(not old) or delta.structural, delta=delta)

    def save(self, root) -> None:
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        self.graph_path.write_text(json.dumps(hash_repo(root), indent=2, sort_keys=True), encoding="utf-8")

    def run(self, root, regenerate: Callable[[Delta], None]) -> GateResult:
        """Check, call the generator only on structural change, then store the graph."""
        result = self.check(root)
        if result.regenerate:
            regenerate(result.delta)
        self.save(root)
        return result
