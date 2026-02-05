# Label Flow Alignment Checklist (Agent B Refresh)

## Scope and Standards

- MVP classes only: `player_jake`, `train`, `barrier`, `coin`, `powerup`.
- Labeling contract source: `/Users/ryunzz/_projects/yolodex/labeler/LABELING_RULES.md`.
- Shared rules/class helpers: `/Users/ryunzz/_projects/yolodex/labeler/rules.py`.
- Shared detection path used by CLI workers: `/Users/ryunzz/_projects/yolodex/labeler/label_frames.py`.
- Last verified against current code: `2026-02-05`.

## Milestone 1: Touchpoints (inputs, outputs, invariants)

1. Frame sampling / frame set
- Expectation: label path consumes one deterministic frame list.
- Current behavior:
- `labeler` CLI labels frames from `frames.json` only (`load_frames` -> `create_tasks` -> `run_task`).
- No alternate sampler in the active `labeler` flow; sampling is controlled upstream by `extract-frames --fps`.
- References:
- `/Users/ryunzz/_projects/yolodex/labeler/cli.py` (`cmd_label`, `cmd_run_mvp`)
- `/Users/ryunzz/_projects/yolodex/labeler/frames.py` (`load_frames`, `extract_frames`)
- `/Users/ryunzz/_projects/yolodex/labeler/tasks.py` (`create_tasks`)
- Status: `RESOLVED` for current CLI path.
- Remaining risk: legacy `/Users/ryunzz/_projects/yolodex/skills/label/label_frames.py` still has `start/step/limit` and can diverge if used outside CLI.

2. Prompt/rule consistency
- Expectation: worker prompt behavior is sourced from shared rules-aware code.
- Current behavior:
- `label_worker.run_task` calls shared `detect` in `labeler/label_frames.py`.
- `detect` uses strict JSON schema responses and applies class filtering + tiny-box filter.
- Prompt includes global rules excerpt from `LABELING_RULES.md` via `labeling_rules_excerpt`.
- References:
- `/Users/ryunzz/_projects/yolodex/labeler/label_worker.py` (`run_task`)
- `/Users/ryunzz/_projects/yolodex/labeler/label_frames.py` (`build_prompt`, `detect`, `SCHEMA`)
- `/Users/ryunzz/_projects/yolodex/labeler/rules.py` (`labeling_rules_excerpt`)
- Status: `PARTIAL`.
- Remaining risk: only "Global Rules" section is injected; class-specific and "Edge Cases" sections are not directly injected into prompt text.

3. Class filtering / class order
- Expectation: class order and allowed classes remain stable and MVP-scoped.
- Current behavior:
- Default classes now load from `LABELING_RULES.md` (`extract_rule_classes`) when no classes file is provided.
- Worker drops any detection not in task classes.
- Validation enforces `data.yaml` class order equals classes extracted from rules.
- References:
- `/Users/ryunzz/_projects/yolodex/labeler/tasks.py` (`load_classes`)
- `/Users/ryunzz/_projects/yolodex/labeler/label_frames.py` (`detect`)
- `/Users/ryunzz/_projects/yolodex/labeler/validate.py` (`validate_dataset`)
- Status: `RESOLVED` for default-rules runs.
- Remaining risk: `merge` does not accept `--rules`; non-default rules require explicit `--classes` on merge to avoid drift from default rules path.

4. Tiny-box handling
- Expectation: `<2 px` objects are filtered consistently.
- Current behavior:
- Tiny-box filter is in shared `detect`, so worker JSONL and final YOLO output both inherit it.
- References:
- `/Users/ryunzz/_projects/yolodex/labeler/label_frames.py` (`detect`)
- `/Users/ryunzz/_projects/yolodex/labeler/label_worker.py` (`run_task`)
- `/Users/ryunzz/_projects/yolodex/labeler/merge.py` (`merge_to_yolo`)
- Status: `RESOLVED`.

5. Output naming and rules-aware validation
- Expectation: labels match image basenames and validate against rules.
- Current behavior:
- Merge writes `dataset/labels/train/<image_stem>.txt`.
- Validation checks:
- image/label directory presence
- class order equality with rules-derived classes
- image/label count and stem parity
- YOLO numeric format and coordinate range
- References:
- `/Users/ryunzz/_projects/yolodex/labeler/merge.py` (`merge_to_yolo`)
- `/Users/ryunzz/_projects/yolodex/labeler/validate.py` (`validate_dataset`)
- `/Users/ryunzz/_projects/yolodex/labeler/cli.py` (`cmd_validate`)
- Status: `RESOLVED` (structural checks); semantic box quality still depends on prompt/model behavior.

## Milestone 2: Invariants to Preserve (must statements)

1. Class order must remain `player_jake, train, barrier, coin, powerup` for MVP.
- State: `RESOLVED` in validation for default rules path.
- Pass: `python3 -m labeler validate --dataset <run_dir>/dataset --rules <rules_path>` prints `OK`.
- Fail: class order mismatch error in validation.

2. Unknown classes must never enter final YOLO labels.
- State: `RESOLVED`.
- Pass: every `class_id` maps to the 5 MVP classes only.
- Fail: non-MVP names appear in `data.yaml` or class-id overflow appears in labels.

3. Tiny detections (`width < 2` or `height < 2`) must be dropped before merge.
- State: `RESOLVED`.
- Pass: no sub-2px boxes in JSONL outputs from workers.
- Fail: any sub-2px box survives worker output.

4. Label file naming must match image basename and be complete.
- State: `RESOLVED`.
- Pass: stem parity and count parity checks pass in validation.
- Fail: missing or extra label stems.

5. Prompt must remain rules-aware and class-constrained.
- State: `PARTIAL`.
- Pass: prompt includes class whitelist + rules excerpt and model returns schema-valid JSON.
- Fail: prompt path bypasses `rules.py` or accepts out-of-class detections.

## Milestone 3: Actionable Alignment Items (Agent A)

1. Verify CLI `--rules` behavior end-to-end, including non-default rules paths.
- Action: run `label` and `validate` with a non-default rules file; confirm workers receive that rules path from task JSON.
- Pass cue: task files include `rules_path`, and validation passes with same `--rules` path.
- Fail cue: task JSON uses empty/default `rules_path`, or validation only passes with default rules file.

2. Close `merge`/`--rules` propagation gap.
- Action: decide one of:
- add `--rules` to `merge`, or
- require `--classes` on `merge` whenever non-default rules are used.
- Pass cue: merge class mapping is guaranteed to match the same rules used during label/validate.
- Fail cue: merge silently pulls classes from default rules while label/validate used another rules file.

3. Decide contract level for prompt coverage of `LABELING_RULES.md`.
- Action: either keep current global-rules-only excerpt as accepted MVP behavior, or expand prompt injection to include edge-case directives.
- Pass cue: documented and intentional policy with tests/checks aligned to that policy.
- Fail cue: implicit expectation that edge-case section is enforced when code does not inject it.

## Brief Unresolved Questions

1. Is the old `/skills/label/label_frames.py` intentionally out of MVP CLI scope, or should it be explicitly deprecated to prevent accidental divergent runs?
2. For custom rule files, should class extraction in `merge` and class validation always use the same `--rules` argument to eliminate config drift by construction?
