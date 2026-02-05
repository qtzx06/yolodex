# Agent C (Test Coach)

## Design Decisions
- Created `docs/testing-instructions.md` with single-command and TAS flows, `validate` expectations, pytest baseline, and a checklist that maps to the run-mvp pipeline.
- Emphasized local tooling dependencies (`yt-dlp`, `ffmpeg`, `ffprobe`, `OPENAI_API_KEY`) while keeping tests runnable without GPU or cloud access.
- Updated the testing doc to use the final `validate --dataset ... --rules ...` syntax and document the default rules file.
- Added an explicit gotcha noting there are no packaged videos in the repo.

## Assumptions
- Agents have access to the same repository and can run Python CLI commands in parallel (one per task for TAS).
- No sample videos are checked in; testers need to supply their own or rely on YouTube URLs.
- The CLI commands (`run-mvp`, `label-worker`, `merge`, `validate`) are stable once Agent A finalizes their wiring.

## Interaction Notes
- Agent A provides the final command syntax; Agent C uses it verbatim in the docs to keep instructions accurate.
- Agent B’s invariants inform what the validation command must check, so document the checks accordingly.

## Deliverables
- `docs/testing-instructions.md` detailing prerequisites, manual/TAS flows, validation behavior, pytest command, and a checklist.
- Validation section now includes `--rules`, success/failure outputs, and default rule file behavior.

## Next Handoff
- Keep command snippets aligned with any future CLI help changes.
