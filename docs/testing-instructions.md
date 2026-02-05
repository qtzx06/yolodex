# Yolodex Testing Instructions

This document describes how to exercise the MVP pipeline end-to-end and how to run any automated tests currently in the repo.

## Prerequisites

- Python 3.11+
- Install Python deps: `pip install -r requirements.txt`
- System tools on PATH (used by the CLI): `yt-dlp`, `ffmpeg`, `ffprobe`
- `OPENAI_API_KEY` set in your environment for labeling steps
- No GPU is required by any script in this repo

## Sample Inputs

- Sample YouTube URL (from `config.json`): `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Local clip fallback: there are no video files checked into the repo. If you have a local clip, use the manual flow and pass `--video /path/to/clip.mp4` to `extract-frames`.
- Default rules file (used when `--rules` is omitted): `labeler/LABELING_RULES.md`

## MVP End-to-End (Primary CLI: `run-mvp`)

The main CLI entry point is `python3 -m labeler`. The MVP helper command is `run-mvp`.

### Option A: Full local run (single command)

This runs ingest -> extract -> label (local workers) -> merge -> validate.

```bash
python3 -m labeler run-mvp \
  --youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ \
  --run-dir runs/demo \
  --fps 1 \
  --agents 4 \
  --rules labeler/LABELING_RULES.md \
  --local-workers
```

What to expect:

- The downloaded video lands in `runs/demo/raw/video.mp4`.
- Extracted frames are saved under `runs/demo/dataset/images/train/`.
- Labels JSONL output is written to `runs/demo/labels_json/`.
- YOLO output is written to `runs/demo/dataset/` (including `labels/train/` and `data.yaml`).
- On success, the command prints the dataset path.

### Option B: TAS manual mode (parallel agents)

This runs ingest -> extract -> create labeling tasks, then stops so you can run each task in parallel with Codex TAS agents.

```bash
python3 -m labeler run-mvp \
  --youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ \
  --run-dir runs/demo \
  --fps 1 \
  --agents 4 \
  --rules labeler/LABELING_RULES.md
```

Then run each task (one per agent/worktree):

```bash
python3 -m labeler label-worker --run-dir runs/demo --task runs/demo/label_tasks/task_000.json
python3 -m labeler label-worker --run-dir runs/demo --task runs/demo/label_tasks/task_001.json
python3 -m labeler label-worker --run-dir runs/demo --task runs/demo/label_tasks/task_002.json
python3 -m labeler label-worker --run-dir runs/demo --task runs/demo/label_tasks/task_003.json
```

Finally merge and validate:

```bash
python3 -m labeler merge --run-dir runs/demo
python3 -m labeler validate --dataset runs/demo/dataset --rules labeler/LABELING_RULES.md
```

## Manual Flow (Local Clip)

`run-mvp` only accepts a YouTube URL. For a local clip, use the explicit commands:

```bash
mkdir -p runs/local_demo
python3 -m labeler extract-frames --run-dir runs/local_demo --video /path/to/clip.mp4 --fps 1
python3 -m labeler label --run-dir runs/local_demo --agents 4 --rules labeler/LABELING_RULES.md
```

Then run each task with `label-worker`, merge, and validate as shown above.

## Validate Command and Output

Command:

```bash
python3 -m labeler validate --dataset runs/demo/dataset --rules labeler/LABELING_RULES.md
```

What it checks (from `labeler/validate.py`):

- `images/train` and `labels/train` directories exist
- `data.yaml` exists and includes a `names:` list
- Class order in `data.yaml` matches the class list derived from `--rules` (default `labeler/LABELING_RULES.md`)
- Image and label counts match
- No missing or extra label files
- Each YOLO line has exactly 5 fields
- Class IDs are in range
- Box coordinates are in the range [0, 1]

Expected output:

- Success: prints `OK` and exits 0.
- Failure: raises a `ValidationError` (CLI prints `Error: <reason>` and exits 1).
- If `--rules` is omitted, CLI defaults to `labeler/LABELING_RULES.md`.

## Automated Tests (pytest)

Inventory:

- The `tests/` directory is empty in this repo.

Default command:

```bash
pytest
```

Expected result:

- `pytest` should run with 0 collected tests unless you add tests later.

## Checklist: End-to-End MVP Verification

- [ ] Install Python deps: `pip install -r requirements.txt`
- [ ] Confirm `yt-dlp`, `ffmpeg`, and `ffprobe` are on PATH
- [ ] Export `OPENAI_API_KEY`
- [ ] Run `python3 -m labeler run-mvp --youtube <url> --run-dir runs/demo --fps 1 --agents 4 --rules labeler/LABELING_RULES.md --local-workers`
- [ ] Confirm `runs/demo/dataset/` exists and contains `images/train`, `labels/train`, and `data.yaml`
- [ ] Run `python3 -m labeler validate --dataset runs/demo/dataset --rules labeler/LABELING_RULES.md`

## Notes on Flaky Steps

- Labeling uses the OpenAI API via `labeler/label_worker.py`; results can vary by model response and network conditions.
- There are no packaged videos in the repo; testers must supply a YouTube URL or a local clip.
