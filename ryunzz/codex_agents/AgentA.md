# Agent A (Pipeline Integrator)

## Design Decisions
- Consolidated the YOLO labeling pipeline under `labeler/` so there is a single CLI entrypoint (`run-mvp`).
- Introduced shared `label_frames.py` + `rules.py` to keep schema enforcement, class filtering, and prompt structure reusable between `label_worker` and the CLI.
- Defaulted to `1 FPS`, `gpt-5`, and local-only execution with clear TAS/manual guidance.
- `validate_dataset(dataset_dir, rules_path=None)` now resolves rules to `labeler/LABELING_RULES.md` when omitted; CLI exposes `--rules` and returns clean `Error: ...` messages with exit code `1` (no traceback) on validation failures.

## Assumptions
- Labeling must stay local-first: no cloud dependencies, no GPUs, no YOLO pre-pass.
- OpenAI API access is managed externally via `OPENAI_API_KEY`.
- Frame extraction uses deterministic directories per `runs/<timestamp>`.

## Interaction Notes
- Agent A expects Agent B to keep `label_flow_alignment.md` updated with invariants (frame sampling, class order, tiny-box filters).
- Agent C should document how to invoke the new CLI flow and validation commands (including `--rules`).
- Validation guards that come from `LABELING_RULES.md` feed into both CLI and documentation.

## Deliverables
- `labeler/run-mvp`, `label_worker`, `label_frames`, `rules`, and `validate` with CLI help/exit handling.
- `SKILL.md` and `docs/testing-instructions.md` updates describing TAS/manual usage and explicit `validate --rules` behavior.
- Smoke-check logs verifying `run-mvp`, `validate`, and CLI help commands.

## Next Handoff
- Confirm Agent B’s checklist no longer lists gaps.
- Wait for Agent C to finalize testing steps; run `run-mvp` + `validate` once tooling is ready.

## Verification Snapshot
- Re-ran CLI smoke checks: `python3 -m labeler --help`, `python3 -m labeler run-mvp --help`, `python3 -m labeler label-worker --help`, `python3 -m labeler merge --help`, `python3 -m labeler validate --help`.
- Re-ran failure path: `python3 -m labeler validate --dataset /tmp/nonexistent_dataset --rules labeler/LABELING_RULES.md` -> prints `Error: ...` and exits `1`.
- Verified default rules behavior on a local fixture:
  - `merge` (without `--classes`) emitted `data.yaml` names in `LABELING_RULES.md` order.
  - `validate` succeeds both with explicit `--rules` and when omitted (defaulting to `labeler/LABELING_RULES.md`).

## Additional Assumption
- `merge` class/order enforcement comes from rules only when `--classes` is omitted. If `--classes` is provided, that file becomes the class source of truth for `data.yaml`.
