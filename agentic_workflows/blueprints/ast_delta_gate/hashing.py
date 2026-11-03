"""Deterministic structural hashing of Python source.

Comments, formatting and docstrings never reach the hash.
Each symbol gets a signature hash (public shape) and a body hash.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".dump", ".extra", "build", "dist"}
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, *DEFS)):
            body = node.body
            first = body[0] if body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _dump(node) -> str:
    items = node if isinstance(node, list) else [node]
    return "|".join(ast.dump(n, annotate_fields=True, include_attributes=False) for n in items)


def _signature(node) -> str:
    if isinstance(node, ast.ClassDef):
        return _dump([*node.bases, *node.keywords, *node.decorator_list])
    parts = [_dump(node.args), _dump(node.decorator_list)]
    if node.returns is not None:
        parts.append(_dump(node.returns))
    return "|".join(parts)


def hash_source(source: str) -> dict:
    """Return {'imports': [...], 'symbols': {qualname: {'sig','body'}}, 'module': hash}."""
    tree = _strip_docstrings(ast.parse(source))
    imports: set[str] = set()
    symbols: dict[str, dict] = {}

    def visit(body, prefix=""):
        for node in body:
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
            elif isinstance(node, DEFS):
                name = prefix + node.name
                if isinstance(node, ast.ClassDef):
                    rest = [n for n in node.body if not isinstance(n, DEFS)]
                    body_hash = _h(_dump(rest))
                else:
                    body_hash = _h(_dump(node.body))
                symbols[name] = {"sig": _h(_signature(node)), "body": body_hash}
                visit(node.body, name + ".")

    visit(tree.body)
    return {"imports": sorted(imports), "symbols": symbols, "module": _h(_dump(tree))}


def hash_repo(root) -> dict[str, dict]:
    root = Path(root)
    out: dict[str, dict] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        try:
            out[rel.as_posix()] = hash_source(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            out[rel.as_posix()] = {"imports": [], "symbols": {}, "module": "unparseable"}
    return out
