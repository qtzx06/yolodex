#!/usr/bin/env python3
"""Show Yolodex run status from run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from shared.utils import load_config


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _last_history(job_state: dict[str, Any], n: int = 5) -> list[dict[str, Any]]:
    history = job_state.get("history", [])
    if not isinstance(history, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in history[-n:]:
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _count_files(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


def _next_action(config: dict[str, Any], output_dir: Path, eval_results: dict[str, Any] | None) -> dict[str, str]:
    """Return next action based on current pipeline artifacts."""
    video_path = output_dir / "video.mp4"
    frames_dir = output_dir / "frames"
    weights_path = output_dir / "weights" / "best.pt"
    eval_path = output_dir / "eval_results.json"

    frame_count = _count_files(frames_dir, "*.jpg")
    label_count = _count_files(frames_dir, "*.txt")

    label_mode = str(config.get("label_mode", "codex")).strip().lower()
    num_agents = int(config.get("num_agents", 4))

    if not video_path.exists() or frame_count == 0:
        return {
            "phase": "collect",
            "reason": "video or frames missing",
            "command": "uv run .agents/skills/collect/scripts/run.py",
        }

    if label_count == 0:
        if label_mode == "cua+sam":
            cmd = "uv run .agents/skills/label/scripts/label_cua_sam.py"
        elif label_mode == "gemini":
            cmd = "uv run .agents/skills/label/scripts/label_gemini.py"
        elif label_mode in {"gpt", "codex"} and num_agents > 1:
            cmd = f"bash .agents/skills/label/scripts/dispatch.sh {num_agents}"
        else:
            cmd = "uv run .agents/skills/label/scripts/run.py"
        return {
            "phase": "label",
            "reason": "frames present but no labels",
            "command": cmd,
        }

    if not weights_path.exists():
        return {
            "phase": "augment_train",
            "reason": "labels present but model weights missing",
            "command": "uv run .agents/skills/augment/scripts/run.py && uv run .agents/skills/train/scripts/run.py",
        }

    if not eval_path.exists():
        return {
            "phase": "eval",
            "reason": "model exists but eval results missing",
            "command": "uv run .agents/skills/eval/scripts/run.py",
        }

    if eval_results and bool(eval_results.get("meets_target")):
        return {
            "phase": "complete",
            "reason": "target accuracy met",
            "command": "none",
        }

    return {
        "phase": "improve",
        "reason": "eval below target, relabel weak classes and retrain",
        "command": "bash yolodex-run.sh",
    }


def _print_human(
    output_dir: Path,
    manifest: dict[str, Any] | None,
    job_state: dict[str, Any] | None,
    eval_results: dict[str, Any] | None,
    qa_report: dict[str, Any] | None,
    next_action: dict[str, str],
) -> None:
    print("yolodex status")
    print("")
    print(f"output_dir: {output_dir}")

    if manifest:
        print(f"started_at: {manifest.get('started_at', 'unknown')}")
        print(f"updated_at: {manifest.get('updated_at', 'unknown')}")
        print(f"git_commit: {manifest.get('git_commit', 'unknown')}")
    else:
        print("manifest: missing (run_manifest.json)")

    print("")
    if job_state:
        print("job_state:")
        print(f"  phase: {job_state.get('phase', 'unknown')}")
        print(f"  status: {job_state.get('status', 'unknown')}")
        if job_state.get("error"):
            print(f"  error: {job_state.get('error')}")
        recent = _last_history(job_state, n=5)
        if recent:
            print("  recent_history:")
            for row in recent:
                ts = row.get("timestamp", "unknown")
                phase = row.get("phase", "unknown")
                status = row.get("status", "unknown")
                print(f"    - {ts} | {phase} | {status}")
    else:
        print("job_state: missing (job_state.json)")

    print("")
    if eval_results:
        print("eval:")
        print(f"  meets_target: {eval_results.get('meets_target', False)}")
        print(f"  target_accuracy: {eval_results.get('target_accuracy', 'n/a')}")
        print(f"  map50: {eval_results.get('map50', 'n/a')}")
        print(f"  map50_95: {eval_results.get('map50_95', 'n/a')}")
        print(f"  precision: {eval_results.get('precision', 'n/a')}")
        print(f"  recall: {eval_results.get('recall', 'n/a')}")
        weak = eval_results.get("weakest_classes", [])
        if isinstance(weak, list) and weak:
            print(f"  weakest_classes: {', '.join(str(x) for x in weak)}")
    else:
        print("eval: missing (eval_results.json)")

    print("")
    if qa_report:
        print("label_qa:")
        print(f"  files_checked: {qa_report.get('files_checked', 'n/a')}")
        print(f"  files_with_errors: {qa_report.get('files_with_errors', 'n/a')}")
        print(f"  total_errors: {qa_report.get('total_errors', 'n/a')}")
        print(f"  total_warnings: {qa_report.get('total_warnings', 'n/a')}")
    else:
        print("label_qa: missing (label_qa_report.json)")

    print("")
    print("next_action:")
    print(f"  phase: {next_action.get('phase', 'unknown')}")
    print(f"  reason: {next_action.get('reason', 'unknown')}")
    print(f"  command: {next_action.get('command', 'unknown')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Yolodex run status.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable status json",
    )
    args = parser.parse_args()

    config = load_config()
    output_dir = Path(config.get("output_dir", "output"))

    manifest = _safe_read_json(output_dir / "run_manifest.json")
    job_state = _safe_read_json(output_dir / "job_state.json")
    eval_results = _safe_read_json(output_dir / "eval_results.json")
    qa_report = _safe_read_json(output_dir / "label_qa_report.json")
    action = _next_action(config, output_dir, eval_results)

    if args.json:
        payload = {
            "output_dir": str(output_dir),
            "manifest": manifest,
            "job_state": job_state,
            "eval_results": eval_results,
            "label_qa_report": qa_report,
            "next_action": action,
        }
        print(json.dumps(payload, indent=2))
        return 0

    _print_human(output_dir, manifest, job_state, eval_results, qa_report, action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
