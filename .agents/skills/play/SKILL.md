---
name: play
description: Run a deterministic real-time game bot using MSS capture + YOLO detections + state machine controls.
---

## Instructions
1. Ensure training produced weights at `runs/<project>/weights/best.pt` or set `bot.model_path`.
2. Optional calibration:
   - `uv run .agents/skills/play/scripts/run.py --list-games`
   - `uv run .agents/skills/play/scripts/run.py --game <game> --monitor-info`
3. Start gameplay bot:
   - `uv run .agents/skills/play/scripts/run.py --game <game>`
4. Runtime hotkeys (default):
   - `f8` toggle start/stop
   - `f9` emergency kill
5. Keep the browser game visible within configured ROI.

