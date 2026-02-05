# Yolodex

Autonomous YOLO training data generation from gameplay videos. Give it a YouTube URL and target classes — it downloads the video, extracts frames, labels them with a vision LLM, augments the data, trains a YOLO model, evaluates it, and loops until it hits your target accuracy.

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

## Setup

```bash
git clone <repo-url> && cd yolodex
bash setup.sh
```

The setup script installs everything: ffmpeg, yt-dlp, uv, Python deps (ultralytics, openai, torch, Pillow). It checks your environment and tells you what's missing.

**Requirements:**
- macOS or Linux
- Python 3.11+
- `OPENAI_API_KEY` environment variable
- Optional: [Codex CLI](https://github.com/openai/codex) for parallel labeling + autonomous loop

## Enable Subagents (Codex)

If you want to use `call subagent` workflows in this repo, enable Codex collaboration features once:

```bash
codex features enable collab
codex features enable child_agents_md
codex features enable steer
codex features list | rg 'collab|child_agents_md|steer'
```

Then start a new Codex session in this repo. In Yolodex, `call subagent` for labeling maps to the same orchestrator used by scripts:

```bash
bash .agents/skills/label/scripts/dispatch.sh 4
```

If your session does not expose subagents, use the command above directly.
For no-key labeling, set `"label_mode": "codex"` in `config.json` and run the same command.

## Quick Start

### 1. Configure

```bash
# Edit config.json
{
  "video_url": "https://youtube.com/watch?v=YOUR_VIDEO",
  "classes": ["player", "weapon", "vehicle"],
  "label_mode": "codex",
  "target_accuracy": 0.75,
  "model": "gpt-5-nano"
}
```

### 2. Run

**Autonomous (recommended):**
```bash
bash yolodex.sh
```
Runs the full pipeline in a loop until target accuracy is reached.

**Manual (skill by skill):**
```bash
uv run .agents/skills/collect/scripts/run.py       # download + extract frames
bash .agents/skills/label/scripts/dispatch.sh 4    # label, merge, and auto-generate previews + video
uv run .agents/skills/augment/scripts/run.py        # augment training data
uv run .agents/skills/train/scripts/run.py          # train YOLO model
uv run .agents/skills/eval/scripts/run.py           # evaluate model
```

**With Codex (interactive):**
```
$ codex
> Train a YOLO model to detect players and weapons from this Fortnite video: https://youtube.com/...
> call subagent label frames with 4 agents
```
Codex reads AGENTS.md, asks for config, runs everything.

### 3. Results

```bash
cat output/eval_results.json    # mAP, precision, recall, per-class breakdown
cd landing && bunx serve .      # web dashboard
```
After labeling you can inspect `runs/<project>/frames/preview/` (PNG overlays)
and `runs/<project>/frames/preview/preview.mp4` for a quick annotated walkthrough.

## How It Works

### Skills Architecture

Each pipeline stage is a standalone [Codex skill](https://developers.openai.com/codex/skills/) in `.agents/skills/`:

| Skill | What it does | Entry point |
|-------|-------------|-------------|
| **collect** | Download YouTube video, extract frames at configurable FPS | `scripts/run.py` |
| **label** | Auto-label frames with bounding boxes using vision LLM | `scripts/run.py` (single) or `scripts/dispatch.sh` (parallel) |
| **augment** | Generate synthetic training data (flip, brightness, contrast, noise) | `scripts/run.py` |
| **train** | Split dataset, generate YAML, train YOLO with ultralytics | `scripts/run.py` |
| **eval** | Evaluate model, compute mAP@50, identify weakest classes | `scripts/run.py` |

### Parallel Labeling

The label skill can dispatch N concurrent Codex subagents, each in its own git worktree:

1. Frames split into N batches
2. Each batch gets a git worktree at `/tmp/yolodex-workers/agent-N/`
3. `codex exec --full-auto -C <worktree>` labels each batch concurrently
4. Results merge back, class maps unified

```bash
# 4 parallel agents (default)
bash .agents/skills/label/scripts/dispatch.sh 4

# 8 agents if you have the API rate limits
bash .agents/skills/label/scripts/dispatch.sh 8
```

### Ralph Loop

`yolodex.sh` implements an autonomous iteration loop:

1. Each iteration calls `codex exec --full-auto` which reads `AGENTS.md`
2. Codex checks what exists (video? frames? labels? model? eval?) and runs the next phase
3. After eval, if accuracy >= target, emits `<promise>COMPLETE</promise>` and exits
4. If below target, loops back to re-label failures and retrain
5. Cross-iteration memory stored in `progress.txt`

## Models

### Vision (for labeling)

| Model | Cost | Speed | Recommended for |
|-------|------|-------|-----------------|
| **gpt-5-nano** (default) | $$ | Fastest | High-volume labeling |
| gpt-4.1-mini | $$ | Fast | Best accuracy/cost balance |
| gpt-4o | $$$$ | Medium | Maximum accuracy |

### YOLO (for training)

| Model | Params | Speed | Recommended for |
|-------|--------|-------|-----------------|
| **yolov8n.pt** (default) | 3.2M | Fastest | Quick iteration, small datasets |
| yolov8s.pt | 11.2M | Fast | Production, medium datasets |
| yolov8m.pt | 25.9M | Medium | Large datasets, GPU available |

Change in `config.json`:
```json
{"model": "gpt-4.1-mini", "yolo_model": "yolov8s.pt"}
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
| `label_mode` | `"gpt"` | Labeler mode: `cua+sam`, `gemini`, `gpt`, or `codex` (no API keys) |
| `model` | `"gpt-5-nano"` | Vision model for labeling |
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
├── landing/                # Web dashboard (HTML/CSS)
├── docs/                   # Detailed documentation
├── yolodex.sh              # Ralph-style autonomous loop
├── setup.sh                # Install script
├── AGENTS.md               # Codex iteration logic (auto-read)
├── config.json             # Pipeline configuration
├── progress.txt            # Cross-iteration memory
└── pyproject.toml          # Python project (uv)
```

## Sanitized exports

`team_exports/` holds ready-to-share datasets for completed projects.
Each export includes `dataset/images`, `dataset/labels`, `classes.txt`, overlay previews,
and a minimal `manifest.json` so downstream teams can consume clean YOLO data without
touching the full `runs/` tree.

## Docs

- [docs/usage.md](docs/usage.md) — Detailed usage guide
- [docs/models.md](docs/models.md) — Model comparison and pricing
- [docs/skills.md](docs/skills.md) — Skill reference
- [docs/architecture.md](docs/architecture.md) — System design
- [docs/changelog.md](docs/changelog.md) — Rewrite history

## License

MIT
