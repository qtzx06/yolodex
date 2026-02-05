---
name: train
description: Train a YOLO model on labeled dataset using ultralytics. Splits data into train/val, generates dataset.yaml, and produces trained weights. Use after labeling and augmenting.
---

## Instructions
1. Read config.json for yolo_model, epochs, train_split, output_dir
2. Run: uv run .agents/skills/train/scripts/run.py
3. Outputs: output/weights/best.pt, output/dataset.yaml
