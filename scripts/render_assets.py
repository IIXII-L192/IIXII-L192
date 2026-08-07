#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
DATA_PATH = ROOT / "data" / "contributions.json"
THEMES = ("terminal", "minimal", "experimental", "artistic")

THEME = {
    "terminal": {
        "bg": "#07110b", "panel": "#0b1710", "text": "#d9ffe4", "muted": "#78a987",
        "stroke": "#1d4b2b", "accent": "#53f57d", "accent2": "#2dd4bf",
        "palette": ["#102018", "#163522", "#1d5c31", "#258143", "#33b557", "#53f57d"],
        "font": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
    },
    "minimal": {
        "bg": "#f3f0e8", "panel": "#f8f6f0", "text": "#181816", "muted": "#726f67",
        "stroke": "#d8d3c8", "accent": "#2d6a56", "accent2": "#9b7b49",
        "palette": ["#e3dfd4", "#c8d8cf", "#9fc1af", "#6da087", "#417a64", "#244f40"],
        "font": "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    },
    "experimental": {
        "bg": "#0b0711", "panel": "#120c1c", "text": "#f5efff", "muted": "#9a8fa8",
        "stroke": "#34234a", "accent": "#b97cff", "accent2": "#63e6ff",
        "palette": ["#1b1227", "#34204d", "#5b327f", "#8347b8", "#ae65ed", "#63e6ff"],
        "font": "ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
    },
    "artistic": {
        "bg": "#111820", "panel": "#151e27", "text": "#eee9df", "muted": "#8794a0",
        "stroke": "#2a3946", "accent": "#8ba8bb", "accent2": "#d0b58f",
        "palette": ["#1c2831", "#293b47", "#405766", "#5e7584", "#7791a1", "#a5bdca"],
        "font": "Georgia, Times New Roman, serif",
    },
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def demo_data():
    # Deterministic visual seed only. GitHub Actions replaces this with live data.
    end = dt.date.today()
    start = end - dt.timedelta(days=370)
    days = []
    total = 0
    d = start
    while d <= end:
        h = int(hashlib.sha256((PROFILE["username"] + d.isoformat()).encode()).hexdigest()[:8], 16)
        # Sparse but lively, with occasional heavier bursts.
        if h % 100 < 42:
            count = 0
        else:
            count = 1 + (h % 18)
            if h % 29 == 0:
                count += 25
            if h % 83 == 0:
                count += 70
        days.append({"date": d.isoformat(), "count": count})
        total += count
        d += dt.timedelta(days=1)
    return {
        "source": "preview-seed",
        "username": PROFILE["username"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_contributions": total,
        "active_days": sum(x["count"] > 0 for x in days),
        "current_streak": 0,
        "longest_streak": 0,
        "best_day": max(days, key=lambda x: x["count"]),
        "days": days,
    }


def load_data():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    data = demo_data()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def level(count):
    if count <= 0: return 0
    if count <= 3: return 1
    if count <= 8: return 2
    if count <= 16: return 3
    if count <= 30: return 4
    return 5


def calendar(days):
    by_date = {dt.date.fromisoformat(x["date"]): x["count"] for x in days}
    first = min(by_date)
    last = max(by_date)
    first_sun = first - dt.timedelta(days=(first.weekday()+1)%7)
    last_sat = last + dt.timedelta(days=(5-last.weekday())%7)
    weeks = []
    cur = first_sun
    while cur <= last_sat:
        col=[]
        for _ in range(7):
            col.append((cur, by_date.get(cur)))
            cur += dt.timedelta(days=1)
        weeks.append(col)
    return weeks


def cell_anim(theme, ci, ri):
    if theme == "terminal":
        delay = ci*.018 + ri*.045
        return f"animation-delay:{delay:.3f}s"
    if theme == "minimal":
        delay = ci*.012 + ri*.022
        return f"animation-delay:{delay:.3f}s"
    if theme == "experimental":
        delay = (ci+ri)*.022 + abs(3-ri)*.018
        return f"animation-delay:{delay:.3f}s"
    delay = ci*.020 + ri*.035
    return f"animation-delay:{delay:.3f}s"


def render_heatmap(theme, data):
    c = THEME[theme]
    weeks = calendar(data["days"])
    cell=10; gap=3; step=cell+gap
    left=50; top=61; cols=len(weeks)
    width=860; grid_w=cols*step; x0=(width-grid_w)/2
    height=210
    css = {
        "terminal": "@keyframes pop{0%{opacity:0;transform:translateY(-8px)}100%{opacity:1;transform:translateY(0)}}.day{opacity:0;animation:pop .42s cubic-bezier(.2,.8,.2,1) both}",
        "minimal": "@keyframes pop{0%{opacity:0;transform:scale(.35)}100%{opacity:1;transform:scale(1)}}.day{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .36s cubic-bezier(.2,.75,.2,1) both}",
        "experimental": "@keyframes pop{0%{opacity:0;transform:scale(.1) rotate(-90deg)}70%{opacity:1;transform:scale(1.12) rotate(5deg)}100%{opacity:1;transform:scale(1) rotate(0)}}.day{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .58s cubic-bezier(.16,1,.3,1) both}@keyframes scan{0%{transform:translateX(-180px);opacity:0}15%{opacity:.65}100%{transform:translateX(960px);opacity:0}}.scan{animation:scan 3.2s ease-out 1 both}",
        "artistic": "@keyframes pop{0%{opacity:0;transform:translateY(11px)}100%{opacity:1;transform:translateY(0)}}.day{opacity:0;animation:pop .65s cubic-bezier(.16,1,.3,1) both}",
    }[theme]
    p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{c["font"]}">',f'<style>{css}</style>']
    rx = 14 if theme != "minimal" else 0
    p.append(f'<rect width="860" height="210" rx="{rx}" fill="{c["bg"]}"/>')
    if theme == "terminal":
        p += [f'<circle cx="24" cy="22" r="4" fill="{c["accent"]}" opacity=".8"/>',f'<text x="38" y="27" fill="{c["muted"]}" font-size="12">l192@github ~ $ ./contributions.sh</text>',f'<line x1="18" y1="42" x2="842" y2="42" stroke="{c["stroke"]}"/>']
    elif theme == "minimal":
        p += [f'<text x="24" y="29" fill="{c["text"]}" font-size="13" letter-spacing="1.5">ACTIVITY / LAST 53 WEEKS</text>',f'<text x="836" y="29" fill="{c["muted"]}" text-anchor="end" font-size="11">{esc(PROFILE["alias"])}</text>',f'<line x1="24" y1="42" x2="836" y2="42" stroke="{c["stroke"]}"/>']
    elif theme == "experimental":
        p += [f'<text x="22" y="29" fill="{c["accent"]}" font-size="12" letter-spacing="4">ACTIVITY SIGNAL</text>',f'<text x="838" y="29" fill="{c["accent2"]}" text-anchor="end" font-size="12">53W / LIVE</text>',f'<path d="M22 43 H838" stroke="{c["stroke"]}"/>']
    else:
        p += [f'<text x="24" y="28" fill="{c["text"]}" font-size="14" font-style="italic">a year, leaving small marks</text>',f'<text x="836" y="28" fill="{c["muted"]}" text-anchor="end" font-family="ui-monospace,monospace" font-size="10">CONTRIBUTIONS</text>',f'<line x1="24" y1="42" x2="836" y2="42" stroke="{c["stroke"]}" stroke-opacity=".8"/>']

    # month labels
    seen=set()
    for ci,col in enumerate(weeks):
        for date,count in col:
            if count is None: continue
            key=(date.year,date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                p.append(f'<text x="{x0+ci*step:.1f}" y="55" fill="{c["muted"]}" font-size="9">{date.strftime("%b")}</text>')
                break
    for ci,col in enumerate(weeks):
        for ri,(date,count) in enumerate(col):
            if count is None: continue
            x=x0+ci*step; y=top+ri*step
            fill=c["palette"][level(count)]
            if theme == "artistic":
                # Soft pebble-like cells, still a faithful 7x53 calendar.
                r = 2.6 if count == 0 else 4.5
                p.append(f'<circle class="day" style="{cell_anim(theme,ci,ri)}" cx="{x+5:.1f}" cy="{y+5:.1f}" r="{r}" fill="{fill}"/>')
            else:
                cr = 1.8 if theme != "minimal" else 1
                p.append(f'<rect class="day" style="{cell_anim(theme,ci,ri)}" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="{cr}" fill="{fill}"/>')
    if theme == "experimental":
        p.append(f'<rect class="scan" x="0" y="47" width="90" height="118" fill="{c["accent2"]}" opacity=".12"/>')

    source = data.get("source", "")
    if source == "preview-seed":
        footer = "preview seed · GitHub Action replaces this with live data"
    else:
        footer = f"{data.get('total_contributions',0):,} contributions · {data.get('active_days',0)} active days"
    if theme == "terminal":
        p.append(f'<text x="22" y="193" fill="{c["muted"]}" font-size="10">[ok] {esc(footer)}</text>')
    elif theme == "minimal":
        p.append(f'<text x="24" y="193" fill="{c["muted"]}" font-size="10">{esc(footer)}</text>')
    elif theme == "experimental":
        p.append(f'<text x="22" y="193" fill="{c["muted"]}" font-size="10" letter-spacing="1.2">{esc(footer.upper())}</text>')
    else:
        p.append(f'<text x="24" y="193" fill="{c["muted"]}" font-family="ui-monospace,monospace" font-size="9">{esc(footer)}</text>')
    p.append('</svg>')
    return ''.join(p)


def tspans(text, x, y, width_chars, line_h, **attrs):
    words=text.split(); lines=[]; cur=[]; n=0
    for w in words:
        if n + len(w) + (1 if cur else 0) > width_chars:
            lines.append(' '.join(cur)); cur=[w]; n=len(w)
        else:
            cur.append(w); n += len(w)+(1 if len(cur)>1 else 0)
    if cur: lines.append(' '.join(cur))
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items())
    return ''.join(f'<text x="{x}" y="{y+i*line_h}" {a}>{esc(line)}</text>' for i,line in enumerate(lines))


def render_profile(theme):
    c=THEME[theme]; W=860; H=390
    if theme == "terminal":
        css="@keyframes row{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}.r{opacity:0;animation:row .42s ease-out both}@keyframes caret{50%{opacity:0}}.caret{animation:caret .9s steps(1) infinite}"
        p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{c["font"]}"><style>{css}</style>',f'<rect width="{W}" height="{H}" rx="14" fill="{c["bg"]}"/>',f'<rect x=".5" y=".5" width="859" height="389" rx="14" fill="none" stroke="{c["stroke"]}"/>']
        p += [f'<circle cx="24" cy="22" r="4" fill="#ff5f56"/><circle cx="40" cy="22" r="4" fill="#ffbd2e"/><circle cx="56" cy="22" r="4" fill="#27c93f"/>',f'<text x="430" y="27" text-anchor="middle" fill="{c["muted"]}" font-size="11">l192@iixii: ~/identity</text>',f'<line x1="0" y1="42" x2="860" y2="42" stroke="{c["stroke"]}"/>']
        rows=[
            ("$ whoami", c["accent"], 60, 0),
            (PROFILE["name"]+"  /  "+PROFILE["alias"], c["text"], 90, .15),
            ("studio     "+PROFILE["studio"], c["muted"], 128, .30),
            ("location   "+PROFILE["location"], c["muted"], 154, .42),
            ("featured   "+PROFILE["featured_project"]["repo"], c["accent2"], 180, .54),
            ("portfolio  anshu192.vercel.app", c["muted"], 206, .66),
            ("photo      apertureatlas192.vercel.app", c["muted"], 232, .78),
            ("contact    unio192.vercel.app/dev", c["muted"], 258, .90),
        ]
        for text,col,y,delay in rows:
            p.append(f'<text class="r" style="animation-delay:{delay}s" x="28" y="{y}" fill="{col}" font-size="{14 if y==90 else 12}">{esc(text)}</text>')
        p.append(tspans(PROFILE["about"], 470, 91, 46, 22, fill=c["text"], **{"font-size":"14"}))
        p.append(f'<line x1="470" y1="151" x2="824" y2="151" stroke="{c["stroke"]}"/>')
        p.append(tspans('“'+PROFILE["quote"]+'”', 470, 184, 42, 25, fill=c["accent"], **{"font-size":"16","font-style":"italic"}))
        p.append(f'<text x="28" y="354" fill="{c["accent"]}" font-size="12">$ <tspan class="caret">_</tspan></text></svg>')
        return ''.join(p)

    if theme == "minimal":
        css="@keyframes in{0%{opacity:0;transform:translateY(7px)}100%{opacity:1;transform:translateY(0)}}.in{opacity:0;animation:in .55s ease-out both}"
        p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{c["font"]}"><style>{css}</style>',f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>',f'<line x1="24" y1="36" x2="836" y2="36" stroke="{c["stroke"]}"/>']
        p += [f'<text x="24" y="25" fill="{c["muted"]}" font-size="10" letter-spacing="1.8">PERSON / 01</text>',f'<text class="in" style="animation-delay:.08s" x="24" y="95" fill="{c["text"]}" font-family="Georgia,Times New Roman,serif" font-size="42">{esc(PROFILE["name"])}</text>',f'<text class="in" style="animation-delay:.18s" x="26" y="120" fill="{c["accent"]}" font-size="12" letter-spacing="2">{esc(PROFILE["alias"])} · {esc(PROFILE["studio"])} · {esc(PROFILE["location"])}</text>']
        p.append(tspans(PROFILE["about"], 24, 164, 55, 24, fill=c["text"], **{"font-size":"16"}))
        p.append(f'<line x1="24" y1="236" x2="836" y2="236" stroke="{c["stroke"]}"/>')
        infos=[("FEATURED",PROFILE["featured_project"]["repo"]),("PORTFOLIO","anshu192.vercel.app"),("PHOTOGRAPHY","apertureatlas192.vercel.app"),("CONTACT","unio192.vercel.app/dev")]
        for i,(k,v) in enumerate(infos):
            x=24+(i%2)*408; y=266+(i//2)*48
            p.append(f'<text x="{x}" y="{y}" fill="{c["muted"]}" font-size="9" letter-spacing="1.3">{k}</text><text x="{x}" y="{y+18}" fill="{c["text"]}" font-size="12">{esc(v)}</text>')
        p.append(f'<text x="836" y="364" text-anchor="end" fill="{c["accent2"]}" font-family="Georgia,Times New Roman,serif" font-size="13" font-style="italic">{esc(PROFILE["quote"])}</text></svg>')
        return ''.join(p)

    if theme == "experimental":
        css="@keyframes slash{0%{transform:translateX(-250px)}100%{transform:translateX(0)}}@keyframes reveal{0%{opacity:0;transform:translateY(18px)}100%{opacity:1;transform:translateY(0)}}.rev{opacity:0;animation:reveal .65s cubic-bezier(.16,1,.3,1) both}.slash{animation:slash .8s cubic-bezier(.16,1,.3,1) both}"
        p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{c["font"]}"><style>{css}</style>',f'<rect width="{W}" height="{H}" rx="18" fill="{c["bg"]}"/>',f'<path class="slash" d="M-40 0 L250 0 L90 390 L-200 390 Z" fill="{c["accent"]}" opacity=".16"/>',f'<path d="M500 0 H860 V160 L590 390 H380 Z" fill="{c["accent2"]}" opacity=".045"/>']
        p += [f'<text x="26" y="36" fill="{c["accent2"]}" font-size="10" letter-spacing="4">IDENTITY // SIGNAL 192</text>',f'<text class="rev" style="animation-delay:.06s" x="24" y="115" fill="{c["text"]}" font-size="51" font-weight="700">{esc(PROFILE["name"])}</text>',f'<text class="rev" style="animation-delay:.15s" x="27" y="145" fill="{c["accent"]}" font-size="15" letter-spacing="5">{esc(PROFILE["alias"])} / {esc(PROFILE["studio"])}</text>']
        p.append(tspans(PROFILE["about"], 28, 194, 52, 24, fill=c["text"], **{"font-size":"15"}))
        p.append(f'<rect x="28" y="265" width="804" height="1" fill="{c["stroke"]}"/>')
        items=[("01","DELHI, INDIA"),("02",PROFILE["featured_project"]["repo"]),("03","ANSHU192.VERCEL.APP"),("04","APERTUREATLAS192.VERCEL.APP"),("05","UNIO192.VERCEL.APP/DEV")]
        for i,(n,t) in enumerate(items):
            x=28+(i%3)*270; y=292+(i//3)*43
            p.append(f'<text x="{x}" y="{y}" fill="{c["accent"]}" font-size="9">{n}</text><text x="{x+28}" y="{y}" fill="{c["muted"]}" font-size="9" letter-spacing=".7">{esc(t)}</text>')
        p.append(f'<text x="832" y="366" text-anchor="end" fill="{c["text"]}" font-size="12" font-style="italic">{esc(PROFILE["quote"])}</text></svg>')
        return ''.join(p)

    # artistic
    css="@keyframes breathe{0%{opacity:0;transform:translateY(8px)}100%{opacity:1;transform:translateY(0)}}.b{opacity:0;animation:breathe .9s ease-out both}@keyframes drift{0%{opacity:.15;transform:translateX(-12px)}100%{opacity:.5;transform:translateX(12px)}}.drift{animation:drift 6s ease-in-out infinite alternate}"
    p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{c["font"]}"><style>{css}</style>',f'<rect width="{W}" height="{H}" rx="18" fill="{c["bg"]}"/>',f'<circle class="drift" cx="725" cy="68" r="150" fill="none" stroke="{c["accent"]}" stroke-opacity=".18"/><circle class="drift" cx="742" cy="74" r="112" fill="none" stroke="{c["accent2"]}" stroke-opacity=".14"/>']
    p.append(f'<text class="b" style="animation-delay:.05s" x="38" y="72" fill="{c["muted"]}" font-family="ui-monospace,monospace" font-size="10" letter-spacing="2">{esc(PROFILE["alias"])} / {esc(PROFILE["studio"])}</text>')
    p.append(tspans('“'+PROFILE["quote"]+'”', 38, 126, 48, 32, fill=c["text"], **{"font-size":"24","font-style":"italic"}))
    p.append(f'<line x1="38" y1="218" x2="822" y2="218" stroke="{c["stroke"]}"/>')
    p.append(f'<text class="b" style="animation-delay:.32s" x="38" y="258" fill="{c["text"]}" font-size="19">{esc(PROFILE["name"])}</text>')
    p.append(tspans(PROFILE["about"], 38, 288, 72, 20, fill=c["muted"], **{"font-family":"ui-sans-serif,system-ui,sans-serif","font-size":"12"}))
    p.append(f'<text x="822" y="258" text-anchor="end" fill="{c["accent2"]}" font-family="ui-monospace,monospace" font-size="10">{esc(PROFILE["location"])}</text>')
    p.append(f'<text x="822" y="286" text-anchor="end" fill="{c["accent"]}" font-family="ui-monospace,monospace" font-size="10">{esc(PROFILE["featured_project"]["repo"])}</text>')
    p.append(f'<text x="822" y="315" text-anchor="end" fill="{c["muted"]}" font-family="ui-monospace,monospace" font-size="9">anshu192.vercel.app · apertureatlas192.vercel.app</text>')
    p.append(f'<text x="822" y="341" text-anchor="end" fill="{c["muted"]}" font-family="ui-monospace,monospace" font-size="9">unio192.vercel.app/dev</text></svg>')
    return ''.join(p)


def readme(theme):
    headings={
        "terminal": ("`l192@github ~ $ ./activity`","`l192@github ~ $ whoami`"),
        "minimal": ("Activity","Aakarsh Singhal"),
        "experimental": ("ACTIVITY // SIGNAL","IDENTITY // L192"),
        "artistic": ("small marks, over time","somewhere between utility and atmosphere"),
    }
    h1,h2=headings[theme]
    return f'''<div align="center">\n\n### {h1}\n\n<img src="./assets/{theme}/contributions.svg" width="860" alt="Animated GitHub contribution calendar" />\n\n<br>\n\n### {h2}\n\n<img src="./assets/{theme}/profile.svg" width="860" alt="Profile of Aakarsh Singhal, L192" />\n\n<br>\n\n[Portfolio](https://anshu192.vercel.app) · [IIXII Store](https://iixiistore.vercel.app) · [Photography](https://apertureatlas192.vercel.app) · [Contact](https://unio192.vercel.app/dev)\n\n</div>\n'''


def main():
    data=load_data()
    for theme in THEMES:
        out=ROOT/"assets"/theme; out.mkdir(parents=True,exist_ok=True)
        (out/"contributions.svg").write_text(render_heatmap(theme,data),encoding="utf-8")
        (out/"profile.svg").write_text(render_profile(theme),encoding="utf-8")
        (ROOT/"variants"/f"README.{theme}.md").write_text(readme(theme),encoding="utf-8")
    print("Rendered:", ", ".join(THEMES))

if __name__ == "__main__":
    main()
