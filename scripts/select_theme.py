#!/usr/bin/env python3
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
valid={"terminal","minimal","experimental","artistic"}
if len(sys.argv)!=2 or sys.argv[1] not in valid:
    raise SystemExit("Usage: python scripts/select_theme.py terminal|minimal|experimental|artistic")
theme=sys.argv[1]
shutil.copyfile(ROOT/"variants"/f"README.{theme}.md", ROOT/"README.md")
print(f"Selected {theme}. README.md now uses assets/{theme}/")
