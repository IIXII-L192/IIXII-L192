#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "contrib-heatmap.svg"
USERNAME = "IIXII-L192"
API = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"

req = urllib.request.Request(
    API,
    headers={
        "User-Agent": "IIXII-L192-profile-action/1.0",
        "Accept": "application/json",
    },
)

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
except Exception as exc:
    print(f"Contribution data fetch failed: {exc}")
    if OUT_FILE.exists():
        print("Keeping existing contrib-heatmap.svg")
        raise SystemExit(0)
    raise

items = data.get("contributions", [])
if not items:
    print("Contribution API returned no contribution days; keeping existing SVG.")
    raise SystemExit(0)

days = []
for item in items:
    try:
        d = date.fromisoformat(item["date"])
        level = max(0, min(4, int(item.get("level", 0))))
        count = max(0, int(item.get("count", 0)))
        days.append((d, level, count))
    except Exception:
        continue
days.sort(key=lambda x: x[0])

if not days:
    print("No valid contribution days; keeping existing SVG.")
    raise SystemExit(0)

first = days[0][0]
start_sunday = first - timedelta(days=(first.weekday() + 1) % 7)
last = days[-1][0]
weeks = ((last - start_sunday).days // 7) + 1

CELL, GAP = 12, 4
LEFT, TOP = 38, 32
BOTTOM = 30
WIDTH = LEFT + weeks * (CELL + GAP) + 8
HEIGHT = TOP + 7 * (CELL + GAP) + BOTTOM

COLORS = ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"]
LABEL = "#8B949E"

rects = []
month_labels = []
seen_months = set()

for d, level, count in days:
    delta = (d - start_sunday).days
    week = delta // 7
    row = (d.weekday() + 1) % 7
    x = LEFT + week * (CELL + GAP)
    y = TOP + row * (CELL + GAP)
    delay = (week * 0.045) + (row * 0.035)
    cls = "hot" if level else "cell"

    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
        f'fill="{COLORS[level]}" style="animation-delay:{delay:.3f}s">'
        f'<title>{d.isoformat()}: {count} contributions</title></rect>'
    )

    key = (d.year, d.month)
    if d.day <= 7 and key not in seen_months:
        seen_months.add(key)
        month_labels.append(
            f'<text x="{x}" y="17" fill="{LABEL}" font-size="12">{d.strftime("%b")}</text>'
        )

day_labels = []
for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
    y = TOP + row * (CELL + GAP) + CELL - 1
    day_labels.append(
        f'<text x="2" y="{y}" fill="{LABEL}" font-size="11">{label}</text>'
    )

total = data.get("total", {}).get("lastYear")
total_text = (
    f"{int(total):,} contributions in the last year"
    if isinstance(total, (int, float))
    else ""
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Animated GitHub contribution graph">
<style>
  text {{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; }}
  .cell,.hot {{
    opacity:0;
    transform-box:fill-box;
    transform-origin:center;
    animation:reveal .55s cubic-bezier(.2,.8,.2,1) forwards;
  }}
  .hot {{
    animation:reveal .55s cubic-bezier(.2,.8,.2,1) forwards,
              glow .9s ease-out forwards;
  }}
  @keyframes reveal {{
    0% {{ opacity:0; transform:scale(.15); }}
    65% {{ opacity:1; transform:scale(1.12); }}
    100% {{ opacity:1; transform:scale(1); }}
  }}
  @keyframes glow {{
    0%,35% {{ filter:brightness(1.9); }}
    100% {{ filter:brightness(1); }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .cell,.hot {{ animation:none; opacity:1; }}
  }}
</style>
<rect width="100%" height="100%" fill="none"/>
{''.join(month_labels)}
{''.join(day_labels)}
{''.join(rects)}
<text x="{WIDTH-8}" y="{HEIGHT-7}" text-anchor="end" fill="{LABEL}" font-size="12">{total_text}</text>
</svg>
"""

OUT_FILE.write_text(svg, encoding="utf-8")
print(f"Wrote {OUT_FILE} with {len(days)} contribution days.")
