#!/usr/bin/env python3
"""Sync the portfolio folder into the site.

Usage:  python3 update_site.py

Looks in the Portfolio_images folder for any file not yet on the site,
converts it to a web-ready JPEG (max 2000px, quality 80), and adds a
manifest entry. Existing manifest entries are never touched, so edits
you make by hand (titles, process tags) are safe. Videos (.mp4) are
NOT copied — upload them to YouTube (unlisted) and add a manifest
entry with a "youtube": "<video-id>" field instead.
"""
import os, re, json, subprocess, sys

SRC = "/Users/mikehibyeok/Desktop/Clients/Art Submissions/Portfolio/Portfolio_images"
SITE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(SITE, "images")
MANIFEST = os.path.join(SITE, "manifest.json")

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".heic", ".webp", ".tiff")

series_map = [
    (r"ai-slop|aislop|joejim", "AI Slop"),
    (r"bio-diverse", "Bio Diverse"),
    (r"comic", "Comics"),
    (r"eaas", "EAAS"),
    (r"frootloop|frootpower", "Frootloop"),
    (r"hair", "Hair"),
    (r"impasto", "Impasto"),
    (r"lacma", "LACMA"),
    (r"msu", "MSU"),
]
capfix = {"ai": "AI", "eaas": "EAAS", "lacma": "LACMA", "msu": "MSU", "iphone": "iPhone"}


def web_name(filename):
    """IMG name -> lowercase, extensions stripped, .jpg or .mp4."""
    name = filename.lower()
    if name.endswith(".mp4"):
        return name
    for _ in range(3):  # handles double extensions like .jpeg.jpg
        name = re.sub(r"\.(jpg|jpeg|png|heic|webp|tiff)$", "", name)
    return name + ".jpg"


def make_entry(webfile):
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.(jpg|mp4)$", webfile)
    if not m:
        return None
    date, slug, ext = m.groups()
    words = re.sub(r"(\d+)$", r" \1", slug).replace("-", " ").split()
    title = " ".join(capfix.get(w, w.capitalize()) for w in words)
    series = next((s for pat, s in series_map if re.search(pat, slug)), "Misc")
    return {
        "file": "images/" + webfile,
        "type": "video" if ext == "mp4" else "image",
        "title": title,
        "date": date,
        "series": series,
        "process": "ai",
    }


def main():
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else []
    known = {w["file"].split("/")[-1] for w in manifest}
    os.makedirs(IMAGES, exist_ok=True)

    added, skipped, videos_found = [], [], []
    for f in sorted(os.listdir(SRC)):
        src = os.path.join(SRC, f)
        if f.startswith(".") or not os.path.isfile(src):
            continue
        if f.lower().endswith(".mp4"):
            videos_found.append(f)
            continue
        if not f.lower().endswith(IMAGE_EXTS):
            continue
        wf = web_name(f)
        if wf in known:
            continue
        if not re.match(r"\d{4}-\d{2}-\d{2}-", wf):
            skipped.append(f)
            continue
        out = os.path.join(IMAGES, wf)
        w = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", src],
                           capture_output=True, text=True).stdout
        dims = [int(n) for n in re.findall(r"pixel\w+: (\d+)", w)]
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80"]
        if dims and max(dims) > 2000:
            cmd += ["--resampleHeightWidthMax", "2000"]
        subprocess.run(cmd + [src, "--out", out], check=True,
                       capture_output=True)
        entry = make_entry(wf)
        manifest.append(entry)
        known.add(wf)
        added.append(wf)

    manifest.sort(key=lambda w: w["date"], reverse=True)
    json.dump(manifest, open(MANIFEST, "w"), indent=2)
    with open(os.path.join(SITE, "manifest.js"), "w") as f:
        f.write("window.WORKS = " + json.dumps(manifest, indent=2) + ";\n")

    print(f"{len(added)} new work(s) added, {len(manifest)} total on site.")
    for a in added:
        print("  +", a)
    for s in skipped:
        print(f"  ! skipped (name must start with YYYY-MM-DD-): {s}")
    for v in videos_found:
        print(f"  ! video not copied — upload to YouTube and add a manifest entry: {v}")


if __name__ == "__main__":
    main()
