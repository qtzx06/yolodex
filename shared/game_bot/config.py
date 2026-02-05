"""Configuration loading for the deterministic gameplay bot."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared.utils import load_config


@dataclass(frozen=True)
class CaptureConfig:
    monitor_index: int
    left: int | None
    top: int | None
    width: int | None
    height: int | None


@dataclass(frozen=True)
class ThresholdConfig:
    confidence: float
    threat_persistence_frames: int
    side_switch_cooldown_s: float
    max_evade_duration_s: float
    stabilize_duration_s: float


@dataclass(frozen=True)
class HotkeyConfig:
    toggle_active: str
    emergency_kill: str


@dataclass(frozen=True)
class BotConfig:
    game: str
    available_games: list[str]
    model_path: Path
    threat_classes: list[str]
    capture: CaptureConfig
    thresholds: ThresholdConfig
    hotkeys: HotkeyConfig
    loop_hz: float
    log_hz: float
    imgsz: int
    dry_run: bool


def _default_threat_classes(classes: list[str]) -> list[str]:
    lowered = [name.lower() for name in classes]
    picked = [name for name in lowered if any(tok in name for tok in ("laser", "projectile", "bullet", "beam"))]
    return picked


def _required_int(value: Any, key: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    raise ValueError(f"bot.capture.{key} must be an integer")


def _resolve_model_path(config: dict[str, Any], bot_cfg: dict[str, Any]) -> Path:
    override = bot_cfg.get("model_path")
    if override:
        return Path(str(override)).expanduser()
    output_dir = Path(str(config.get("output_dir", "output")))
    return output_dir / "weights" / "best.pt"


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), Mapping):
            merged[key] = _deep_merge(dict(base[key]), dict(value))
        else:
            merged[key] = value
    return merged


def _selected_game_name(config: dict[str, Any], bot_cfg: dict[str, Any], game_override: str | None) -> str:
    available = sorted(str(name) for name in bot_cfg.get("games", {}).keys())
    if game_override:
        return game_override
    if bot_cfg.get("default_game"):
        return str(bot_cfg["default_game"])
    if len(available) > 1:
        project_name = str(config.get("project", ""))
        if project_name in available:
            return project_name
        return ""
    if len(available) == 1:
        return available[0]
    if config.get("project"):
        return str(config["project"])
    return "default"


def load_bot_config(config_path: Path | None = None, game_override: str | None = None) -> BotConfig:
    """Load game bot config from config.json with optional per-game preset overrides."""
    config = load_config(config_path)
    bot_cfg = config.get("bot", {})
    game_name = _selected_game_name(config, bot_cfg, game_override)
    available_games = sorted(str(name) for name in bot_cfg.get("games", {}).keys())

    if len(available_games) > 1 and not game_override and not bot_cfg.get("default_game") and not game_name:
        raise ValueError(
            "Multiple games configured. Provide --game <name> or set bot.default_game in config.json."
        )
    if available_games and game_name not in available_games:
        raise ValueError(
            f"Unknown game '{game_name}'. Available games: {', '.join(available_games)}"
        )

    game_cfg: dict[str, Any] = {}
    if available_games:
        game_cfg = dict(bot_cfg.get("games", {}).get(game_name, {}))
    merged_bot_cfg = _deep_merge(dict(bot_cfg), game_cfg)

    threshold_cfg = merged_bot_cfg.get("thresholds", {})
    hotkey_cfg = merged_bot_cfg.get("hotkeys", {})
    capture_cfg = merged_bot_cfg.get("capture", {})

    classes = [str(name) for name in config.get("classes", [])]
    threat_classes = [str(name).lower() for name in merged_bot_cfg.get("threat_classes", _default_threat_classes(classes))]

    return BotConfig(
        game=game_name,
        available_games=available_games,
        model_path=_resolve_model_path(config, merged_bot_cfg),
        threat_classes=threat_classes,
        capture=CaptureConfig(
            monitor_index=int(capture_cfg.get("monitor_index", 1)),
            left=_required_int(capture_cfg.get("left"), "left"),
            top=_required_int(capture_cfg.get("top"), "top"),
            width=_required_int(capture_cfg.get("width"), "width"),
            height=_required_int(capture_cfg.get("height"), "height"),
        ),
        thresholds=ThresholdConfig(
            confidence=float(threshold_cfg.get("detection_confidence", 0.35)),
            threat_persistence_frames=int(threshold_cfg.get("threat_persistence_frames", 2)),
            side_switch_cooldown_s=float(threshold_cfg.get("side_switch_cooldown_s", 0.25)),
            max_evade_duration_s=float(threshold_cfg.get("max_evade_duration_s", 0.6)),
            stabilize_duration_s=float(threshold_cfg.get("stabilize_duration_s", 0.12)),
        ),
        hotkeys=HotkeyConfig(
            toggle_active=str(hotkey_cfg.get("toggle_active", "f8")).lower(),
            emergency_kill=str(hotkey_cfg.get("emergency_kill", "f9")).lower(),
        ),
        loop_hz=float(merged_bot_cfg.get("loop_hz", 30.0)),
        log_hz=float(merged_bot_cfg.get("log_hz", 5.0)),
        imgsz=int(merged_bot_cfg.get("imgsz", 640)),
        dry_run=bool(merged_bot_cfg.get("dry_run", False)),
    )


def list_games(config_path: Path | None = None) -> list[str]:
    config = load_config(config_path)
    bot_cfg = config.get("bot", {})
    return sorted(str(name) for name in bot_cfg.get("games", {}).keys())
