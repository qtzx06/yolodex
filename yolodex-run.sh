#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MAX_ITERATIONS="${1:-}"

if [ -z "$MAX_ITERATIONS" ]; then
  MAX_ITERATIONS="$(
    python3 - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("config.json").read_text(encoding="utf-8"))
print(int(config.get("max_iterations", 10)))
PY
  )"
fi

echo "[run] preflight checks..."
bash "$SCRIPT_DIR/yolodex-doctor.sh"

echo ""
echo "[run] status before execution..."
bash "$SCRIPT_DIR/yolodex-status.sh"

echo ""
echo "[run] starting codex loop (max_iterations=${MAX_ITERATIONS})..."
set +e
bash "$SCRIPT_DIR/yolodex.sh" "$MAX_ITERATIONS"
RUN_EXIT_CODE=$?
set -e

echo ""
echo "[run] status after execution..."
bash "$SCRIPT_DIR/yolodex-status.sh"

if [ "$RUN_EXIT_CODE" -ne 0 ]; then
  echo ""
  echo "[run] pipeline exited with non-zero status: $RUN_EXIT_CODE"
  exit "$RUN_EXIT_CODE"
fi

echo ""
echo "[run] pipeline finished successfully."
