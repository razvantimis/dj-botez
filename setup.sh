#!/usr/bin/env bash
# Setup complet pentru Botez Amalia DJ kit.
# Auto-detectează ce-i instalat, aduce doar ce lipsește, descarcă piese, generează playlist-uri Mixxx.
#
# Usage: ./setup.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
step() { echo -e "\n${BOLD}▶ $*${RESET}"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
fail() { echo -e "${RED}✗${RESET} $*"; exit 1; }

# ------------------------------------------------------------------------------
# 1. Platform check
# ------------------------------------------------------------------------------
step "Verificare platformă"
OS="$(uname -s)"
case "$OS" in
  Darwin) ok "macOS detectat" ;;
  Linux)  ok "Linux detectat" ;;
  *)      fail "OS nesuportat: $OS (doar macOS și Linux)" ;;
esac

command -v python3 >/dev/null 2>&1 || fail "python3 lipsește"
ok "python3 $(python3 --version | cut -d' ' -f2)"

# ------------------------------------------------------------------------------
# 2. Install only what's missing
# ------------------------------------------------------------------------------

install_mac() {
  command -v brew >/dev/null 2>&1 || fail "Homebrew lipsește. Instalează de la https://brew.sh"
  local formula="$1"
  echo "  ⬇  installing $formula..."
  brew install "$formula"
}

install_mac_cask() {
  command -v brew >/dev/null 2>&1 || fail "Homebrew lipsește. Instalează de la https://brew.sh"
  local cask="$1"
  echo "  ⬇  installing $cask (cask, durează ~1min)..."
  brew install --cask "$cask"
}

install_linux() {
  command -v apt-get >/dev/null 2>&1 || fail "apt-get lipsește (Linux non-Debian — instalează manual $*)"
  sudo apt-get install -y "$@"
}

# --- yt-dlp
step "yt-dlp"
if command -v yt-dlp >/dev/null 2>&1; then
  ok "yt-dlp $(yt-dlp --version)"
else
  [ "$OS" = "Darwin" ] && install_mac yt-dlp || install_linux yt-dlp
fi

# --- ffmpeg
step "ffmpeg"
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)"
else
  [ "$OS" = "Darwin" ] && install_mac ffmpeg || install_linux ffmpeg
fi

# --- DJ player (Mixxx sau alternativă)
step "DJ player"
DJ_APPS=(
  "/Applications/Mixxx.app"
  "/Applications/rekordbox.app"
  "/Applications/rekordbox 6.app"
  "/Applications/Serato DJ Pro.app"
  "/Applications/djay Pro AI.app"
  "/Applications/Traktor Pro 3.app"
  "/Applications/VirtualDJ.app"
)
DJ_FOUND=""
if [ "$OS" = "Darwin" ]; then
  for app in "${DJ_APPS[@]}"; do
    [ -d "$app" ] && DJ_FOUND="$(basename "$app" .app)" && break
  done
fi

if [ -n "$DJ_FOUND" ]; then
  ok "DJ software deja instalat: $DJ_FOUND"
elif [ "$OS" = "Darwin" ]; then
  install_mac_cask mixxx
elif [ "$OS" = "Linux" ]; then
  command -v mixxx >/dev/null 2>&1 || install_linux mixxx
  ok "Mixxx gata"
fi

# ------------------------------------------------------------------------------
# 3. Download piese (doar dacă lipsesc)
# ------------------------------------------------------------------------------
step "Descărcare piese (yt-dlp)"
EXPECTED=$(python3 -c "import json; d=json.load(open('tracks.json')); print(sum(len(v) for v in d.values()))")
ACTUAL=$(find muzica -name '*.m4a' 2>/dev/null | wc -l | tr -d ' ')
if [ "$ACTUAL" = "$EXPECTED" ]; then
  ok "muzica/ complet ($ACTUAL/$EXPECTED piese) — skip"
else
  echo "  $ACTUAL/$EXPECTED piese prezente, descarcă restul..."
  python3 download-muzica.py
fi

# ------------------------------------------------------------------------------
# 4. Generate playlists
# ------------------------------------------------------------------------------
step "Generare playlist-uri (.m3u8)"
python3 generate-playlists.py

# ------------------------------------------------------------------------------
# 5. Done
# ------------------------------------------------------------------------------
step "Setup complet!"
echo
echo -e "${BOLD}Ce ai acum:${RESET}"
echo "  • muzica/           — 115 piese m4a în 10 blocuri"
echo "  • playlists/        — 10 fișiere .m3u8"
echo "  • plan-botez-amalia.md — planul DJ complet"
echo
echo -e "${BOLD}Next steps:${RESET}"
echo "  1. Deschide $([ -n "$DJ_FOUND" ] && echo "$DJ_FOUND" || echo "Mixxx")"
echo "  2. Drag & drop playlists/*.m3u8 în sidebar-ul Playlists"
echo "  3. Fiecare playlist → right-click → Send to Auto DJ"
echo "  4. La eveniment: schimbi Auto DJ queue după bloc (A → B → C → ...)"
echo
echo -e "${BOLD}Backup pentru eveniment:${RESET}"
echo "  • Copiază muzica/ pe stick USB"
echo "  • Sync la iCloud/Google Drive"
echo
