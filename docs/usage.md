# usage guide

## prerequisites

```bash
# CLI tools
brew install yt-dlp ffmpeg

# python (via uv)
brew install uv
uv sync

# environment
export OPENAI_API_KEY="sk-..."
```

## quick start

### option 1: interactive (codex plugin)

open codex in the yolodex directory. it reads AGENTS.md automatically.

```
$ cd yolodex
$ codex

> train a YOLO model to detect players and weapons from this video: https://youtube.com/watch?v=...
```

codex will:
1. ask for target classes, accuracy threshold, agent count
2. write config.json
3. run the full pipeline: collect -> label -> augment -> train -> eval
4. loop if accuracy < target

### option 2: autonomous (ralph loop)

edit config.json manually, then run:

```bash
# edit config
cat config.json
# set video_url, classes, etc.

# run up to 10 iterations
bash yolodex.sh 10
```

the loop runs `codex exec --full-auto` each iteration. it checks AGENTS.md for what to do next based on what files exist in `output/`.

### option 3: manual (skill by skill)

```bash
# 1. download video + extract frames
uv run .agents/skills/collect/scripts/run.py

# 2. label frames (pick one)
bash .agents/skills/label/scripts/dispatch.sh 4    # parallel (4 agents)
uv run .agents/skills/label/scripts/run.py          # single agent

# 3. augment training data
uv run .agents/skills/augment/scripts/run.py

# 4. train YOLO model
uv run .agents/skills/train/scripts/run.py

# 5. evaluate
uv run .agents/skills/eval/scripts/run.py
```

## config.json reference

```json
{
  "video_url": "",              // youtube URL (required)
  "classes": [],                // target classes e.g. ["player", "weapon"] (empty = auto-detect)
  "target_accuracy": 0.75,      // mAP@50 threshold to stop (0.0-1.0)
  "max_iterations": 10,         // ralph loop safety cap
  "num_agents": 4,              // parallel labeling agents
  "fps": 1,                    // frame extraction rate (frames per second)
  "output_dir": "output",      // where all outputs go
  "model": "gpt-5-nano",       // vision model for labeling
  "yolo_model": "yolov8n.pt",  // ultralytics base model
  "epochs": 50,                // training epochs per iteration
  "train_split": 0.8           // train/val split (0.8 = 80% train, 20% val)
}
```

## output directory structure

after a full run, `output/` contains:

```
output/
├── video.mp4                   # downloaded youtube video
├── frames/
│   ├── frame_000001.jpg        # extracted frames
│   ├── frame_000001.txt        # YOLO labels (class_id cx cy w h, normalized)
│   └── ...
├── classes.txt                 # class name mapping (line number = class id)
├── augmented/
│   ├── frame_000001_flip.jpg   # horizontally flipped
│   ├── frame_000001_flip.txt
│   ├── frame_000001_bright.jpg # brightness jittered
│   ├── frame_000001_contrast.jpg
│   ├── frame_000001_noise.jpg
│   └── ...
├── dataset/                    # train/val split
│   ├── images/{train,val}/
│   └── labels/{train,val}/
├── dataset.yaml                # ultralytics training config
├── weights/
│   └── best.pt                 # trained YOLO model
└── eval_results.json           # metrics (mAP, precision, recall, per-class)
```

## eval_results.json format

```json
{
  "map50": 0.782,
  "map50_95": 0.651,
  "precision": 0.834,
  "recall": 0.719,
  "target_accuracy": 0.75,
  "meets_target": true,
  "per_class": [
    { "class": "player", "ap50": 0.92 },
    { "class": "weapon", "ap50": 0.71 },
    { "class": "vehicle", "ap50": 0.65 }
  ],
  "weakest_classes": ["vehicle", "weapon"]
}
```

## parallel labeling

when `num_agents > 1`, the label skill uses `dispatch.sh` to:

1. split frames into N batches
2. create N git worktrees at `/tmp/yolodex-workers/agent-{1..N}`
3. copy each batch of frames to its worktree
4. launch N concurrent `codex exec --full-auto -C <worktree>` processes
5. each subagent runs `run_batch.py` on its frames
6. after all finish, copy .txt labels back to main repo
7. run `merge_classes.py` to unify class maps
8. clean up worktrees and branches

to adjust parallelism:

```bash
# 2 agents
bash .agents/skills/label/scripts/dispatch.sh 2

# 8 agents (if you have the API rate limits)
bash .agents/skills/label/scripts/dispatch.sh 8
```

## tips

- **fast iteration**: use `gpt-5-nano` (default) for labeling — cheapest and fastest
- **better accuracy**: switch to `gpt-4.1-mini` or `gpt-4o` in config.json
- **more data**: lower fps to extract more frames (e.g. `"fps": 2` = 2 frames/sec)
- **bigger model**: change `yolo_model` to `yolov8s.pt` or `yolov8m.pt` for better detection
- **longer training**: increase `epochs` beyond 50 for more convergence
- **landing page**: `cd landing && bunx serve .` to view live eval dashboard
