"""Every diagram in assets/ must parse, animate and use right-angle connectors only."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SVGS = sorted(ASSETS.glob("*.svg"))
NS = "{http://www.w3.org/2000/svg}"
CASE_STUDY_SVGS = ["zoom-cta-orchestrator.svg", "crm-invoicing-pipeline.svg", "tutor-notebooklm-kb.svg"]
TOKEN_RE = re.compile(r"[MLHVmlhv]|-?\d+(?:\.\d+)?")


def segments(d: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Split a path d attribute into absolute point pairs. Reject curves and arcs."""
    tokens = TOKEN_RE.findall(d)
    leftover = TOKEN_RE.sub("", d).replace(",", "").strip()
    assert not leftover, f"unsupported path command in {d!r}: {leftover!r}"
    out, cur, cmd, i = [], None, None, 0
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            continue
        if cmd in "MLml":
            x, y = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if cmd.islower() and cur:
                x, y = cur[0] + x, cur[1] + y
            nxt = (x, y)
            if cmd in "Mm":
                cmd = "l" if cmd == "m" else "L"
                cur = nxt
                continue
        else:
            v = float(tokens[i])
            i += 1
            if cmd == "H":
                nxt = (v, cur[1])
            elif cmd == "h":
                nxt = (cur[0] + v, cur[1])
            elif cmd == "V":
                nxt = (cur[0], v)
            else:
                nxt = (cur[0], cur[1] + v)
        out.append((cur, nxt))
        cur = nxt
    return out


def test_case_study_diagrams_exist():
    for name in CASE_STUDY_SVGS:
        assert (ASSETS / name).is_file(), f"missing assets/{name}"


@pytest.mark.parametrize("svg", SVGS, ids=lambda p: p.name)
def test_svg_parses_and_animates(svg: Path):
    text = svg.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    assert root.tag == f"{NS}svg"
    assert root.find(f"{NS}title") is not None
    assert root.find(f"{NS}desc") is not None
    assert "@keyframes" in text
    assert "prefers-reduced-motion" in text
    assert chr(0x2013) not in text and chr(0x2014) not in text


@pytest.mark.parametrize("svg", SVGS, ids=lambda p: p.name)
def test_svg_paths_are_orthogonal(svg: Path):
    root = ET.fromstring(svg.read_text(encoding="utf-8"))
    for path in root.iter(f"{NS}path"):
        for (x0, y0), (x1, y1) in segments(path.get("d", "")):
            assert x0 == x1 or y0 == y1, f"diagonal segment in {svg.name}: {path.get('d')}"


def test_segment_parser_flags_diagonals():
    assert segments("M0 0 L10 0 V5 h-3") == [((0, 0), (10, 0)), ((10, 0), (10, 5)), ((10, 5), (7, 5))]
    (a, b), = segments("M0 0 L4 4")
    assert a[0] != b[0] and a[1] != b[1]
