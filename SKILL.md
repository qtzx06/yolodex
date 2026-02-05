---
name: yolodex
description: Build YOLO datasets from YouTube videos by extracting frames, labeling with Codex TAS agents, and exporting train-ready datasets. Use this when users want rapid object-detection dataset generation or parallel labeling workflows.
---

# Yolodex Skill

This repo runs a local YOLO dataset generation flow from gameplay videos.

## Workflow

1. Ingest video from a YouTube URL.
2. Extract frames into `dataset/images/train`.
3. Create parallel labeling tasks for Codex agents.
4. Merge JSON outputs into YOLO labels + `data.yaml`.
5. Validate the dataset.

## Entry Points

- CLI: `python -m labeler`

## Quickstart (MVP)

1. Single entrypoint (default TAS/manual mode):
   - `python3 -m labeler run-mvp --youtube <url> --run-dir runs/demo --fps 1 --agents 4`
   - This creates `label_tasks/` and waits for parallel agent execution.
2. Run each task in parallel (one per Codex agent/worktree):
   - `python3 -m labeler label-worker --run-dir runs/demo --task runs/demo/label_tasks/task_000.json`
3. Merge and validate:
   - `python3 -m labeler merge --run-dir runs/demo`
   - `python3 -m labeler validate --dataset runs/demo/dataset`
4. Optional one-command local execution (no TAS fan-out):
   - `python3 -m labeler run-mvp --youtube <url> --run-dir runs/demo --local-workers`

## Validation

- Validation reads class order from `labeler/LABELING_RULES.md` and enforces:
  - dataset layout: `dataset/images/train`, `dataset/labels/train`, `data.yaml`
  - one label file per image
  - class list/order in `data.yaml` matches `LABELING_RULES.md`
  - YOLO line shape and normalized coord range [0,1]

## Requirements

- Python 3.11+
- `ffmpeg`, `ffprobe`, `yt-dlp` on PATH
- `OPENAI_API_KEY` set
