#!/usr/bin/env python3
"""Suprascrie tag-urile genre/artist/title pe fisierele m4a din muzica/
conform tracks.json.

Foloseste ffmpeg -c copy (rapid, fara re-encode).

Usage:
    python3 tag-muzica.py             # toate blocurile
    python3 tag-muzica.py E1-Latino   # un singur bloc
    python3 tag-muzica.py --dry-run   # preview
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
MUZICA = REPO / "muzica"
TRACKS_FILE = REPO / "tracks.json"


def update_tags(file_path: Path, artist: str, title: str, genre: str) -> bool:
    tmp = file_path.with_suffix(".tmp.m4a")
    cmd = [
        "ffmpeg",
        "-y", "-loglevel", "error",
        "-i", str(file_path),
        "-c", "copy",
        "-metadata", f"artist={artist}",
        "-metadata", f"title={title}",
        "-metadata", f"genre={genre}",
        "-metadata", f"album_artist={artist}",
        str(tmp),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        print(f"      ❌ {result.stderr.strip().splitlines()[-1] if result.stderr else 'fail'}")
        return False
    tmp.replace(file_path)
    return True


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    only_block = args[0] if args else None

    if not MUZICA.exists():
        print(f"⚠️  {MUZICA} nu există")
        return

    with open(TRACKS_FILE) as f:
        data = json.load(f)

    total = 0
    ok = 0

    for block, tracks in data.items():
        if only_block and block != only_block:
            continue
        block_dir = MUZICA / block
        if not block_dir.exists():
            print(f"⚠️  skip {block}: folder lipsește")
            continue
        files = sorted(block_dir.glob("*.m4a"))
        print(f"\n== {block} ({len(files)} fișiere) ==")

        for i, entry in enumerate(tracks):
            if i >= len(files):
                break
            if isinstance(entry, dict):
                artist = entry["artist"]
                title = entry["title"]
                genre = entry.get("genre", "")
            else:
                artist, title = entry[0], entry[1]
                genre = ""

            total += 1
            f = files[i]
            print(f"  [{i+1:02d}] {artist} — {title}")
            print(f"       genre: [{genre}]")
            if dry:
                ok += 1
                continue
            if update_tags(f, artist, title, genre):
                ok += 1

    print(f"\n{'='*60}")
    print(f"✅ {ok}/{total} taguri actualizate" + (" (dry-run)" if dry else ""))
    if not dry:
        print("\nÎn Mixxx: Settings → Library → Rescan Library (sau File → Reload metadata)")


if __name__ == "__main__":
    main()
