#!/usr/bin/env python3
"""Generează 10 fișiere .m3u8 (câte unul per bloc) din muzica/ descărcată.

Format M3U8 extins — include titluri și durată pentru afișare frumoasă în Mixxx.
Playlist-urile au paths absolute așa că merg direct în Mixxx (File → Import Playlist).

Usage:
    python3 generate-playlists.py
"""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent
MUZICA = REPO / "muzica"
PLAYLISTS = REPO / "playlists"
TRACKS_FILE = REPO / "tracks.json"


def ffprobe_duration(path: Path) -> int:
    """Returns duration in seconds (int), or -1 if unknown."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True
        )
        return int(float(r.stdout.strip()))
    except Exception:
        return -1


def main():
    PLAYLISTS.mkdir(exist_ok=True)

    with open(TRACKS_FILE) as f:
        data = json.load(f)

    for block, tracks in data.items():
        block_dir = MUZICA / block
        if not block_dir.exists():
            print(f"⚠️  skip {block}: folder lipsește")
            continue

        files = sorted(block_dir.glob("*.m4a"))
        if not files:
            print(f"⚠️  skip {block}: fără fișiere m4a")
            continue

        m3u_path = PLAYLISTS / f"{block}.m3u8"
        lines = ["#EXTM3U"]
        for i, f in enumerate(files):
            # Match file index (NN-Artist-Title) with tracks.json order
            if i < len(tracks):
                artist, title = tracks[i][0], tracks[i][1]
                display = f"{artist} — {title}"
            else:
                display = f.stem
            duration = ffprobe_duration(f)
            lines.append(f"#EXTINF:{duration},{display}")
            lines.append(str(f.resolve()))

        m3u_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        total_min = sum(ffprobe_duration(f) for f in files) // 60
        print(f"✅ {block}.m3u8  ({len(files)} piese, ~{total_min}min)")

    print(f"\n📂 Playlists generate în: {PLAYLISTS}/")
    print("   În Mixxx: File → Import Playlist → selectează fiecare .m3u8")


if __name__ == "__main__":
    main()
