# Yolodex

Autonomous YOLO training data generation from gameplay videos.

## Quick Start (Interactive)
If the user wants to train a model, use the **yolodex skill** (`.agents/skills/yolodex/SKILL.md`).
Ask for: YouTube URL (or local video path), target classes, **labeling mode** (cua+sam / gemini / gpt / codex), optional accuracy target.
Then write to config.json (set `project` for named output in `runs/<project>/`) and run the pipeline.
If the user says `call subagent` for labeling, execute:
`bash .agents/skills/label/scripts/dispatch.sh [num_agents]`

## Quick Start (Autonomous)
If config.json is already populated, just run: `bash yolodex.sh`

## Conventions
- Python with type hints, use `uv run` for execution
- Each skill in .agents/skills/ is independently runnable
- Use `codex exec --full-auto -C <path>` for parallel subagent dispatch
- Label modes: `cua+sam` (CUA clicks + SAM segmentation), `gemini` (native bbox), `gpt` (fallback), `codex` (subagent image-view mode, no API keys)
- YOLO model: yolov8n.pt (default, can be changed in config.json)

## Architecture
- Skills: yolodex (intake), collect, label (parallel), augment, train, eval
- Shared code: shared/utils.py
- Config: config.json | Memory: progress.txt

## Output Directory
When `project` is set in config.json, output goes to `runs/<project>/` (e.g. `runs/subway-surfers/`).
When `project` is empty, falls back to `output_dir` (default `output/`).
All skills read `output_dir` from config — the `load_config()` helper resolves this automatically.

## Iteration Logic
Check state and execute next phase (paths relative to output_dir):

1. **No video** (video.mp4 missing):
   → Run collect: `uv run .agents/skills/collect/scripts/run.py`

2. **No frames** (frames/ empty):
   → Run collect: `uv run .agents/skills/collect/scripts/run.py`

3. **Frames but no labels** (no .txt files in frames/):
   → Check `label_mode` in config.json:
     - `cua+sam`: `uv run .agents/skills/label/scripts/label_cua_sam.py`
     - `gemini`: `uv run .agents/skills/label/scripts/label_gemini.py`
     - `gpt` (parallel / subagent): `bash .agents/skills/label/scripts/dispatch.sh`
     - `codex` (parallel / no-key): `bash .agents/skills/label/scripts/dispatch.sh`
     - `gpt` (single): `uv run .agents/skills/label/scripts/run.py`

4. **Labels but no model** (weights/best.pt missing):
   → Run augment: `uv run .agents/skills/augment/scripts/run.py`
   → Run train: `uv run .agents/skills/train/scripts/run.py`

5. **Model but no eval** (eval_results.json missing):
   → Run eval: `uv run .agents/skills/eval/scripts/run.py`

6. **Eval exists, accuracy >= target**: → `<promise>COMPLETE</promise>`

7. **Eval exists, accuracy < target**:
   → Read failure analysis from eval_results.json
   → Re-label worst frames or collect more data
   → Re-train and re-evaluate

## After Each Phase
- Append learnings to progress.txt
- Commit: `git add -A && git commit -m "iter: [phase] - [description]"`
