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

## how to run

interactive: codex reads AGENTS.md, asks for url + classes, writes config, runs pipeline

autonomous: populate config.json, then `bash yolodex.sh`

individual skills: `uv run .agents/skills/<name>/scripts/run.py`
