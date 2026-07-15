#!/usr/bin/env python3
"""Sync the self-portrait archive from Art_Studio into the site and rebuild
selfportraits/sp_manifest.js. Run after adding images to
Art_Studio/00_RAW_MATERIAL/self_portraits/<year>/, then commit + push.
"""

import json
import os
import re
import shutil

SRC = os.path.expanduser("~/Desktop/Art_Studio/00_RAW_MATERIAL/self_portraits")
SITE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(SITE, "selfportraits")


def title_from(filename):
    m = re.match(r"\d{4}-\d{2}-\d{2}_(.+)\.jpg$", filename)
    slug = m.group(1) if m else os.path.splitext(filename)[0]
    return " ".join(w.capitalize() for w in slug.split("_"))


entries, copied = [], 0
for year in sorted(os.listdir(SRC)):
    ydir = os.path.join(SRC, year)
    if not (year.isdigit() and os.path.isdir(ydir)):
        continue
    os.makedirs(os.path.join(DEST, year), exist_ok=True)
    for f in sorted(os.listdir(ydir)):
        if not f.lower().endswith(".jpg"):
            continue
        dest = os.path.join(DEST, year, f)
        if not os.path.exists(dest):
            shutil.copy2(os.path.join(ydir, f), dest)
            copied += 1
        entries.append({
            "file": f"{year}/{f}",
            "date": f[:10],
            "year": int(year),
            "title": title_from(f),
        })

entries.sort(key=lambda e: e["date"], reverse=True)  # newest first, site convention
with open(os.path.join(DEST, "sp_manifest.js"), "w") as out:
    out.write("window.SP = " + json.dumps(entries, indent=1) + ";\n")
print(f"{copied} new image(s) copied, {len(entries)} total in sp_manifest.js")
