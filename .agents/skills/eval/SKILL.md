---
name: eval
description: Evaluate trained YOLO model accuracy with mAP metrics and per-class error analysis. Identifies failure cases for targeted improvement. Use after training.
---

## Instructions
1. Read config.json for output_dir, target_accuracy
2. Run: uv run .agents/skills/eval/scripts/run.py
3. Outputs: output/eval_results.json with mAP, precision, recall, per-class breakdown
