#!/usr/bin/env bash
# Dispatch parallel Codex subagents for frame labeling
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_BASE="/tmp/yolodex-workers"
NUM_AGENTS="${1:-4}"

if ! [[ "$NUM_AGENTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: num_agents must be a positive integer (got: ${NUM_AGENTS})"
  exit 1
fi

if [ ! -f "${REPO_ROOT}/config.json" ]; then
  echo "Error: config.json not found at repo root."
  exit 1
fi

# Resolve output dir the same way shared.utils.load_config() does.
OUTPUT_DIR="$(
  REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import json
import os
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
config = json.loads((repo_root / "config.json").read_text(encoding="utf-8"))
if config.get("project"):
    print(f"runs/{config['project']}")
else:
    print(config.get("output_dir", "output"))
PY
)"
FRAMES_DIR="${REPO_ROOT}/${OUTPUT_DIR}/frames"
LABEL_MODE="$(
  REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import json
import os
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
config = json.loads((repo_root / "config.json").read_text(encoding="utf-8"))
print(str(config.get("label_mode", "gpt")).strip().lower())
PY
)"
CLASSES_CSV="$(
  REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import json
import os
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
config = json.loads((repo_root / "config.json").read_text(encoding="utf-8"))
classes = [str(c).strip() for c in config.get("classes", []) if str(c).strip()]
print(",".join(classes))
PY
)"

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: codex CLI not found. Install Codex to use parallel subagents."
  echo "Fallback: uv run .agents/skills/label/scripts/run.py"
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv not found. Install uv to run merge_classes.py."
  exit 1
fi

if ! git worktree list >/dev/null 2>&1; then
  echo "Error: git worktree is unavailable in this repository."
  exit 1
fi

if [ "$LABEL_MODE" != "gpt" ] && [ "$LABEL_MODE" != "codex" ]; then
  echo "Error: dispatch.sh supports label_mode=gpt or label_mode=codex (got: ${LABEL_MODE})"
  echo "For cua+sam/gemini use the dedicated label scripts."
  exit 1
fi

# Count frames
shopt -s nullglob
FRAMES=("${FRAMES_DIR}"/frame_*.jpg)
TOTAL=${#FRAMES[@]}

if [ "$TOTAL" -eq 0 ]; then
  echo "Error: No frames found in ${FRAMES_DIR}. Run collect first."
  exit 1
fi

BATCH_SIZE=$(( (TOTAL + NUM_AGENTS - 1) / NUM_AGENTS ))

echo "Dispatching ${NUM_AGENTS} subagents for ${TOTAL} frames (${BATCH_SIZE} each)"

mkdir -p "$WORKTREE_BASE"

pids=()
for i in $(seq 1 $NUM_AGENTS); do
  BRANCH="yolodex/labeler-${i}"
  DIR="${WORKTREE_BASE}/agent-${i}"
  START=$(( (i - 1) * BATCH_SIZE ))
  END=$(( i * BATCH_SIZE ))
  [ $END -gt $TOTAL ] && END=$TOTAL

  # Skip empty batches
  [ $START -ge $TOTAL ] && continue

  # Create isolated worktree
  git branch "$BRANCH" HEAD 2>/dev/null || true
  git worktree add "$DIR" "$BRANCH" 2>/dev/null || true

  # Copy frames to worktree's output dir
  mkdir -p "${DIR}/${OUTPUT_DIR}/frames"
  for j in $(seq $START $(( END - 1 ))); do
    cp "${FRAMES[$j]}" "${DIR}/${OUTPUT_DIR}/frames/"
  done

  # Launch Codex subagent in the worktree
  echo "  Agent ${i}: frames ${START}-${END} in ${DIR}"

  if [ "$LABEL_MODE" = "gpt" ] && [ -n "${OPENAI_API_KEY:-}" ]; then
    codex exec --skip-git-repo-check --full-auto -C "$DIR" \
      "You are a labeling subagent. Label all frames in ${OUTPUT_DIR}/frames/ using the label skill.
       Run: uv run .agents/skills/label/scripts/run_batch.py
       Do not modify any other files. Only create .txt label files next to each .jpg." \
      > "${DIR}/codex-output.log" 2>&1 &
  else
    codex exec --skip-git-repo-check --full-auto -C "$DIR" \
      "You are a vision labeling subagent. Do not use external APIs or API keys.
       Work only inside ${OUTPUT_DIR}/frames/.
       For each .jpg without a same-name .txt, inspect the image with the available image-viewing tool.
       Create YOLO labels in normalized format: <class_id> <cx> <cy> <w> <h>.
       Use only these classes: ${CLASSES_CSV}.
       Class id mapping must follow that class list order (0-based).
       Write ${OUTPUT_DIR}/classes.txt with exactly that class list order if missing.
       Do not edit any files outside labels/classes." \
      > "${DIR}/codex-output.log" 2>&1 &
  fi
  pids+=($!)
done

# Wait for all subagents to finish
echo "Waiting for all subagents..."
for pid in "${pids[@]}"; do
  wait "$pid" || echo "Warning: agent PID $pid failed"
done

# Merge label files back to main repo
echo "Merging label results..."
for i in $(seq 1 $NUM_AGENTS); do
  DIR="${WORKTREE_BASE}/agent-${i}"
  [ -d "$DIR" ] || continue
  # Copy .txt label files back
  cp "${DIR}/${OUTPUT_DIR}"/frames/*.txt "${FRAMES_DIR}/" 2>/dev/null || true
  # Cleanup
  git worktree remove "$DIR" --force 2>/dev/null || true
  git branch -D "yolodex/labeler-${i}" 2>/dev/null || true
done

# Merge class maps
uv run .agents/skills/label/scripts/merge_classes.py

echo "Parallel labeling complete. ${TOTAL} frames labeled."
