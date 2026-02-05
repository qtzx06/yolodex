---
name: augment
description: Generate synthetic training data variations using image transforms. Increases dataset diversity with flips, brightness jitter, and noise. Use after labeling.
---

## Instructions
1. Read config.json for output_dir
2. Run: uv run .agents/skills/augment/scripts/run.py
3. Outputs: output/augmented/ with transformed images and labels
