# skills reference

each skill lives in `.agents/skills/<name>/` with a `SKILL.md` (metadata for codex) and `scripts/` (runnable code).

## yolodex (intake)

**purpose**: conversational entry point. gathers youtube url, classes, and config from the user, then orchestrates the pipeline.

**location**: `.agents/skills/yolodex/SKILL.md`

**invocation**: user-invocable in codex — just ask "train a YOLO model" and it kicks in.

**what it does**:
1. asks for youtube url (required)
2. asks for target classes (required)
3. asks for accuracy threshold (optional, default 0.75)
4. asks for agent count (optional, default 4)
5. writes config.json
6. runs pipeline phases in order

---

## collect

**purpose**: download a youtube video and extract frames.

**location**: `.agents/skills/collect/`

**run**: `uv run .agents/skills/collect/scripts/run.py`

**reads from config**: `video_url`, `fps`, `output_dir`

**outputs**:
- `output/video.mp4`
- `output/frames/frame_000001.jpg`, `frame_000002.jpg`, ...

**dependencies**: yt-dlp, ffmpeg

---

## label

**purpose**: auto-label frames with bounding boxes using a vision LLM.

**location**: `.agents/skills/label/`

### single-agent mode

**run**: `uv run .agents/skills/label/scripts/run.py`

labels all unlabeled frames sequentially. good for small batches or when codex isn't available.

### parallel mode

**run**: `bash .agents/skills/label/scripts/dispatch.sh [num_agents]`

splits frames into batches, creates git worktrees, dispatches concurrent codex subagents. ~Nx faster.
if a user says `call subagent`, map it to this command.
supports:
- `label_mode=gpt` with `OPENAI_API_KEY` (runs `run_batch.py`)
- `label_mode=codex` without API keys (Codex subagents inspect images directly)

### scripts

| script | purpose |
|--------|---------|
| `run.py` | single-agent labeling (all frames) |
| `run_batch.py` | subagent labeling (only frames in its worktree) |
| `dispatch.sh` | orchestrator — splits, dispatches, merges |
| `merge_classes.py` | unifies class maps from all subagents |

**reads from config**: `classes`, `model`, `output_dir`, `num_agents`
`dispatch.sh` also resolves `project -> runs/<project>/` so subagents write to the active run directory.

**outputs**:
- `output/frames/*.txt` (YOLO format labels)
- `output/classes.txt` (class name -> id mapping)

**label format** (YOLO normalized):
```
<class_id> <center_x> <center_y> <width> <height>
```
all values normalized to [0, 1] relative to image dimensions.

**dependencies**: openai (API), ffprobe (image dimensions)

---

## augment

**purpose**: generate synthetic training data from labeled frames.

**location**: `.agents/skills/augment/`

**run**: `uv run .agents/skills/augment/scripts/run.py`

**transforms applied** (per frame, 4 variants):

| transform | image effect | label effect |
|-----------|-------------|-------------|
| horizontal flip | mirror left-right | `new_cx = 1.0 - cx` |
| brightness jitter | random factor 0.7-1.3 | unchanged |
| contrast jitter | random factor 0.7-1.3 | unchanged |
| gaussian noise | intensity=15 | unchanged |

**outputs**: `output/augmented/` with `*_flip.jpg`, `*_bright.jpg`, `*_contrast.jpg`, `*_noise.jpg` and matching `.txt` labels.

result: ~5x training data (original + 4 augmented per frame).

**dependencies**: Pillow, numpy

---

## train

**purpose**: train a YOLO model on the labeled + augmented dataset.

**location**: `.agents/skills/train/`

**run**: `uv run .agents/skills/train/scripts/run.py`

**what it does**:
1. collects all image/label pairs from `output/frames/` and `output/augmented/`
2. splits into train/val per `train_split` ratio
3. copies to `output/dataset/images/{train,val}/` and `output/dataset/labels/{train,val}/`
4. generates `output/dataset.yaml` with class names and paths
5. runs `ultralytics.YOLO(yolo_model).train(data=dataset.yaml, epochs=N)`
6. copies best weights to `output/weights/best.pt`

**reads from config**: `yolo_model`, `epochs`, `train_split`, `output_dir`

**outputs**:
- `output/dataset/` (organized train/val split)
- `output/dataset.yaml`
- `output/weights/best.pt`

**dependencies**: ultralytics

---

## eval

**purpose**: evaluate trained model and produce metrics for the loop decision.

**location**: `.agents/skills/eval/`

**run**: `uv run .agents/skills/eval/scripts/run.py`

**what it does**:
1. loads `output/weights/best.pt`
2. runs `model.val(data=output/dataset.yaml)`
3. extracts mAP@50, mAP@50-95, precision, recall
4. computes per-class AP50
5. identifies weakest classes (sorted by AP ascending)
6. writes `output/eval_results.json`

**reads from config**: `output_dir`, `target_accuracy`

**outputs**: `output/eval_results.json`

**dependencies**: ultralytics
