#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "profile-views.json"
OUT_FILE = ROOT / "profile-views.svg"

W, H = 860, 300
LEFT, RIGHT, TOP, BOTTOM = 44, 24, 52, 42
PW = W - LEFT - RIGHT
PH = H - TOP - BOTTOM

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
samples = data.get("samples", [])[-30:]

if not samples:
    samples = [{"date": datetime.utcnow().date().isoformat(), "count": 0}]

dates = [item["date"] for item in samples]
values = [int(item["count"]) for item in samples]

vmin = min(values)
vmax = max(values)
span = max(1, vmax - vmin)
pad = max(1.0, span * 0.15)
lo = vmin - pad
hi = vmax + pad

def x_for(i: int) -> float:
    if len(values) == 1:
        return LEFT + PW / 2
    return LEFT + PW * i / (len(values) - 1)

def y_for(v: int) -> float:
    return TOP + PH * (1 - (v - lo) / (hi - lo))

points = [(x_for(i), y_for(v)) for i, v in enumerate(values)]

def smooth_path(pts):
    if len(pts) == 1:
        x, y = pts[0]
        return f"M {x:.2f},{y:.2f}"
    d = f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d += (
            f" C {c1x:.2f},{c1y:.2f}"
            f" {c2x:.2f},{c2y:.2f}"
            f" {p2[0]:.2f},{p2[1]:.2f}"
        )
    return d

line_path = smooth_path(points)

if len(points) > 1:
    area_path = (
        line_path
        + f" L {points[-1][0]:.2f},{TOP+PH:.2f}"
        + f" L {points[0][0]:.2f},{TOP+PH:.2f} Z"
    )
else:
    area_path = ""

grid = []
for frac in (0, .25, .5, .75, 1):
    y = TOP + PH * frac
    grid.append(
        f'<line x1="{LEFT}" y1="{y:.2f}" x2="{W-RIGHT}" y2="{y:.2f}" '
        f'stroke="#172231" stroke-width="1" stroke-dasharray="4 7"/>'
    )

if len(samples) == 1:
    label_indices = [0]
else:
    wanted = min(5, len(samples))
    label_indices = sorted(set(round(i * (len(samples)-1) / (wanted-1)) for i in range(wanted)))

date_labels = []
for idx in label_indices:
    dt = datetime.fromisoformat(dates[idx])
    date_labels.append(
        f'<text x="{x_for(idx):.2f}" y="{H-16}" text-anchor="middle" '
        f'fill="#7f95ad" font-size="12">{dt.strftime("%d %b")}</text>'
    )

if len(points) > 1:
    graph_markup = f"""
  <path d="{area_path}" fill="url(#area)"/>
  <path d="{line_path}" fill="none" stroke="#6FD3FF" stroke-width="4"
        stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
  <circle cx="{points[-1][0]:.2f}" cy="{points[-1][1]:.2f}" r="5"
          fill="#071019" stroke="#A8E7FF" stroke-width="2"/>
"""
else:
    x, y = points[0]
    graph_markup = f"""
  <circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="#071019"
          stroke="#78D8FF" stroke-width="3" filter="url(#glow)"/>
  <circle cx="{x:.2f}" cy="{y:.2f}" r="13" fill="none"
          stroke="#78D8FF" stroke-opacity=".22" stroke-width="2"/>
  <text x="{x:.2f}" y="{y-22:.2f}" text-anchor="middle"
        fill="#86A4BE" font-size="12">collecting daily history</text>
"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
viewBox="0 0 {W} {H}" role="img" aria-label="GitHub profile views statistics">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0B0F15"/>
    <stop offset="1" stop-color="#05080D"/>
  </linearGradient>
  <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#62CCFF" stop-opacity=".42"/>
    <stop offset="1" stop-color="#62CCFF" stop-opacity=".02"/>
  </linearGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="3.2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="17.5"
      fill="none" stroke="#1B2837"/>
<text x="{LEFT}" y="31" fill="#EDF7FF" font-family="Arial,Helvetica,sans-serif"
      font-size="18" font-weight="700">GitHub profile views statistics</text>
<text x="{W-RIGHT}" y="31" text-anchor="end" fill="#627D97"
      font-family="Arial,Helvetica,sans-serif" font-size="12">last 30 days</text>
{''.join(grid)}
{graph_markup}
{''.join(date_labels)}
</svg>
"""

OUT_FILE.write_text(svg, encoding="utf-8")
print(f"Wrote {OUT_FILE}")
