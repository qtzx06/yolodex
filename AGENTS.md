# Yolodex

Autonomous YOLO training data generation from gameplay videos.

## Quick Start (Interactive)
If the user wants to train a model, use the **yolodex skill** (`.agents/skills/yolodex/SKILL.md`).
Ask for: YouTube URL, target classes, optional accuracy target. Then write to config.json and run the pipeline.

## Quick Start (Autonomous)
If config.json is already populated, just run: `bash yolodex.sh`

## Conventions
- Python with type hints, use `uv run` for execution
- Each skill in .agents/skills/ is independently runnable
- Use `codex exec --full-auto -C <path>` for parallel subagent dispatch
- Vision model: gpt-5-nano (fastest, cheapest for bounding box detection)
- YOLO model: yolov8n.pt (default, can be changed in config.json)

## Architecture
- Skills: yolodex (intake), collect, label (parallel), augment, train, eval
- Shared code: shared/utils.py
- Config: config.json | Memory: progress.txt

## Iteration Logic
Check state and execute next phase:

1. **No video** (output/video.mp4 missing):
   → Run collect: `uv run .agents/skills/collect/scripts/run.py`

2. **No frames** (output/frames/ empty):
   → Run collect: `uv run .agents/skills/collect/scripts/run.py`

3. **Frames but no labels** (no .txt files in output/frames/):
   → Run parallel label: `bash .agents/skills/label/scripts/dispatch.sh`
   This dispatches N subagents in worktrees for concurrent labeling.

4. **Labels but no model** (output/weights/best.pt missing):
   → Run augment: `uv run .agents/skills/augment/scripts/run.py`
   → Run train: `uv run .agents/skills/train/scripts/run.py`

5. **Model but no eval** (output/eval_results.json missing):
   → Run eval: `uv run .agents/skills/eval/scripts/run.py`

6. **Eval exists, accuracy >= target**: → `<promise>COMPLETE</promise>`

7. **Eval exists, accuracy < target**:
   → Read failure analysis from eval_results.json
   → Re-label worst frames or collect more data
   → Re-train and re-evaluate

## After Each Phase
- Append learnings to progress.txt
- Commit: `git add -A && git commit -m "iter: [phase] - [description]"`
