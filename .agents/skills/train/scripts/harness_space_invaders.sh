#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

PROJECT="space-invaders-v1"
GAME="space-invaders"
EPOCHS=3
MODE="${1:-full}"

EXPECTED_WEIGHTS="runs/${PROJECT}/weights/best.pt"
ALT_WEIGHTS_1="runs/${PROJECT}/yolo_run/weights/best.pt"
ALT_WEIGHTS_2="runs/detect/runs/${PROJECT}/yolo_run/weights/best.pt"

usage() {
  cat <<'EOF'
Space Invaders Harness

Usage:
  bash .agents/skills/train/scripts/harness_space_invaders.sh [mode]

Modes:
  preflight     Validate dataset/config/runtime prerequisites
  train3        Train Space Invaders for 3 epochs
  sync-weights  Copy best.pt from known ultralytics output paths to runs/space-invaders-v1/weights/best.pt
  input-test    Send direct keyboard test inputs for 15s (no detection/model loop)
  play-dry      Start play bot in dry-run mode
  play-live     Start play bot live, active immediately, with line-by-line terminal logs
  full          preflight + train3 + sync-weights

Notes:
  - Project is fixed to "space-invaders-v1"
  - Game preset is fixed to "space-invaders"
EOF
}

preflight() {
  cd "${REPO_ROOT}"
  echo "[harness] preflight: repo=${REPO_ROOT}"

  if [[ ! -f "config.json" ]]; then
    echo "[harness] missing config.json"
    exit 1
  fi

  if [[ ! -f "runs/${PROJECT}/classes.txt" ]]; then
    echo "[harness] missing runs/${PROJECT}/classes.txt"
    echo "[harness] run labeling first, then training"
    exit 1
  fi

  if ! ls "runs/${PROJECT}/frames/"*.txt >/dev/null 2>&1; then
    echo "[harness] no frame labels found under runs/${PROJECT}/frames/"
    echo "[harness] run labeling first, then training"
    exit 1
  fi

  echo "[harness] checking torch + ultralytics imports..."
  uv run python - <<'PY'
import torch
import ultralytics
print("[harness] torch_ok", getattr(torch, "__version__", "unknown"), "has_save", hasattr(torch, "save"))
print("[harness] ultralytics_ok", getattr(ultralytics, "__version__", "unknown"))
if not hasattr(torch, "save"):
    raise SystemExit("torch is installed but missing torch.save; reinstall env with `uv sync --reinstall`")
PY
}

train3() {
  cd "${REPO_ROOT}"
  echo "[harness] train3: project=${PROJECT} epochs=${EPOCHS}"
  uv run .agents/skills/train/scripts/run.py --project "${PROJECT}" --epochs "${EPOCHS}"
}

sync_weights() {
  cd "${REPO_ROOT}"
  mkdir -p "runs/${PROJECT}/weights"

  if [[ -f "${EXPECTED_WEIGHTS}" ]]; then
    echo "[harness] weights already present: ${EXPECTED_WEIGHTS}"
    return 0
  fi

  if [[ -f "${ALT_WEIGHTS_1}" ]]; then
    cp "${ALT_WEIGHTS_1}" "${EXPECTED_WEIGHTS}"
    echo "[harness] synced weights from ${ALT_WEIGHTS_1} -> ${EXPECTED_WEIGHTS}"
    return 0
  fi

  if [[ -f "${ALT_WEIGHTS_2}" ]]; then
    cp "${ALT_WEIGHTS_2}" "${EXPECTED_WEIGHTS}"
    echo "[harness] synced weights from ${ALT_WEIGHTS_2} -> ${EXPECTED_WEIGHTS}"
    return 0
  fi

  echo "[harness] could not find best.pt in known output paths"
  echo "[harness] checked:"
  echo "  - ${EXPECTED_WEIGHTS}"
  echo "  - ${ALT_WEIGHTS_1}"
  echo "  - ${ALT_WEIGHTS_2}"
  exit 1
}

play_dry() {
  cd "${REPO_ROOT}"
  echo "[harness] play-dry: game=${GAME}"
  uv run .agents/skills/play/scripts/run.py --game "${GAME}" --dry-run --start-active
}

input_test() {
  cd "${REPO_ROOT}"
  echo "[harness] input-test: game=${GAME} duration=15s"
  uv run .agents/skills/play/scripts/run.py --game "${GAME}" --input-test-seconds 15 --status-lines
}

play_live() {
  cd "${REPO_ROOT}"
  echo "[harness] play-live: game=${GAME} (start-active, status-lines)"
  uv run .agents/skills/play/scripts/run.py --game "${GAME}" --start-active --status-lines
}

case "${MODE}" in
  preflight)
    preflight
    ;;
  train3)
    train3
    ;;
  sync-weights)
    sync_weights
    ;;
  input-test)
    input_test
    ;;
  play-dry)
    play_dry
    ;;
  play-live)
    play_live
    ;;
  full)
    preflight
    train3
    sync_weights
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "[harness] unknown mode: ${MODE}"
    usage
    exit 1
    ;;
esac
