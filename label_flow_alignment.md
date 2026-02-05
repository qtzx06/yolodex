# Label Flow Alignment Checklist (Agent B)

## Scope and standards

- MVP class scope is fixed to: `player_jake`, `train`, `barrier`, `coin`, `powerup`.
- Labeling contract source of truth: `/Users/ryunzz/_projects/yolodex/labeler/LABELING_RULES.md`.
- CLI class defaults source: `/Users/ryunzz/_projects/yolodex/labeler/defaults.py`.

## Milestone 1: Touchpoints (spec vs implementation)

1. Frame discovery and selection
- Expectation: deterministic frame set is passed into labeling.
- `label_frames.py`: discovers `*.jpg|*.jpeg|*.png`; supports `start_index`, `step`, `limit` via `discover_frames()` and `pick_frames()`.
- `labeler/` CLI: labels all frames listed in `frames.json` loaded by `load_frames()` and split by `create_tasks()`.
- References:
  - `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` (`discover_frames`, `pick_frames`, `label_frames`)
  - `/Users/ryunzz/_projects/yolodex/labeler/frames.py` (`load_frames`)
  - `/Users/ryunzz/_projects/yolodex/labeler/tasks.py` (`create_tasks`)
- Gap: CLI has no `start/step/limit` equivalent, so sampled runs are not reproducible across both paths.

2. Prompt/rule enforcement
- Expectation: model behavior follows `LABELING_RULES.md` and class constraints.
- `label_frames.py`: prompt includes tight-box/uncertain-skip guidance; optional allowed-class restriction; strict JSON schema response.
- `labeler/` CLI worker: prompt template enforces class list and pixel schema textually, but not JSON-schema constrained API output.
- References:
  - `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` (`build_prompt`, `detect`, `SCHEMA`)
  - `/Users/ryunzz/_projects/yolodex/labeler/defaults.py` (`PROMPT_TEMPLATE`)
  - `/Users/ryunzz/_projects/yolodex/labeler/label_worker.py` (`detect`)
  - `/Users/ryunzz/_projects/yolodex/labeler/LABELING_RULES.md`
- Gap: neither prompt fully encodes edge-case policy from `LABELING_RULES.md` (occlusion threshold, UI/cutscene exclusions, overlap handling).

3. Label output staging and naming
- Expectation: final YOLO labels use frame basename with `.txt`.
- `label_frames.py`: writes YOLO text directly next to each frame (`frame_xxx.txt`).
- `labeler/` CLI: writes intermediate `labels_json/*.jsonl`, then `merge_to_yolo()` writes `dataset/labels/train/<frame_stem>.txt`.
- References:
  - `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` (`label_frames`)
  - `/Users/ryunzz/_projects/yolodex/labeler/label_worker.py` (`run_task`)
  - `/Users/ryunzz/_projects/yolodex/labeler/merge.py` (`merge_to_yolo`)
- Gap: output staging differs (direct YOLO vs JSONL+merge), but basename invariant is compatible.

4. Class map and class-order source
- Expectation: class IDs are stable and match MVP order.
- `label_frames.py`: builds/extends `class_map`; can add unseen classes unless strict class list is enabled.
- `labeler/` CLI: class order comes from `load_classes()`; worker drops unknown classes; merge uses provided class list to map IDs.
- References:
  - `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` (`load_class_map`, `label_frames`)
  - `/Users/ryunzz/_projects/yolodex/labeler/tasks.py` (`load_classes`)
  - `/Users/ryunzz/_projects/yolodex/labeler/label_worker.py` (`detect`, `run_task`)
  - `/Users/ryunzz/_projects/yolodex/labeler/merge.py` (`merge_to_yolo`)
- Gap: `label_frames.py` can drift class set/order without strict mode; CLI path is fixed to provided class list.

5. Box normalization and validation
- Expectation: YOLO coordinates are clamped to `[0,1]` and validate cleanly.
- Both paths: convert from pixel xywh and clamp during YOLO conversion.
- CLI path adds dataset-level validation (`validate_dataset`).
- References:
  - `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` (`to_yolo`, `clamp`)
  - `/Users/ryunzz/_projects/yolodex/labeler/merge.py` (`to_yolo`, `clamp`)
  - `/Users/ryunzz/_projects/yolodex/labeler/validate.py` (`validate_dataset`)
- Gap: `label_frames.py` applies min-size filter `<2 px`; CLI path currently does not apply an equivalent filter before merge.

## Milestone 2: Invariants to preserve (must statements)

1. Class order must remain `player_jake, train, barrier, coin, powerup` for MVP runs.
- Pass: `data.yaml names` and produced IDs follow this exact order.
- Fail: any run introduces new class names or reorders IDs.

2. Bounding boxes must follow `LABELING_RULES.md` global rules and edge-case handling.
- Pass: sampled frames in test clips show tight boxes, no UI/cutscene labels, and skipped uncertain objects.
- Fail: loose boxes, duplicated objects, or labels on non-gameplay overlays.

3. Label filename must match frame basename with `.txt`.
- Pass: `frame_000123.jpg` maps to `frame_000123.txt`.
- Fail: missing labels for existing images or non-basename naming scheme.

4. YOLO lines must be valid `class_id cx cy w h` with coordinates in `[0,1]`.
- Pass: `python -m labeler validate --dataset <dataset_dir>` returns `OK`.
- Fail: validation error for class ID or coordinate range.

5. Unknown classes must not be introduced in MVP flow.
- Pass: all detections outside MVP classes are dropped.
- Fail: `classes.txt` or `data.yaml` contains non-MVP names.

## Milestone 3: Actionable alignment steps (for Agent A)

1. Enforce strict MVP classes in any path that uses `label_frames.py`.
- Action: provide `--class-list` with MVP classes and set `--strict-class-list`.
- Pass cue: output class file contains only 5 MVP classes in fixed order.
- Fail cue: any additional class appears.

2. Align prompt policy with `LABELING_RULES.md` in one shared prompt definition.
- Action: move/compose shared rules text so both `skills/label/label_frames.py` and `labeler/defaults.py` consume the same rule block.
- Pass cue: both paths include identical edge-case directives (UI/cutscene skip, occlusion handling, uncertain-skip).
- Fail cue: rule text differs between the two paths.

3. Add equivalent min-size filtering in CLI path before YOLO merge output.
- Action: apply the same `<2 px` width/height skip rule used in `label_frames.py` when handling worker boxes (worker or merge stage).
- Pass cue: tiny boxes are absent in final YOLO labels in both paths.
- Fail cue: CLI path emits tiny boxes while `label_frames.py` path does not.

4. Keep output naming invariant while allowing different staging.
- Action: if keeping separate implementations, preserve `image stem -> .txt` mapping and validate with `labeler validate`.
- Pass cue: every frame in `dataset/images/train` has same-stem label in `dataset/labels/train`.
- Fail cue: missing or mismatched label basenames.

## Unresolved questions for Agent A decision

1. Should CLI expose frame subsampling controls (`start-index`, `step`, `limit`) to match `label_frames.py` reproducibility behavior, or should `label_frames.py` be constrained to full-frame labeling for parity?
2. Should JSON-schema constrained response mode be adopted in `labeler/label_worker.py` for parity with `label_frames.py`, or is prompt-only JSON strictness acceptable for MVP?
