# yolodex architecture

## what it does

takes a youtube gameplay url and autonomously produces a trained yolo model through an iterative loop: collect frames, label with vision llm, augment, train, evaluate, repeat until target accuracy.

## pipeline stages

```
youtube url + target classes
       |
       v
  +---------+     +-------+     +---------+     +-------+     +------+
  | collect | --> | label | --> | augment | --> | train | --> | eval |
  +---------+     +-------+     +---------+     +-------+     +------+
                     |                                            |
              parallel subagents                          meets target?
              in git worktrees                           no -> loop back
                                                         yes -> done
```

## key innovation: parallel labeling

frames are split into N batches. each batch gets its own git worktree and a codex subagent (`codex exec --full-auto -C <worktree>`). all agents label concurrently, then results merge back.

## subagent-first orchestration

for `label_mode = gpt`, subagents are the primary parallel path:

1. dispatcher resolves `output_dir` from `config.json` (`runs/<project>/` when project is set)
2. preflight verifies `codex`, `uv`, and `git worktree`
3. each agent runs `run_batch.py` in an isolated worktree
4. labels and class maps are merged back into the main run directory

trigger phrase in interactive sessions: `call subagent ...`
for keyless operation, use `label_mode = codex` so subagents label via Codex image viewing instead of API keys.

## directory layout

```
yolodex/
├── .agents/skills/          # codex skills (each has SKILL.md + scripts/)
│   ├── collect/             # download video, extract frames
│   ├── label/               # vision labeling (single + parallel modes)
│   ├── augment/             # synthetic data augmentation
│   ├── train/               # ultralytics yolo training
│   └── eval/                # mAP metrics + failure analysis
├── shared/                  # shared python utils (BoundingBox, helpers)
├── pipeline/main.py         # original monolith (preserved, not used by skills)
├── landing/                 # project landing page
├── yolodex.sh               # ralph-style autonomous loop orchestrator
├── AGENTS.md                # codex reads this automatically for iteration logic
├── config.json              # pipeline configuration
└── progress.txt             # cross-iteration memory (append-only)
```

## config.json

| field | purpose |
|-------|---------|
| video_url | youtube url to process |
| classes | target object classes (empty = auto-detect) |
| target_accuracy | mAP@50 threshold to stop iterating |
| max_iterations | safety cap on loop iterations |
| num_agents | parallel labeling agents |
| fps | frame extraction rate |
| model | vision model for labeling |
| yolo_model | ultralytics model to train |
| epochs | training epochs per iteration |
| train_split | train/val split ratio |

## models

- **vision labeling**: gpt-5-nano (default, fastest/cheapest), gpt-4.1-mini (best value), gpt-4o (legacy)
- **YOLO training**: yolov8n.pt (default, fast), yolov8s/m/l/x.pt (progressively more accurate)
- uses structured outputs (responses API) so vision model always returns valid JSON

see [models.md](models.md) for full comparison.

## how to run

interactive: codex reads AGENTS.md, asks for url + classes, writes config, runs pipeline

autonomous: populate config.json, then `bash yolodex.sh`

individual skills: `uv run .agents/skills/<name>/scripts/run.py`

see [usage.md](usage.md) for detailed walkthrough.

## docs index

- [usage.md](usage.md) — how to run (quick start, manual, autonomous)
- [models.md](models.md) — vision + YOLO model comparison and pricing
- [skills.md](skills.md) — detailed reference for each skill
- [changelog.md](changelog.md) — what changed from the original monolith
