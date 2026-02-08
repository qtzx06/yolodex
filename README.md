# yolodex

codex-native yolo dataset + training pipeline for gameplay videos.
main flow is skill-driven orchestration through codex, not ad-hoc scripts.

[![star history chart](https://api.star-history.com/svg?repos=qtzx06/yolodex&type=Date)](https://star-history.com/#qtzx06/yolodex&Date)

```
YouTube URL + classes
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

## codex-first setup

```bash
git clone <repo-url> && cd yolodex
bash setup.sh
```

the setup script installs ffmpeg, yt-dlp, uv, and python deps (ultralytics/torch/pillow).

**requirements:**
- macOS or Linux
- Python 3.11+
- [Codex CLI](https://github.com/openai/codex)

## codex integration

enable codex collaboration features once:

```bash
codex features enable collab
codex features enable child_agents_md
codex features enable steer
codex features list | rg 'collab|child_agents_md|steer'
```

then start codex in this repo. `call subagent` for labeling maps to:

```bash
bash .agents/skills/label/scripts/dispatch.sh 4
```

if your session does not expose subagents, run that command directly.
set `"label_mode": "codex"` for codex-native labeling.

## quick start (recommended)

### 1) configure

```bash
# Edit config.json
{
  "video_url": "https://youtube.com/watch?v=YOUR_VIDEO",
  "classes": ["player", "weapon", "vehicle"],
  "label_mode": "codex",
  "target_accuracy": 0.75
}
```

### 2) run through codex

interactive codex flow:
```text
$ codex
> use the yolodex skill to train from this video: https://youtube.com/...
> classes: player, weapon, vehicle
> label_mode: codex
> call subagent label frames with 4 agents
```

autonomous loop flow:
```bash
bash yolodex.sh
```
runs codex full-auto iterations until target is met or max iterations is hit.

manual fallback (same skills, explicit commands):
```bash
uv run .agents/skills/collect/scripts/run.py       # download + extract frames
bash .agents/skills/label/scripts/dispatch.sh 4    # label, merge, and auto-generate previews + video
uv run .agents/skills/augment/scripts/run.py        # augment training data
uv run .agents/skills/train/scripts/run.py          # train YOLO model
uv run .agents/skills/eval/scripts/run.py           # evaluate model
```

### 3) outputs

```bash
cat runs/<project>/eval_results.json    # mAP, precision, recall, per-class breakdown
```
After labeling you can inspect `runs/<project>/frames/preview/` (PNG overlays)
and `runs/<project>/frames/preview/preview.mp4` for a quick annotated walkthrough.

## how it works

### skills architecture (source of truth)

Each pipeline stage is a standalone [Codex skill](https://developers.openai.com/codex/skills/) in `.agents/skills/`:

| Skill | What it does | Entry point |
|-------|-------------|-------------|
| **collect** | Download YouTube video, extract frames at configurable FPS | `scripts/run.py` |
| **label** | Auto-label frames with bounding boxes using vision LLM | `scripts/run.py` (single) or `scripts/dispatch.sh` (parallel) |
| **augment** | Generate synthetic training data (flip, brightness, contrast, noise) | `scripts/run.py` |
| **train** | Split dataset, generate YAML, train YOLO with ultralytics | `scripts/run.py` |
| **eval** | Evaluate model, compute mAP@50, identify weakest classes | `scripts/run.py` |

### parallel labeling

The label skill can dispatch N concurrent Codex subagents, each in its own git worktree:

1. Frames split into N batches
2. Each batch gets a git worktree under `/tmp/yolodex-workers/run-*/agent-N/`
3. `codex exec --full-auto -C <worktree>` labels each batch concurrently
4. Results merge back, class maps unified

```bash
# 4 parallel agents (default)
bash .agents/skills/label/scripts/dispatch.sh 4

# 8 agents if you have the API rate limits
bash .agents/skills/label/scripts/dispatch.sh 8
```

### codex iteration loop

`yolodex.sh` implements an autonomous iteration loop:

1. Each iteration calls `codex exec --full-auto` which reads `AGENTS.md`
2. Codex checks what exists (video? frames? labels? model? eval?) and runs the next phase
3. After eval, loop exits when target is met (from `<promise>COMPLETE</promise>` or `eval_results.json`)
4. If below target, loops back to re-label failures and retrain
5. Cross-iteration memory stored in `progress.txt`

## models

### yolo (for training)

| Model | Params | Speed | Recommended for |
|-------|--------|-------|-----------------|
| **yolov8n.pt** (default) | 3.2M | Fastest | Quick iteration, small datasets |
| yolov8s.pt | 11.2M | Fast | Production, medium datasets |
| yolov8m.pt | 25.9M | Medium | Large datasets, GPU available |

change in `config.json`:
```json
{"yolo_model": "yolov8s.pt"}
```

## Config Reference

| Field | Default | Description |
|-------|---------|-------------|
| `video_url` | `""` | YouTube URL to process |
| `classes` | `[]` | Target object classes (empty = auto-detect all) |
| `target_accuracy` | `0.75` | mAP@50 threshold to stop iterating |
| `max_iterations` | `10` | Safety cap on autonomous loop |
| `num_agents` | `4` | Parallel labeling subagents |
| `fps` | `1` | Frame extraction rate (frames/second) |
| `label_mode` | `"codex"` | Labeler mode: `cua+sam`, `gemini`, `gpt`, or `codex` |
| `yolo_model` | `"yolov8n.pt"` | YOLO base model for training |
| `epochs` | `50` | Training epochs per iteration |
| `train_split` | `0.8` | Train/val split ratio |

## Project Structure

```
yolodex/
├── .agents/skills/         # Codex skills (each has SKILL.md + scripts/)
│   ├── yolodex/            # Intake skill (interactive config gathering)
│   ├── collect/            # Download video, extract frames
│   ├── label/              # Vision labeling (single + parallel modes)
│   ├── augment/            # Synthetic data augmentation
│   ├── train/              # YOLO training with ultralytics
│   └── eval/               # mAP metrics + failure analysis
├── shared/utils.py         # Shared Python utils (BoundingBox, helpers)
├── pipeline/main.py        # Original monolith (preserved as reference)
├── docs/                   # Detailed documentation
├── yolodex.sh              # Ralph-style autonomous loop
├── setup.sh                # Install script
├── AGENTS.md               # Codex iteration logic (auto-read)
├── config.json             # Pipeline configuration
├── progress.txt            # Cross-iteration memory
└── pyproject.toml          # Python project (uv)
```

Generated datasets, previews, model weights, and exports are intentionally kept out of git.
Run artifacts live under `runs/` (or `output/`) locally and should be shared via release assets
or external storage when needed.

## Docs

- [docs/usage.md](docs/usage.md) — Detailed usage guide
- [docs/models.md](docs/models.md) — Model comparison and pricing
- [docs/skills.md](docs/skills.md) — Skill reference
- [docs/architecture.md](docs/architecture.md) — System design
- [docs/changelog.md](docs/changelog.md) — Rewrite history

## License

MIT
