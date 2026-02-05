---
name: yolodex
description: Train a custom YOLO object detection model from any YouTube gameplay video. Provide a video URL and target classes, and this skill handles the entire pipeline autonomously — frame extraction, AI-powered labeling, data augmentation, training, and evaluation with iterative improvement.
user_invocable: true
---

## Intake Flow

When the user wants to train a YOLO model, gather the following:

1. **YouTube URL** (required): Ask for the video URL
2. **Target classes** (required): What objects to detect (e.g. "players, weapons, vehicles")
3. **Target accuracy** (optional, default 0.75): mAP@50 threshold
4. **Parallel agents** (optional, default 4): How many labeling subagents

## After Gathering Config

1. Write the values to `config.json`:
   ```python
   import json
   config = json.load(open("config.json"))
   config["video_url"] = "<user's url>"
   config["classes"] = ["player", "weapon", ...]
   config["target_accuracy"] = 0.75
   config["num_agents"] = 4
   json.dump(config, open("config.json", "w"), indent=2)
   ```

2. Then execute the pipeline phases in order by following the iteration logic in AGENTS.md:
   - `uv run .agents/skills/collect/scripts/run.py`
   - `bash .agents/skills/label/scripts/dispatch.sh` (parallel) or `uv run .agents/skills/label/scripts/run.py` (single)
   - `uv run .agents/skills/augment/scripts/run.py`
   - `uv run .agents/skills/train/scripts/run.py`
   - `uv run .agents/skills/eval/scripts/run.py`

3. Check `output/eval_results.json` — if accuracy < target, re-label failures and retrain.

## Autonomous Mode

For fully autonomous execution, run: `bash yolodex.sh`
This is a Ralph-style loop that iterates until target accuracy is reached.

## Prerequisites

- `OPENAI_API_KEY` environment variable set
- `yt-dlp` and `ffmpeg` installed
- `uv` for Python dependency management
- `codex` CLI (for parallel subagent dispatch)
