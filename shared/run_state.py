"""Run-state helpers for codex-native pipeline observability."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass
    return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolve_output_dir(config: dict[str, Any]) -> Path:
    return Path(config.get("output_dir", "output"))


def _git_head() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def init_run_manifest(config: dict[str, Any]) -> None:
    """Create or refresh run manifest for this output directory."""
    output_dir = _resolve_output_dir(config)
    manifest_path = output_dir / "run_manifest.json"
    manifest = _safe_read_json(manifest_path)

    if "started_at" not in manifest:
        manifest["started_at"] = _now_iso()
    manifest["updated_at"] = _now_iso()
    manifest["git_commit"] = _git_head()
    manifest["config"] = config

    _write_json(manifest_path, manifest)


def mark_phase_running(config: dict[str, Any], phase: str) -> None:
    output_dir = _resolve_output_dir(config)
    state_path = output_dir / "job_state.json"
    state = _safe_read_json(state_path)

    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "phase": phase,
            "status": "running",
            "timestamp": _now_iso(),
        }
    )

    state.update(
        {
            "phase": phase,
            "status": "running",
            "updated_at": _now_iso(),
            "history": history,
        }
    )
    _write_json(state_path, state)


def mark_phase_done(config: dict[str, Any], phase: str, details: dict[str, Any] | None = None) -> None:
    output_dir = _resolve_output_dir(config)
    state_path = output_dir / "job_state.json"
    state = _safe_read_json(state_path)

    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "phase": phase,
            "status": "completed",
            "timestamp": _now_iso(),
            "details": details or {},
        }
    )

    state.update(
        {
            "phase": phase,
            "status": "completed",
            "updated_at": _now_iso(),
            "last_successful_phase": phase,
            "details": details or {},
            "history": history,
        }
    )
    _write_json(state_path, state)


def mark_phase_failed(config: dict[str, Any], phase: str, error: str) -> None:
    output_dir = _resolve_output_dir(config)
    state_path = output_dir / "job_state.json"
    state = _safe_read_json(state_path)

    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "phase": phase,
            "status": "failed",
            "timestamp": _now_iso(),
            "error": error,
        }
    )

    state.update(
        {
            "phase": phase,
            "status": "failed",
            "updated_at": _now_iso(),
            "error": error,
            "history": history,
        }
    )
    _write_json(state_path, state)

