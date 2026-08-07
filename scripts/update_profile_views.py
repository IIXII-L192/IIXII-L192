#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "profile-views.json"

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
samples = data.setdefault("samples", [])
today = datetime.now(timezone.utc).date().isoformat()

# Avoid repeatedly hitting the counter if the workflow is re-run on the same day.
if any(item.get("date") == today for item in samples):
    print(f"Profile-view sample for {today} already exists; skipping.")
    raise SystemExit(0)

counter = data.get("counter", "IIXII-L192-IIXII-L192")
url = f"https://count.getloli.com/record/@{counter}"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "IIXII-L192-profile-action/1.0",
        "Accept": "application/json",
    },
)

with urllib.request.urlopen(req, timeout=30) as response:
    payload = json.loads(response.read().decode("utf-8"))

count = int(payload["num"])
samples.append({"date": today, "count": count})
samples.sort(key=lambda x: x["date"])
data["samples"] = samples[-366:]

DATA_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Recorded a profile-view sample for {today}.")
