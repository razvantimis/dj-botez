#!/usr/bin/env python3
"""Descarcă toate piesele din tracks.json în muzica/<block>/ folosind yt-dlp.

Usage:
    python3 download-muzica.py                # descarcă toate
    python3 download-muzica.py A-Aperitiv-Lounge  # un singur bloc
    python3 download-muzica.py --dry-run      # doar listează ce ar descărca
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
MUZICA = REPO / "muzica"
TRACKS_FILE = REPO / "tracks.json"


def safe(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return re.sub(r"_+", "_", s).strip("_")


def already_downloaded(outdir: Path, stem: str) -> bool:
    return any(outdir.glob(f"{stem}.*"))


def download(block: str, idx: int, entry, dry: bool) -> bool:
    # Suport pentru ambele formate: dict (nou, cu genre) și list (legacy)
    if isinstance(entry, dict):
        artist = entry["artist"]
        title = entry["title"]
        explicit_url = entry.get("url")
    else:
        artist = entry[0]
        title = entry[1]
        explicit_url = entry[2] if len(entry) >= 3 else None

    outdir = MUZICA / block
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"{idx:02d}-{safe(artist)}-{safe(title)}"

    if already_downloaded(outdir, stem):
        print(f"  ⏭  [{idx:02d}] skip (already have): {artist} — {title}")
        return True

    source = explicit_url if explicit_url else f"ytsearch1:{artist} {title}"
    print(f"  ⬇  [{idx:02d}] {artist} — {title}")
    if dry:
        print(f"      source: {source}")
        return True

    cmd = [
        "yt-dlp",
        "--format", "bestaudio[ext=m4a]/bestaudio",
        "--extract-audio",
        "--audio-format", "m4a",
        "--audio-quality", "0",
        "--embed-thumbnail",
        "--add-metadata",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "--progress",
        "-o", str(outdir / f"{stem}.%(ext)s"),
        source,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"      ❌ FAIL: {result.stderr.strip().splitlines()[-1] if result.stderr else 'unknown'}")
        return False
    return True


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    only_block = args[0] if args else None

    with open(TRACKS_FILE) as f:
        data = json.load(f)

    total = 0
    ok = 0
    for block, tracks in data.items():
        if only_block and block != only_block:
            continue
        print(f"\n=== {block} ({len(tracks)} piese) ===")
        for i, entry in enumerate(tracks, 1):
            total += 1
            if download(block, i, entry, dry):
                ok += 1

    print(f"\n✅ {ok}/{total} piese gata" + (" (dry-run)" if dry else ""))


if __name__ == "__main__":
    main()
