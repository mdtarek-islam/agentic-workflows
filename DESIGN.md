# Design tokens

Source for every diagram in `assets/`. Change tokens here first, then regenerate with `python scripts/generate_svgs.py`.

## Colour

| Token | Value | Use |
|---|---|---|
| night | #0B0F19 | Canvas background |
| panel | #141A2A | Node fill |
| accent | #7C3AED | Gate and focus nodes |
| ramp-1 | #FBBF24 | First flow stage |
| ramp-2 | #F97316 | Middle flow stage |
| ramp-3 | #F43F5E | Final flow stage |
| text | #E5E7EB | Titles and labels |
| muted | #9CA3AF | Sub labels |

## Type

| Role | Size | Weight |
|---|---|---|
| Diagram title | 22px | 700 |
| Node title | 15px | 600 |
| Node sub label | 12px | 400 |

Font stack: Inter, Segoe UI, Arial, sans-serif.

## Layout and motion

1. Connectors use right angles only.
2. Node corner radius is 10px. Node stroke is 2px.
3. Flow dashes move at 1.6s per cycle.
4. `prefers-reduced-motion: reduce` stops all animation.
