#!/usr/bin/env bash
# Ralph-style autonomous loop: iterates until target accuracy or max iterations
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_ITERATIONS="${1:-10}"
LOG_FILE="$SCRIPT_DIR/yolodex.log"

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

[ ! -f "$SCRIPT_DIR/progress.txt" ] && echo "# Yolodex Progress Log" > "$SCRIPT_DIR/progress.txt"

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "=== Yolodex Iteration $i/$MAX_ITERATIONS ==="

  OUTPUT=$(codex exec --full-auto \
    "Execute the next phase of the Yolodex pipeline. Read AGENTS.md for iteration logic.
     Check config.json, progress.txt, and output/eval_results.json to determine current state.
     Use parallel subagents (dispatch.sh) for labeling when num_agents > 1." \
    2>&1) || true

  echo "$OUTPUT"
  echo "$OUTPUT" >> "$LOG_FILE"

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "Target accuracy reached at iteration $i!"
    exit 0
  fi
  sleep 2
done

echo "Max iterations ($MAX_ITERATIONS) reached."
exit 1
