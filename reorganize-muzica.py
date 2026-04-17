#!/usr/bin/env python3
"""Reorganizează muzica/ conform tracks.json nou (fără re-download).

Găsește fișierele existente după artist+title și le mută în blocurile/indicii noi.
Folosește muzica_new/ ca staging, apoi înlocuiește muzica/ atomic la final.

Usage:
    python3 reorganize-muzica.py              # migrează
    python3 reorganize-muzica.py --dry-run    # doar preview
"""
import json
import re
import shutil
import sys
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional

REPO = Path(__file__).parent
MUZICA = REPO / "muzica"
STAGING = REPO / "muzica_new"
TRACKS_FILE = REPO / "tracks.json"


def safe(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return re.sub(r"_+", "_", s).strip("_")


def strip_idx(stem: str) -> str:
    """Strip 'NN-' index prefix from filename stem."""
    return re.sub(r"^\d+-", "", stem)


def score_match(needle_stem: str, file_stem: str) -> float:
    """Fuzzy match score between needle (artist-title safe) and file stem."""
    return SequenceMatcher(None, needle_stem.lower(), file_stem.lower()).ratio()


def find_best_match(artist: str, title: str, all_files: list) -> Optional[Path]:
    needle = f"{safe(artist)}-{safe(title)}"
    best = None
    best_score = 0
    for f in all_files:
        clean = strip_idx(f.stem)
        score = score_match(needle, clean)
        if score > best_score:
            best_score = score
            best = f
    # Require decent match threshold
    if best and best_score >= 0.60:
        return best
    return None


def main():
    dry = "--dry-run" in sys.argv

    if not MUZICA.exists():
        print(f"⚠️  {MUZICA} nu există — rulează download-muzica.py întâi")
        return

    with open(TRACKS_FILE) as f:
        data = json.load(f)

    all_existing = sorted(MUZICA.rglob("*.m4a"))
    print(f"Găsite {len(all_existing)} fișiere existente în {MUZICA}\n")

    if STAGING.exists() and not dry:
        shutil.rmtree(STAGING)
    if not dry:
        STAGING.mkdir()

    missing = []
    matched = 0
    used_files = set()

    for block, tracks in data.items():
        block_dir = STAGING / block
        if not dry:
            block_dir.mkdir(exist_ok=True)
        print(f"== {block} ({len(tracks)} piese) ==")

        for i, entry in enumerate(tracks, 1):
            if isinstance(entry, dict):
                artist = entry["artist"]
                title = entry["title"]
            else:
                artist, title = entry[0], entry[1]

            # Exclude already-used files
            available = [f for f in all_existing if f not in used_files]
            match = find_best_match(artist, title, available)

            if not match:
                print(f"  ✗ [{i:02d}] LIPSA: {artist} — {title}")
                missing.append(f"{block}[{i}] {artist} — {title}")
                continue

            used_files.add(match)
            matched += 1
            new_name = f"{i:02d}-{safe(artist)}-{safe(title)}.m4a"
            new_path = block_dir / new_name
            print(f"  ✓ [{i:02d}] {artist} — {title}")
            print(f"      from: {match.relative_to(MUZICA)}")
            print(f"      to:   {block}/{new_name}")

            if not dry:
                shutil.copy2(match, new_path)

    print(f"\n{'='*60}")
    print(f"Match: {matched}/{sum(len(v) for v in data.values())}")
    if missing:
        print(f"\n⚠️  {len(missing)} lipsă — vor fi descărcate dacă rulezi download-muzica.py")
        for m in missing:
            print(f"  - {m}")

    unused = [f for f in all_existing if f not in used_files]
    if unused:
        print(f"\n🗑️  {len(unused)} fișiere vechi nereusite (nu mai sunt în tracks.json):")
        for f in unused:
            print(f"  - {f.relative_to(MUZICA)}")

    if dry:
        print("\n(DRY RUN — nu s-a modificat nimic. Rulează fără --dry-run pentru a aplica.)")
        return

    # Atomic swap
    backup = REPO / "muzica_old"
    if backup.exists():
        shutil.rmtree(backup)
    MUZICA.rename(backup)
    STAGING.rename(MUZICA)
    print(f"\n✅ Done. Backup vechi în: {backup} (poți șterge manual după verificare)")


if __name__ == "__main__":
    main()
