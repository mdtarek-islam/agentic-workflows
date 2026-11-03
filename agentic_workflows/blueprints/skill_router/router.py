"""Progressive disclosure skill router.

Stage 1: index only the frontmatter (name, description, keywords).
Stage 2: score a query against the index with keyword and token overlap.
Stage 3: load a skill body on demand. No embeddings, no network.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "is", "it", "my", "this", "that", "with"}


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a simple `key: value` frontmatter block. Returns (meta, body)."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


@dataclass
class SkillEntry:
    name: str
    description: str
    keywords: list[str]
    path: Path


@dataclass
class SkillRouter:
    entries: dict[str, SkillEntry] = field(default_factory=dict)
    loaded: dict[str, str] = field(default_factory=dict)
    body_reads: int = 0

    @classmethod
    def from_dir(cls, root) -> "SkillRouter":
        router = cls()
        for path in sorted(Path(root).glob("*/SKILL.md")):
            # Read frontmatter only; the body is discarded at index time.
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            name = meta.get("name", path.parent.name)
            kws = [k.strip().lower() for k in meta.get("keywords", "").split(",") if k.strip()]
            router.entries[name] = SkillEntry(name, meta.get("description", ""), kws, path)
        return router

    def _idf(self, term: str) -> float:
        n = len(self.entries) or 1
        df = sum(1 for e in self.entries.values() if term in tokens(e.description) or term in e.keywords)
        return math.log(1 + n / (1 + df)) + 1.0

    def score(self, query: str, entry: SkillEntry) -> float:
        q = tokens(query)
        desc = set(tokens(entry.description))
        kws = set(entry.keywords)
        total = 0.0
        for t in q:
            if t in kws:
                total += 3.0 * self._idf(t)  # keyword hits weigh most
            elif t in desc:
                total += 1.0 * self._idf(t)
        return total

    def route(self, query: str, top_k: int = 3, threshold: float = 1.0) -> list[tuple[str, float]]:
        scored = [(e.name, round(self.score(query, e), 4)) for e in self.entries.values()]
        scored = [s for s in scored if s[1] >= threshold]
        return sorted(scored, key=lambda s: (-s[1], s[0]))[:top_k]

    def load(self, name: str) -> str:
        """Read the skill body once, then serve from cache."""
        if name not in self.loaded:
            _, body = parse_frontmatter(self.entries[name].path.read_text(encoding="utf-8"))
            self.loaded[name] = body.strip()
            self.body_reads += 1
        return self.loaded[name]

    def load_for(self, query: str, top_k: int = 1) -> dict[str, str]:
        return {name: self.load(name) for name, _ in self.route(query, top_k=top_k)}
