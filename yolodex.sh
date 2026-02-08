#!/usr/bin/env bash
# Ralph-style autonomous loop: iterates until target accuracy or max iterations
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_ITERATIONS="${1:-10}"
LOG_FILE="$SCRIPT_DIR/yolodex.log"
MAX_CONSECUTIVE_FAILURES="${MAX_CONSECUTIVE_FAILURES:-3}"

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

[ ! -f "$SCRIPT_DIR/progress.txt" ] && echo "# Yolodex Progress Log" > "$SCRIPT_DIR/progress.txt"

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI not found. Install Codex CLI to run yolodex.sh."
  exit 1
fi

if [ ! -f "$SCRIPT_DIR/config.json" ]; then
  echo "Error: config.json not found at repo root."
  exit 1
fi

OUTPUT_DIR="$(
  SCRIPT_DIR="$SCRIPT_DIR" python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["SCRIPT_DIR"])
config = json.loads((root / "config.json").read_text(encoding="utf-8"))
if config.get("project"):
    print(f"runs/{config['project']}")
else:
    print(config.get("output_dir", "output"))
PY
)"
JOB_STATE_PATH="$SCRIPT_DIR/$OUTPUT_DIR/job_state.json"
EVAL_RESULTS_PATH="$SCRIPT_DIR/$OUTPUT_DIR/eval_results.json"

consecutive_failures=0

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "=== Yolodex Iteration $i/$MAX_ITERATIONS ==="

  set +e
  OUTPUT=$(codex exec --full-auto \
    "Execute the next phase of the Yolodex pipeline. Read AGENTS.md for iteration logic.
     Check config.json, progress.txt, and ${OUTPUT_DIR}/eval_results.json to determine current state.
     Use parallel subagents (dispatch.sh) for labeling when num_agents > 1." \
    2>&1)
  exit_code=$?
  set -e

  echo "$OUTPUT"
  echo "$OUTPUT" >> "$LOG_FILE"

  if [ "$exit_code" -ne 0 ]; then
    consecutive_failures=$((consecutive_failures + 1))
    echo "Iteration $i failed (exit code: $exit_code). Consecutive failures: $consecutive_failures/$MAX_CONSECUTIVE_FAILURES"
    if [ "$consecutive_failures" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
      echo "Stopping early after repeated failures."
      exit 1
    fi
    sleep 2
    continue
  fi

  consecutive_failures=0

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "Target accuracy reached at iteration $i!"
    exit 0
  fi

  if [ -f "$EVAL_RESULTS_PATH" ]; then
    if python3 - <<'PY' "$EVAL_RESULTS_PATH"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
raise SystemExit(0 if bool(payload.get("meets_target")) else 1)
PY
    then
      echo "Target accuracy reached at iteration $i (from eval_results.json)."
      exit 0
    fi
  fi

  if [ -f "$JOB_STATE_PATH" ]; then
    if python3 - <<'PY' "$JOB_STATE_PATH"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
raise SystemExit(0 if str(payload.get("status", "")).lower() == "failed" else 1)
PY
    then
      echo "Pipeline reported failed state in job_state.json. Stopping."
      exit 1
    fi
  fi
  sleep 2
done

echo "Max iterations ($MAX_ITERATIONS) reached."
exit 1
