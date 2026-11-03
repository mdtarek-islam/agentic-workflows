"""PreToolUse hook pipeline.

Contract: JSON on stdin, exit 0 to allow, exit 2 to block (reason on stderr).
Payload shape: {"tool_name": str, "tool_input": {...}, "cwd": str}.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

ALLOW, BLOCK = 0, 2
Result = tuple[int, str]

BANNED_WORDS = (
    "delve leverage tapestry testament seamless seamlessly cutting-edge game-changer unlock "
    "unleash elevate foster realm paradigm beacon underscore pivotal meticulous embark "
    "symphony robust"
).split()
PROSE_SUFFIXES = (".md", ".svg", ".html")

SECRET_RE = re.compile(
    r"""(^|[/\\\s"'=])(\.env(\.[A-Za-z0-9_-]+)?|[^/\\\s"']*\.(pem|key)|id_rsa[^/\\\s"']*|id_ed25519[^/\\\s"']*)($|[\s"';|&])"""
    r"""|[/\\]secrets[/\\]""",
    re.IGNORECASE,
)
DESTRUCTIVE_RE = re.compile(
    r"(^|[;&|]\s*|\s)(rm|rmdir|unlink)\s|git\s+(rm|clean)\b|git\s+reset\s+--hard|git\s+branch\s+-D\b"
)
COMMIT_RE = re.compile(r"\bgit\s+(-C\s+\S+\s+)?commit\b|\bgh\s+pr\b", re.IGNORECASE)
ATTRIBUTION_RE = re.compile(r"co-authored-by|\bclaude\b|anthropic|generated with", re.IGNORECASE)
TRAILER_RE = re.compile(r"^\s*(co-authored-by:.*|.*generated with \[?claude.*)\n?", re.IGNORECASE | re.MULTILINE)


def _command(p: dict) -> str:
    return p.get("tool_input", {}).get("command", "") or ""


def _target_text(p: dict) -> str:
    ti = p.get("tool_input", {})
    keys = ("file_path", "path", "pattern", "glob", "command")
    return "\n".join(str(ti[k]) for k in keys if ti.get(k))


def block_secret_paths(p: dict) -> Result:
    text = re.sub(r"""[^\s"'/\\]*\.example""", "", _target_text(p))  # example files stay readable
    if SECRET_RE.search(text):
        return BLOCK, "Secret file access refused. Use the .example file."
    return ALLOW, ""


def archive_destructive(p: dict) -> Result:
    cmd = _command(p)
    if cmd and DESTRUCTIVE_RE.search(cmd):
        return BLOCK, "Deletion refused. Move the file to .dump/<repo>/<file>.<YYYYMMDD-HHMMSS>.bak instead."
    return ALLOW, ""


def archive_path(path, dump_root, repo: str, now: datetime | None = None) -> Path:
    """Move path to <dump_root>/<repo>/<name>.<timestamp>.bak and return the new location."""
    src = Path(path)
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    dest = Path(dump_root) / repo / f"{src.name}.{stamp}.bak"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return dest


def prose_guard(p: dict) -> Result:
    ti = p.get("tool_input", {})
    path = str(ti.get("file_path", ""))
    if not path.lower().endswith(PROSE_SUFFIXES):
        return ALLOW, ""
    text = ti.get("content") or ti.get("new_string") or ""
    if "—" in text or "–" in text:
        return BLOCK, "Dash characters found. Use a comma, colon, full stop or the word 'to'."
    if any(0x1F300 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF for c in text):
        return BLOCK, "Emoji found. Remove it."
    for word in BANNED_WORDS:
        if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text, re.IGNORECASE):
            return BLOCK, f"Banned word '{word}'. Rewrite the sentence."
    return ALLOW, ""


def strip_trailers(message: str) -> str:
    """Remove attribution trailers from a commit message."""
    return TRAILER_RE.sub("", message).rstrip() + "\n"


def coauthor_guard(p: dict) -> Result:
    cmd = _command(p)
    if cmd and COMMIT_RE.search(cmd) and ATTRIBUTION_RE.search(cmd):
        return BLOCK, "Attribution trailer found. Remove it; the owner is the sole author."
    return ALLOW, ""


HOOKS: dict[str, Callable[[dict], Result]] = {
    "block_secret_paths": block_secret_paths,
    "archive_destructive": archive_destructive,
    "prose_guard": prose_guard,
    "coauthor_guard": coauthor_guard,
}


def run_pipeline(payload: dict, names: list[str] | None = None) -> Result:
    """Run hooks in order. The first block wins."""
    for name in names or list(HOOKS):
        code, msg = HOOKS[name](payload)
        if code != ALLOW:
            return code, f"[{name}] {msg}"
    return ALLOW, ""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return ALLOW  # malformed input never blocks
    code, msg = run_pipeline(payload, argv or None)
    if msg:
        print(msg, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
