#!/usr/bin/env bash
# Dispatch parallel Codex subagents for frame labeling
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
FRAMES_DIR="${REPO_ROOT}/output/frames"
WORKTREE_BASE="/tmp/yolodex-workers"
NUM_AGENTS="${1:-4}"

# Count frames
FRAMES=($(ls -1 "${FRAMES_DIR}"/frame_*.jpg 2>/dev/null))
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
  mkdir -p "${DIR}/output/frames"
  for j in $(seq $START $(( END - 1 ))); do
    cp "${FRAMES[$j]}" "${DIR}/output/frames/"
  done

  # Launch Codex subagent in the worktree
  echo "  Agent ${i}: frames ${START}-${END} in ${DIR}"
  codex exec --full-auto -C "$DIR" \
    "You are a labeling subagent. Label all frames in output/frames/ using the label skill.
     Run: uv run .agents/skills/label/scripts/run_batch.py
     Do not modify any other files. Only create .txt label files next to each .jpg." \
    > "${DIR}/codex-output.log" 2>&1 &
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
  cp "${DIR}"/output/frames/*.txt "${FRAMES_DIR}/" 2>/dev/null || true
  # Cleanup
  git worktree remove "$DIR" --force 2>/dev/null || true
  git branch -D "yolodex/labeler-${i}" 2>/dev/null || true
done

# Merge class maps
uv run .agents/skills/label/scripts/merge_classes.py

echo "Parallel labeling complete. ${TOTAL} frames labeled."
