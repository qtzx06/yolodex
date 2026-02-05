---
name: yolodex
description: Train a custom YOLO object detection model from any YouTube gameplay video. Provide a video URL and target classes, and this skill handles the entire pipeline autonomously — frame extraction, AI-powered labeling, data augmentation, training, and evaluation with iterative improvement.
user_invocable: true
---

## Intake Flow

When the user wants to train a model, gather the following:

1. **Video source** (required): YouTube URL or local file path (e.g. `/Users/me/Desktop/gameplay.mp4`)
2. **Project name** (required): Short kebab-case name (e.g. "subway-surfers", "fortnite-clips"). Output goes to `runs/<project>/`
3. **Target classes** (required): What objects to detect (e.g. "players, weapons, vehicles")
3. **Labeling mode** (required): Ask the user which labeling method to use:
   - **CUA+SAM** (recommended): OpenAI CUA clicks on objects, SAM segments precise boundaries. Best accuracy. Requires `OPENAI_API_KEY`.
   - **Gemini**: Google Gemini native bounding box detection. Fast, good accuracy. Requires `GEMINI_API_KEY`.
   - **GPT**: GPT vision model returns bounding boxes via structured output. Simple fallback. Requires `OPENAI_API_KEY`.
   - **Codex**: Codex subagents use built-in image viewing and write YOLO labels directly. No API keys.
4. **Target accuracy** (optional, default 0.75): mAP@50 threshold
5. **Parallel agents** (optional, default 4): How many labeling subagents (GPT mode only)

## After Gathering Config

1. Write the values to `config.json`:
   ```python
   import json
   config = json.load(open("config.json"))
   config["project"] = "subway-surfers"  # output goes to runs/subway-surfers/
   config["video_url"] = "<user's url or local path>"
   config["classes"] = ["player", "weapon", ...]
   config["label_mode"] = "cua+sam"  # or "gemini" or "gpt" or "codex"
   config["target_accuracy"] = 0.75
   config["num_agents"] = 4
   json.dump(config, open("config.json", "w"), indent=2)
   ```

2. Then execute the pipeline phases in order by following the iteration logic in AGENTS.md:
   - `uv run .agents/skills/collect/scripts/run.py`
   - Labeling (based on mode):
     - CUA+SAM: `uv run .agents/skills/label/scripts/label_cua_sam.py`
     - Gemini: `uv run .agents/skills/label/scripts/label_gemini.py`
     - GPT (parallel / call subagent): `bash .agents/skills/label/scripts/dispatch.sh`
     - Codex (parallel / no-key): `bash .agents/skills/label/scripts/dispatch.sh`
     - GPT (single): `uv run .agents/skills/label/scripts/run.py`
   - `uv run .agents/skills/augment/scripts/run.py`
   - `uv run .agents/skills/train/scripts/run.py`
   - `uv run .agents/skills/eval/scripts/run.py`

3. Check `runs/<project>/eval_results.json` — if accuracy < target, re-label failures and retrain.

## Autonomous Mode

For fully autonomous execution, run: `bash yolodex.sh`
This is a Ralph-style loop that iterates until target accuracy is reached.

## Prerequisites

- `OPENAI_API_KEY` environment variable (for CUA+SAM and GPT modes)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` (for Gemini mode)
- No API key required when using `label_mode=codex` + `dispatch.sh`
- `yt-dlp` and `ffmpeg` installed
- `uv` for Python dependency management
- `codex` CLI (optional, for parallel subagent dispatch)
