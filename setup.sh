#!/usr/bin/env bash
# Yolodex setup script — installs all dependencies and verifies the environment
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}
 ██    ██  ██████  ██       ██████  ██████  ███████ ██   ██
  ██  ██  ██    ██ ██      ██    ██ ██   ██ ██       ██ ██
   ████   ██    ██ ██      ██    ██ ██   ██ █████     ███
    ██    ██    ██ ██      ██    ██ ██   ██ ██       ██ ██
    ██     ██████  ███████  ██████  ██████  ███████ ██   ██
${NC}"
echo -e "${BLUE}Autonomous YOLO training from gameplay videos${NC}"
echo ""

# --- Helper functions ---

check_cmd() {
  command -v "$1" &>/dev/null
}

ok()   { echo -e "  ${GREEN}[ok]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[!!]${NC} $1"; }
fail() { echo -e "  ${RED}[fail]${NC} $1"; }

# --- Step 1: System dependencies ---

echo -e "${BLUE}[1/5] Checking system dependencies...${NC}"

MISSING=()

if check_cmd ffmpeg; then
  ok "ffmpeg $(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')"
else
  fail "ffmpeg not found"
  MISSING+=("ffmpeg")
fi

if check_cmd ffprobe; then
  ok "ffprobe"
else
  fail "ffprobe not found (comes with ffmpeg)"
  MISSING+=("ffmpeg")
fi

if check_cmd yt-dlp; then
  ok "yt-dlp $(yt-dlp --version 2>/dev/null || echo 'unknown')"
else
  fail "yt-dlp not found"
  MISSING+=("yt-dlp")
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  echo ""
  # Deduplicate
  UNIQUE_MISSING=($(echo "${MISSING[@]}" | tr ' ' '\n' | sort -u))
  if check_cmd brew; then
    echo -e "  Installing missing deps with homebrew..."
    brew install "${UNIQUE_MISSING[@]}"
    ok "Installed: ${UNIQUE_MISSING[*]}"
  elif check_cmd apt-get; then
    echo -e "  Installing missing deps with apt..."
    sudo apt-get update -qq && sudo apt-get install -y "${UNIQUE_MISSING[@]}"
    ok "Installed: ${UNIQUE_MISSING[*]}"
  else
    fail "Cannot auto-install. Please install manually: ${UNIQUE_MISSING[*]}"
    echo "  macOS: brew install ${UNIQUE_MISSING[*]}"
    echo "  Ubuntu: sudo apt install ${UNIQUE_MISSING[*]}"
    exit 1
  fi
fi

# --- Step 2: Python + uv ---

echo ""
echo -e "${BLUE}[2/5] Checking Python environment...${NC}"

if check_cmd uv; then
  ok "uv $(uv --version 2>/dev/null | awk '{print $2}')"
else
  echo -e "  Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source the updated PATH
  export PATH="$HOME/.local/bin:$PATH"
  if check_cmd uv; then
    ok "uv installed"
  else
    fail "uv installation failed. See https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
  fi
fi

# --- Step 3: Python dependencies ---

echo ""
echo -e "${BLUE}[3/5] Installing Python dependencies...${NC}"

cd "$SCRIPT_DIR"
uv sync 2>&1 | tail -5
ok "Python dependencies installed ($(uv pip list 2>/dev/null | wc -l | tr -d ' ') packages)"

# --- Step 4: Environment variables ---

echo ""
echo -e "${BLUE}[4/5] Checking environment...${NC}"

if [ -n "${OPENAI_API_KEY:-}" ]; then
  ok "OPENAI_API_KEY is set"
else
  warn "OPENAI_API_KEY is not set"
  echo "       You'll need this for the label skill (vision model)."
  echo "       export OPENAI_API_KEY=\"sk-...\""
fi

# --- Step 5: Optional tools ---

echo ""
echo -e "${BLUE}[5/5] Checking optional tools...${NC}"

if check_cmd codex; then
  ok "codex CLI (for parallel labeling + autonomous loop)"
else
  warn "codex CLI not found (optional — needed for parallel labeling and yolodex.sh)"
  echo "       Install: npm install -g @openai/codex"
fi

if check_cmd bun; then
  ok "bun (for landing page dev server)"
else
  warn "bun not found (optional — for landing page: cd landing && bunx serve .)"
fi

# --- Make scripts executable ---

chmod +x "$SCRIPT_DIR/yolodex.sh"
chmod +x "$SCRIPT_DIR/yolodex-doctor.sh"
chmod +x "$SCRIPT_DIR/.agents/skills/label/scripts/dispatch.sh"

# --- Done ---

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Set your OpenAI key (if not already):"
echo "     export OPENAI_API_KEY=\"sk-...\""
echo ""
echo "  2. Edit config.json with your video URL and classes:"
echo "     {\"video_url\": \"https://youtube.com/...\", \"classes\": [\"player\", \"weapon\"]}"
echo ""
echo "  3. Run the pipeline:"
echo "     bash yolodex-doctor.sh   # preflight checks"
echo "     bash yolodex.sh          # autonomous loop"
echo "     # OR run skills manually:"
echo "     uv run .agents/skills/collect/scripts/run.py"
echo "     uv run .agents/skills/label/scripts/run.py"
echo "     uv run .agents/skills/augment/scripts/run.py"
echo "     uv run .agents/skills/train/scripts/run.py"
echo "     uv run .agents/skills/eval/scripts/run.py"
echo ""
echo "  4. View results:"
echo "     cat output/eval_results.json"
echo "     cd landing && bunx serve .    # web dashboard"
echo ""
