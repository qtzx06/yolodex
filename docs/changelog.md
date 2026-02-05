# changelog

## 2026-02-05: skill-based pipeline rewrite

replaced the monolithic pipeline with a codex skill architecture and parallel labeling system.

### what changed from the original

| before | after |
|--------|-------|
| single `pipeline/main.py` monolith | 5 independent codex skills in `.agents/skills/` |
| no training or eval | full ultralytics yolo training + mAP evaluation |
| no augmentation | synthetic augmentation (flip, brightness, contrast, noise) |
| sequential labeling only | parallel labeling via codex subagents in git worktrees |
| no iteration loop | ralph-style autonomous loop (`yolodex.sh`) |
| no shared code | `shared/utils.py` with extracted common utilities |
| basic AGENTS.md | AGENTS.md with full iteration logic for codex |
| no landing page | landing page with pipeline viz + live eval stats |
| `requirements.txt` only | `pyproject.toml` with uv support |

### files created

- `shared/__init__.py`, `shared/utils.py` — extracted BoundingBox, PipelineError, helpers
- `.agents/skills/collect/` — SKILL.md + run.py (yt-dlp download, ffmpeg frame extraction)
- `.agents/skills/label/` — SKILL.md + run.py (single-agent), run_batch.py (subagent), dispatch.sh (parallel orchestrator), merge_classes.py
- `.agents/skills/augment/` — SKILL.md + run.py (pillow-based augmentation with label transforms)
- `.agents/skills/train/` — SKILL.md + run.py (dataset split, yaml gen, ultralytics training)
- `.agents/skills/eval/` — SKILL.md + run.py (model.val(), mAP metrics, per-class breakdown, eval_results.json)
- `yolodex.sh` — ralph loop orchestrator using `codex exec`
- `AGENTS.md` — rewritten with iteration logic, quick start, conventions
- `config.json` — pipeline configuration
- `pyproject.toml` — uv project config
- `.gitignore` — output, python, node, os artifacts
- `progress.txt` — cross-iteration memory log
- `landing/` — index.html, style.css, package.json

### files preserved

- `pipeline/main.py` — original monolith kept as reference, untouched

### what was on remote and removed

the remote main had 3 commits with a flat `skills/` structure, deleted `pipeline/main.py`, placeholder train/eval/augment scripts, and a simulated accuracy eval. all of that was replaced by this rewrite.
