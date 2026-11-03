"""Generate the animated orthogonal SVG diagrams in assets/.

Run: python scripts/generate_svgs.py
Palette: violet accent on night, amber to orange to rose ramp.
Every connector uses right angles only. Motion stops under prefers-reduced-motion.
"""
from __future__ import annotations

from pathlib import Path

NIGHT, PANEL, VIOLET, TEXT, MUTED = "#0B0F19", "#141A2A", "#7C3AED", "#E5E7EB", "#9CA3AF"
RAMP = ["#FBBF24", "#F97316", "#F43F5E"]

# node: (id, x, y, w, h, title, subtitle, accent)
# edge: (points, ramp_index)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def render(title: str, w: int, h: int, nodes: list, edges: list, caption: str) -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">',
        f"<title id=\"t\">{esc(title)}</title><desc id=\"d\">{esc(caption)}</desc>",
        "<style>",
        f"text{{font-family:'Inter','Segoe UI',Arial,sans-serif;fill:{TEXT}}}",
        ".h{font-size:22px;font-weight:700}.n{font-size:15px;font-weight:600}.s{font-size:12px;fill:" + MUTED + "}",
        ".e{fill:none;stroke-width:2.5;stroke-dasharray:8 8;animation:flow 1.6s linear infinite}",
        "@keyframes flow{to{stroke-dashoffset:-32}}",
        ".p{animation:pulse 3s ease-in-out infinite}@keyframes pulse{50%{opacity:.75}}",
        "@media (prefers-reduced-motion:reduce){.e,.p{animation:none}}",
        "</style>",
        f'<rect width="{w}" height="{h}" fill="{NIGHT}"/>',
        f'<text x="30" y="42" class="h">{esc(title)}</text>',
        f'<text x="30" y="64" class="s">{esc(caption)}</text>',
    ]
    for pts, ri in edges:
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        out.append(f'<path d="{d}" class="e" stroke="{RAMP[ri % 3]}"/>')
        x, y = pts[-1]
        px, py = pts[-2]
        if x > px:
            tri = f"{x} {y} {x-9} {y-5} {x-9} {y+5}"
        elif x < px:
            tri = f"{x} {y} {x+9} {y-5} {x+9} {y+5}"
        elif y > py:
            tri = f"{x} {y} {x-5} {y-9} {x+5} {y-9}"
        else:
            tri = f"{x} {y} {x-5} {y+9} {x+5} {y+9}"
        out.append(f'<polygon points="{tri}" fill="{RAMP[ri % 3]}"/>')
    for i, (nid, x, y, nw, nh, t, sub, accent) in enumerate(nodes):
        stroke = VIOLET if accent else "#2A3350"
        cls = ' class="p"' if accent else ""
        out.append(f'<g id="{nid}"{cls}><rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="10" fill="{PANEL}" stroke="{stroke}" stroke-width="2"/>')
        out.append(f'<text x="{x + nw/2}" y="{y + nh/2 - 2}" text-anchor="middle" class="n">{esc(t)}</text>')
        out.append(f'<text x="{x + nw/2}" y="{y + nh/2 + 16}" text-anchor="middle" class="s">{esc(sub)}</text></g>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def orchestrator():
    nodes = [
        ("scout", 30, 150, 120, 60, "Scout", "find repos", False),
        ("plan", 190, 150, 120, 60, "Plan", "scoped tasks", False),
        ("gate", 350, 150, 130, 60, "Approval gate", "interrupt", True),
        ("b1", 540, 80, 130, 50, "Builder A", "scope A", False),
        ("b2", 540, 155, 130, 50, "Builder B", "scope B", False),
        ("b3", 540, 230, 130, 50, "Builder C", "scope C", False),
        ("qa", 730, 150, 100, 60, "QA", "scope check", False),
        ("rc", 860, 150, 80, 60, "Receipt", "sha256", False),
    ]
    edges = [
        ([(150, 180), (190, 180)], 0), ([(310, 180), (350, 180)], 0), ([(480, 180), (510, 180), (510, 105), (540, 105)], 1),
        ([(510, 180), (540, 180)], 1), ([(510, 180), (510, 255), (540, 255)], 1),
        ([(670, 105), (700, 105), (700, 170), (730, 170)], 2), ([(670, 180), (730, 180)], 2),
        ([(670, 255), (700, 255), (700, 190), (730, 190)], 2), ([(830, 180), (860, 180)], 0),
    ]
    return render("Multi-repo orchestrator", 960, 340, nodes, edges,
                  "Scout, plan, pause for approval, fan out scoped builders, check, sign a receipt.")


def delta_gate():
    nodes = [
        ("src", 30, 140, 130, 60, "Source tree", "*.py files", False),
        ("ast", 210, 140, 130, 60, "Normalise", "strip docstrings", False),
        ("hash", 390, 140, 130, 60, "Hash", "sig and body", False),
        ("diff", 570, 140, 130, 60, "Diff", "vs stored graph", True),
        ("regen", 760, 70, 170, 60, "Regenerate", "README and SVG", False),
        ("skip", 760, 220, 170, 60, "Skip", "internal edits only", False),
    ]
    edges = [
        ([(160, 170), (210, 170)], 0), ([(340, 170), (390, 170)], 0), ([(520, 170), (570, 170)], 0),
        ([(700, 170), (730, 170), (730, 100), (760, 100)], 1), ([(700, 170), (730, 170), (730, 250), (760, 250)], 2),
    ]
    return render("AST delta gate", 960, 320, nodes, edges,
                  "Structural change triggers regeneration. Body edits do not.")


def hooks():
    nodes = [
        ("call", 30, 140, 130, 60, "Tool call", "JSON on stdin", False),
        ("h1", 210, 60, 160, 50, "Secret paths", "exit 2 on match", False),
        ("h2", 210, 130, 160, 50, "Destructive cmds", "archive instead", False),
        ("h3", 210, 200, 160, 50, "Prose guard", "dashes, banned words", False),
        ("h4", 210, 270, 160, 50, "Trailer strip", "no attribution", False),
        ("v", 440, 160, 120, 60, "Verdict", "first block wins", True),
        ("ok", 640, 100, 130, 50, "Allow", "exit 0", False),
        ("no", 640, 230, 130, 50, "Block", "exit 2 plus reason", False),
    ]
    edges = [
        ([(160, 170), (185, 170), (185, 85), (210, 85)], 0), ([(160, 170), (185, 170), (185, 155), (210, 155)], 0),
        ([(160, 170), (185, 170), (185, 225), (210, 225)], 0), ([(160, 170), (185, 170), (185, 295), (210, 295)], 0),
        ([(370, 85), (405, 85), (405, 180), (440, 180)], 1), ([(370, 155), (440, 155)], 1),
        ([(370, 225), (405, 225), (405, 200), (440, 200)], 1), ([(370, 295), (415, 295), (415, 210), (440, 210)], 1),
        ([(560, 180), (600, 180), (600, 125), (640, 125)], 2), ([(560, 200), (600, 200), (600, 255), (640, 255)], 2),
    ]
    return render("PreToolUse hook pipeline", 960, 350, nodes, edges,
                  "Four checks run in order. One block stops the tool call.")


def router():
    nodes = [
        ("q", 30, 140, 120, 60, "Query", "user request", False),
        ("idx", 200, 140, 150, 60, "Skill index", "frontmatter only", False),
        ("sc", 400, 140, 140, 60, "Score", "keywords plus tokens", True),
        ("top", 590, 140, 120, 60, "Top match", "above threshold", False),
        ("load", 760, 140, 170, 60, "Load body", "on demand, cached", False),
    ]
    edges = [([(150, 170), (200, 170)], 0), ([(350, 170), (400, 170)], 0),
             ([(540, 170), (590, 170)], 1), ([(710, 170), (760, 170)], 2)]
    return render("Skill router", 960, 280, nodes, edges,
                  "Index metadata first. Read a skill body only after a match.")


def secops():
    nodes = [
        ("ev", 30, 150, 120, 60, "Event", "changed files", False),
        ("tri", 190, 150, 120, 60, "Triage", "pick audits", True),
        ("a1", 380, 70, 160, 50, "Secret scan", "regex rules", False),
        ("a2", 380, 150, 160, 50, "Dependency audit", "advisory table", False),
        ("a3", 380, 230, 160, 50, "Licence check", "allowlist", False),
        ("rev", 620, 150, 130, 60, "Reviewer", "merge findings", False),
        ("ver", 800, 150, 130, 60, "Verdict", "approve or block", False),
    ]
    edges = [
        ([(150, 180), (190, 180)], 0), ([(310, 180), (345, 180), (345, 95), (380, 95)], 1),
        ([(310, 180), (380, 180)], 1), ([(310, 180), (345, 180), (345, 255), (380, 255)], 1),
        ([(540, 95), (580, 95), (580, 170), (620, 170)], 2), ([(540, 175), (620, 175)], 2),
        ([(540, 255), (580, 255), (580, 190), (620, 190)], 2), ([(750, 180), (800, 180)], 0),
    ]
    return render("SecOps office", 960, 320, nodes, edges,
                  "Triage routes a change to three audits. A reviewer sets the verdict.")


def overview():
    nodes = [
        ("o", 40, 100, 200, 70, "Multi-repo orchestrator", "LangGraph or local runner", True),
        ("d", 40, 200, 200, 70, "AST delta gate", "structural hashing", False),
        ("h", 380, 100, 200, 70, "PreToolUse hooks", "block, archive, guard", False),
        ("r", 380, 200, 200, 70, "Skill router", "progressive disclosure", False),
        ("s", 720, 150, 200, 70, "SecOps office", "triage to verdict", False),
        ("core", 380, 310, 200, 60, "Offline test suite", "fake LLM stubs", False),
    ]
    edges = [
        ([(240, 135), (380, 135)], 0), ([(240, 235), (310, 235), (310, 135), (380, 135)], 1),
        ([(580, 135), (650, 135), (650, 185), (720, 185)], 2), ([(580, 235), (650, 235), (650, 185), (720, 185)], 2),
        ([(480, 270), (480, 310)], 0),
    ]
    return render("agentic-workflows architecture", 960, 400, nodes, edges,
                  "Five blueprints share one rule: run offline, test first, gate every change.")


# Case-study diagrams. These draw documented live deployments. No case-study code ships here.
# zone: (x, y, w, h, label, ramp_index)
# card: (id, x, y, w, h, kicker, title_lines, subtitle, accent)
# label: (x, y, text)


def arrow(pts: list, colour: str) -> list[str]:
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    x, y = pts[-1]
    px, py = pts[-2]
    if x > px:
        tri = f"{x} {y} {x-9} {y-5} {x-9} {y+5}"
    elif x < px:
        tri = f"{x} {y} {x+9} {y-5} {x+9} {y+5}"
    elif y > py:
        tri = f"{x} {y} {x-5} {y-9} {x+5} {y-9}"
    else:
        tri = f"{x} {y} {x-5} {y+9} {x+5} {y+9}"
    return [f'<path d="{d}" class="e" stroke="{colour}"/>', f'<polygon points="{tri}" fill="{colour}"/>']


def render_case(title: str, w: int, h: int, zones: list, cards: list, edges: list,
                labels: list, caption: str) -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">',
        f"<title id=\"t\">{esc(title)}</title><desc id=\"d\">{esc(caption)}</desc>",
        "<style>",
        f"text{{font-family:'Inter','Segoe UI',Arial,sans-serif;fill:{TEXT}}}",
        ".h{font-size:22px;font-weight:700}.n{font-size:15px;font-weight:600}.s{font-size:12px;fill:" + MUTED + "}",
        ".k{font-size:11px;font-weight:700;letter-spacing:1px}.z{font-size:13px;font-weight:600}",
        ".e{fill:none;stroke-width:2.5;stroke-dasharray:8 8;animation:flow 1.6s linear infinite}",
        "@keyframes flow{to{stroke-dashoffset:-32}}",
        ".p{animation:pulse 3s ease-in-out infinite}@keyframes pulse{50%{opacity:.75}}",
        "@media (prefers-reduced-motion:reduce){.e,.p{animation:none}}",
        "</style>",
        f'<rect width="{w}" height="{h}" fill="{NIGHT}"/>',
        f'<text x="30" y="42" class="h">{esc(title)}</text>',
        f'<text x="30" y="64" class="s">{esc(caption)}</text>',
    ]
    for x, y, zw, zh, label, ri in zones:
        out.append(f'<rect x="{x}" y="{y}" width="{zw}" height="{zh}" rx="12" fill="#0F1422" '
                   f'stroke="{RAMP[ri % 3]}" stroke-opacity=".55" stroke-width="1.5" stroke-dasharray="4 4"/>')
        out.append(f'<text x="{x + 14}" y="{y + 22}" class="z" fill="{RAMP[ri % 3]}" style="fill:{RAMP[ri % 3]}">{esc(label)}</text>')
    for pts, ri in edges:
        out.extend(arrow(pts, RAMP[ri % 3]))
    for cid, x, y, cw, ch, kicker, lines, sub, accent in cards:
        stroke = VIOLET if accent else "#2A3350"
        cls = ' class="p"' if accent else ""
        rows = 1 + len(lines) + (1 if sub else 0)
        top = y + ch / 2 - (rows - 1) * 9 + 4
        out.append(f'<g id="{cid}"{cls}><rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="{PANEL}" stroke="{stroke}" stroke-width="2"/>')
        cx = x + cw / 2
        out.append(f'<text x="{cx}" y="{top}" text-anchor="middle" class="k" style="fill:{VIOLET if accent else RAMP[0]}">{esc(kicker)}</text>')
        for j, line in enumerate(lines):
            out.append(f'<text x="{cx}" y="{top + 18 * (j + 1)}" text-anchor="middle" class="n">{esc(line)}</text>')
        if sub:
            out.append(f'<text x="{cx}" y="{top + 18 * (len(lines) + 1)}" text-anchor="middle" class="s">{esc(sub)}</text>')
        out.append("</g>")
    for x, y, text in labels:
        out.append(f'<text x="{x}" y="{y}" text-anchor="middle" class="s">{esc(text)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def zoom_cta():
    zones = [
        (20, 90, 280, 330, "Gmail Department [Steps 1 and 5]", 0),
        (330, 90, 300, 150, "Zoom Department [Step 2]", 1),
        (660, 90, 280, 150, "Processing Department [Step 3]", 2),
        (660, 270, 280, 150, "Boss Approval Office [Step 4]", 2),
        (20, 450, 920, 130, "Team Recipients [Step 6]", 0),
    ]
    cards = [
        ("s1", 40, 125, 240, 90, "STEP 1", ["Receive transcript"], "Zoom transcript email arrives", False),
        ("s2", 360, 125, 240, 90, "STEP 2", ["Parse transcript"], "Zoom transcript read in full", False),
        ("s3", 680, 125, 240, 90, "STEP 3", ["Extract and draft"], "actions, owners, deadlines", False),
        ("s4", 680, 305, 240, 90, "STEP 4", ["Review and approve"], "the boss signs off the draft", True),
        ("s5", 40, 305, 240, 90, "STEP 5", ["Send approved email"], "only after sign-off", False),
        ("s6", 360, 480, 240, 80, "STEP 6", ["Team receives"], "actions and deadlines", False),
    ]
    edges = [
        ([(280, 170), (360, 170)], 0),
        ([(600, 170), (680, 170)], 1),
        ([(800, 215), (800, 305)], 2),
        ([(680, 350), (280, 350)], 2),
        ([(250, 395), (250, 520), (360, 520)], 0),
    ]
    labels = [(470, 338, "approved draft only"), (470, 375, "a person approves every email")]
    return render_case("Zoom transcript-to-CTA email orchestrator", 960, 600, zones, cards, edges, labels,
                       "Six steps across five departments. A person approves every email before dispatch.")


def crm_invoicing():
    cards = [
        ("c1", 30, 120, 200, 110, "STAGE 1", ["Windows Task", "Scheduler"], "weekly unattended trigger", False),
        ("c2", 270, 120, 200, 110, "STAGE 2", ["Bespoke Task and", "Pricing Matrix Reader"], "task to pricing tier", False),
        ("c3", 510, 120, 200, 110, "STAGE 3", ["Validation", "Engine"], "checks tier and amount", True),
        ("c4", 750, 120, 200, 110, "STAGE 4", ["Automated Weekly", "CRM Commit"], "Power Automate", False),
    ]
    edges = [
        ([(230, 175), (270, 175)], 0),
        ([(470, 175), (510, 175)], 1),
        ([(710, 175), (750, 175)], 2),
        ([(850, 230), (850, 270), (130, 270), (130, 230)], 0),
    ]
    labels = [(490, 292, "next weekly run")]
    return render_case("CRM bespoke task and pricing invoicing pipeline", 980, 320, [], cards, edges, labels,
                       "One unattended scheduled run per week reads tasks, prices them, checks them and commits to the CRM.")


def tutor_kb():
    cards = [
        ("k1", 30, 120, 200, 110, "STAGE 1", ["Protocol", "Ingestion"], "FAQs and operating protocols", False),
        ("k2", 270, 120, 200, 110, "STAGE 2", ["Structured", "FAQ KB"], "-30% queries", False),
        ("k3", 510, 120, 200, 110, "STAGE 3", ["NotebookLM", "Grounded Layer"], "-30% further queries", True),
        ("k4", 750, 120, 200, 110, "STAGE 4", ["Instant Tutor", "Self-Service"], "answers without waiting", False),
    ]
    edges = [
        ([(230, 175), (270, 175)], 0),
        ([(470, 175), (510, 175)], 1),
        ([(710, 175), (750, 175)], 2),
    ]
    zones = [(30, 260, 920, 70, "Approximate combined effect", 1)]
    labels = [(490, 312, "1 - 0.7 x 0.7 = 0.51, so about 51% fewer queries than the baseline")]
    return render_case("Tutor knowledge base and NotebookLM integration", 980, 350, zones, cards, edges, labels,
                       "Grounded retrieval over one structured knowledge base. Figures are approximate.")


def main():
    out = Path(__file__).resolve().parents[1] / "assets"
    out.mkdir(exist_ok=True)
    files = {"architecture.svg": overview, "multi-repo-orchestrator.svg": orchestrator,
             "ast-delta-gate.svg": delta_gate, "pretooluse-hooks.svg": hooks,
             "skill-router.svg": router, "secops-office.svg": secops,
             "zoom-cta-orchestrator.svg": zoom_cta, "crm-invoicing-pipeline.svg": crm_invoicing,
             "tutor-notebooklm-kb.svg": tutor_kb}
    for name, fn in files.items():
        (out / name).write_text(fn(), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
