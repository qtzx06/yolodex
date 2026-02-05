---
name: label
description: Auto-label frames with bounding boxes. Supports four modes — CUA+SAM (best accuracy, OpenAI CUA clicks + SAM segmentation), Gemini (native bbox detection), GPT vision (API fallback), or Codex vision subagents (no API keys). Parallel dispatch via git worktrees. Use after collecting frames.
---

## Labeling Modes

Set `label_mode` in config.json:

| Mode | How it works | Best for |
|------|-------------|----------|
| **`cua+sam`** | CUA clicks on objects → SAM segments precise boundaries | Best accuracy, hackathon demo |
| **`gemini`** | Gemini native bounding box detection (0-1000 scale) | Fast, good native bbox support |
| **`gpt`** | GPT vision model returns JSON bounding boxes | Simple fallback |
| **`codex`** | Codex subagents view images and write YOLO labels directly | No API keys |

## Instructions

1. Read config.json for `label_mode`, `classes`, `model`, `num_agents`
   If the user asks to `call subagent`, route to parallel dispatch in step 5.

2. **CUA+SAM mode** (recommended):
   Run: `uv run .agents/skills/label/scripts/label_cua_sam.py`
   Requires: `OPENAI_API_KEY`, classes must be set in config.json

3. **Gemini mode**:
   Run: `uv run .agents/skills/label/scripts/label_gemini.py`
   Requires: `GEMINI_API_KEY` or `GOOGLE_API_KEY`

4. **GPT mode** (fallback):
   Run: `uv run .agents/skills/label/scripts/run.py`
   Requires: `OPENAI_API_KEY`

5. **Parallel dispatch** (GPT or Codex mode):
   Run: `bash .agents/skills/label/scripts/dispatch.sh [num_agents]`
   Creates N git worktrees, dispatches N Codex subagents, merges results.
   If Codex subagents are unavailable in-session, this shell command is the fallback path.
   Supports:
   - `label_mode=gpt` with `OPENAI_API_KEY` (runs `run_batch.py`)
   - `label_mode=codex` without API keys (Codex image-viewing subagents)

6. Outputs: `output/frames/*.txt` (YOLO labels), `output/classes.txt`

## Scripts

| Script | Mode | Description |
|--------|------|-------------|
| `label_cua_sam.py` | cua+sam | CUA for clicks + SAM for segmentation |
| `label_gemini.py` | gemini | Gemini native bounding boxes |
| `run.py` | gpt | GPT vision structured output |
| `run_batch.py` | gpt | GPT vision (subagent batch mode) |
| `dispatch.sh` | gpt/codex | Parallel subagent orchestrator |
| `merge_classes.py` | all | Unify class maps from subagents |
| `auto_label_and_show.py` | all | Auto-run configured labeler and print/render label previews |
