---
name: label
description: Auto-label frames using GPT-4o vision with parallel Codex subagents in git worktrees. Splits frames into batches and dispatches concurrent labeling agents. Use after collecting frames.
---

## Instructions
1. Read config.json for classes, model, num_agents
2. For parallel labeling (recommended):
   Run: bash .agents/skills/label/scripts/dispatch.sh [num_agents]
   This creates N git worktrees, dispatches N Codex subagents, merges results.
3. For single-agent labeling (fallback):
   Run: uv run .agents/skills/label/scripts/run.py
4. Outputs: output/frames/*.txt (YOLO labels), output/classes.txt
