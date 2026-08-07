#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
USERNAME = os.environ.get("GH_PROFILE_USER", PROFILE["username"])
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = ROOT / "data" / "contributions.json"


def fetch_days():
    r = requests.get(URL, headers={"User-Agent": "l192-profile-readme/1.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        raise RuntimeError("GitHub contribution cells were not found; markup may have changed.")
    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        count = None
        level = td.get("data-level")
        # Current GitHub markup exposes the count via a linked tool-tip.
        td_id = td.get("id")
        tooltip = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip.get_text(" ", strip=True) if tooltip else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.search(r"(\d[\d,]*)\s+contribution", text, re.I)
            if m:
                count = int(m.group(1).replace(",", ""))
        if count is None:
            # Fallback keeps the renderer usable even if tooltip wording changes.
            try:
                count = int(level or 0)
            except ValueError:
                count = 0
        days.append({"date": date, "count": count})
    days.sort(key=lambda x: x["date"])
    return days


def streaks(days):
    longest = cur = 0
    run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    i = len(days) - 1
    # Do not let an unfinished zero-contribution today kill a streak.
    if i >= 0 and days[i]["count"] == 0 and days[i]["date"] == dt.date.today().isoformat():
        i -= 1
    while i >= 0 and days[i]["count"] > 0:
        cur += 1
        i -= 1
    return cur, longest


def build(days):
    cur, longest = streaks(days)
    active = sum(d["count"] > 0 for d in days)
    best = max(days, key=lambda d: d["count"]) if days else {"date": None, "count": 0}
    return {
        "source": "github-public-contributions",
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_contributions": sum(d["count"] for d in days),
        "active_days": active,
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": best,
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved {len(data['days'])} days / {data['total_contributions']} contributions for {USERNAME}")
