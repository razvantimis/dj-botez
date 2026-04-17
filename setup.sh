#!/usr/bin/env bash
# Setup complet pentru Botez Amalia DJ kit.
# Instalează dependențe, descarcă piese, generează playlist-uri Mixxx.
#
# Usage:
#   ./setup.sh              # full setup (dependencies + download + playlists)
#   ./setup.sh --skip-deps  # sari peste brew install (dacă deja ai yt-dlp/ffmpeg/mixxx)
#   ./setup.sh --no-mixxx   # nu instala Mixxx (dacă preferi alt player)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Flags
SKIP_DEPS=false
NO_MIXXX=false
for arg in "$@"; do
  case "$arg" in
    --skip-deps) SKIP_DEPS=true ;;
    --no-mixxx)  NO_MIXXX=true ;;
    -h|--help)
      grep '^# ' "$0" | sed 's/^# //'
      exit 0
      ;;
  esac
done

# Colors
BOLD='\033[1m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
step() { echo -e "\n${BOLD}▶ $*${RESET}"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
fail() { echo -e "${RED}✗${RESET} $*"; exit 1; }

# 1. Verifică OS
step "Verificare platformă"
OS="$(uname -s)"
case "$OS" in
  Darwin) ok "macOS detectat" ;;
  Linux)  ok "Linux detectat (suport parțial — instalare manuală pentru Mixxx)" ;;
  *)      fail "OS nesuportat: $OS (doar macOS și Linux)" ;;
esac

# 2. Verifică Python 3
step "Verificare Python 3"
command -v python3 >/dev/null 2>&1 || fail "python3 lipsește. Instalează: brew install python3"
ok "python3 $(python3 --version | cut -d' ' -f2)"

# 3. Install dependencies
if ! $SKIP_DEPS; then
  step "Instalare dependențe (yt-dlp, ffmpeg$($NO_MIXXX || echo ", mixxx"))"

  if [ "$OS" = "Darwin" ]; then
    command -v brew >/dev/null 2>&1 || fail "Homebrew lipsește. Instalează de la https://brew.sh"

    if ! command -v yt-dlp >/dev/null 2>&1; then
      echo "  installing yt-dlp..."; brew install yt-dlp
    else ok "yt-dlp $(yt-dlp --version)"; fi

    if ! command -v ffmpeg >/dev/null 2>&1; then
      echo "  installing ffmpeg..."; brew install ffmpeg
    else ok "ffmpeg $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)"; fi

    if ! $NO_MIXXX; then
      if ! [ -d "/Applications/Mixxx.app" ]; then
        echo "  installing Mixxx (cask, durează ~1min)..."; brew install --cask mixxx
      else ok "Mixxx deja instalat"; fi
    fi

  elif [ "$OS" = "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update && sudo apt-get install -y yt-dlp ffmpeg
      $NO_MIXXX || sudo apt-get install -y mixxx
    else
      fail "Apt-get lipsește. Instalează manual: yt-dlp, ffmpeg$($NO_MIXXX || echo ", mixxx")"
    fi
  fi
else
  ok "Skip dependencies (--skip-deps)"
fi

# 4. Download tracks
step "Descărcare piese (yt-dlp)"
if [ -d "muzica" ] && [ "$(find muzica -name '*.m4a' | wc -l | tr -d ' ')" = "115" ]; then
  ok "muzica/ deja complet (115 piese). Re-rulez pentru skip-check..."
fi
python3 download-muzica.py

# 5. Generate playlists
step "Generare playlist-uri Mixxx (.m3u8)"
python3 generate-playlists.py

# 6. Done
step "Setup complet!"
echo
echo "${BOLD}Ce ai acum:${RESET}"
echo "  • muzica/           — 115 piese m4a în 10 blocuri"
echo "  • playlists/        — 10 fișiere .m3u8 pentru Mixxx"
echo "  • plan-botez-amalia.md — planul complet al set-ului"
echo
echo "${BOLD}Next steps:${RESET}"
echo "  1. Deschide Mixxx"
echo "  2. Drag & drop playlists/*.m3u8 în sidebar-ul Playlists"
echo "  3. Fiecare playlist → right-click → Send to Auto DJ"
echo "  4. La eveniment: schimbi Auto DJ queue după bloc (A → B → C → ...)"
echo
echo "${BOLD}Backup recomandat pentru eveniment:${RESET}"
echo "  • Copiază muzica/ pe stick USB"
echo "  • Sync muzica/ la iCloud/Google Drive"
echo
