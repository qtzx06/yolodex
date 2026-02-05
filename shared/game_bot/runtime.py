"""Runtime loop for real-time play bot using MSS + YOLO + state machine."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from pynput.keyboard import Key, KeyCode, Listener

from shared.game_bot.capture import MSSCapture
from shared.game_bot.config import BotConfig, list_games, load_bot_config
from shared.game_bot.input_controller import InputController
from shared.game_bot.state_machine import Decision, GameStateMachine, MoveDirection, StateMachineConfig
from shared.game_bot.types import ThreatSide


@dataclass
class RuntimeFlags:
    active: bool = False
    killed: bool = False


class StatusView:
    """Single-screen status output with clear redraws."""

    def __init__(self, hz: float) -> None:
        self._min_interval_s = 1.0 / max(hz, 1.0)
        self._last_draw = 0.0

    def draw(
        self,
        *,
        now: float,
        flags: RuntimeFlags,
        decision: Decision,
        threat: object,
        frame_ms: float,
        capture_region: tuple[int, int, int, int],
        hotkeys: tuple[str, str],
        game: str,
    ) -> None:
        if now - self._last_draw < self._min_interval_s:
            return
        self._last_draw = now
        print("\033[2J\033[H", end="")
        print("Yolodex Play Bot")
        print(f"game: {game}")
        print(f"active: {flags.active} | kill: {flags.killed}")
        print(f"state: {decision.state.value} | move: {decision.move.value}")
        print(f"threat(observed/persistent): {decision.observed_threat.value}/{decision.persistent_threat.value}")
        best = getattr(threat, "best", None)
        side = getattr(threat, "side", ThreatSide.NONE)
        score = getattr(threat, "score", 0.0)
        if best is None:
            print("best detection: none")
        else:
            print(
                "best detection: "
                f"{best.class_name} conf={best.confidence:.2f} "
                f"side={side.value} score={score:.3f}"
            )
        print(f"capture region: left={capture_region[0]} top={capture_region[1]} w={capture_region[2]} h={capture_region[3]}")
        print(f"frame time: {frame_ms:.1f} ms")
        print(f"hotkeys: toggle={hotkeys[0]} | emergency={hotkeys[1]}", flush=True)


def _parse_hotkey(token: str) -> Key | KeyCode:
    t = token.lower().strip()
    if len(t) == 1:
        return KeyCode.from_char(t)
    if hasattr(Key, t):
        return getattr(Key, t)
    raise ValueError(f"Unsupported hotkey: {token}")


def _hotkey_matches(pressed: Key | KeyCode | None, target: Key | KeyCode) -> bool:
    if pressed is None:
        return False
    if isinstance(target, KeyCode):
        if not isinstance(pressed, KeyCode):
            return False
        return pressed.char == target.char
    return pressed == target


def _print_monitor_info(bot_cfg: BotConfig) -> None:
    capture = MSSCapture(bot_cfg.capture)
    try:
        print("Available monitors:")
        for m in capture.monitor_info():
            print(
                f"  {m['index']}: left={m['left']} top={m['top']} "
                f"width={m['width']} height={m['height']}"
            )
    finally:
        capture.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic gameplay bot with MSS + YOLO.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to config.json (defaults to repo config).",
    )
    parser.add_argument(
        "--monitor-info",
        action="store_true",
        help="Print monitor geometry and exit.",
    )
    parser.add_argument(
        "--list-games",
        action="store_true",
        help="Print configured game presets and exit.",
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Game preset key under bot.games in config.json (feature flag).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run detections/state machine without sending keyboard input.",
    )
    parser.add_argument(
        "--start-active",
        action="store_true",
        help="Start in active mode immediately (otherwise toggle with hotkey).",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.list_games:
        games = list_games(args.config)
        if not games:
            print("No game presets configured in bot.games.")
        else:
            print("Configured games:")
            for name in games:
                print(f"  - {name}")
        return 0

    try:
        bot_cfg = load_bot_config(args.config, game_override=args.game)
    except ValueError as exc:
        print(f"Config error: {exc}")
        return 1
    if args.monitor_info:
        _print_monitor_info(bot_cfg)
        return 0

    if not bot_cfg.model_path.exists():
        print(f"Model weights not found: {bot_cfg.model_path}")
        print("Train first or set bot.model_path in config.json (or game preset).")
        return 1

    print(f"[play] Selected game: {bot_cfg.game}", flush=True)
    print(f"[play] Loading model from: {bot_cfg.model_path}", flush=True)
    print(
        "[play] Capture region source: "
        f"monitor={bot_cfg.capture.monitor_index}, "
        f"left={bot_cfg.capture.left}, top={bot_cfg.capture.top}, "
        f"width={bot_cfg.capture.width}, height={bot_cfg.capture.height}",
        flush=True,
    )

    from shared.game_bot.detector import ThreatObservation, YoloThreatDetector

    toggle_hotkey = _parse_hotkey(bot_cfg.hotkeys.toggle_active)
    kill_hotkey = _parse_hotkey(bot_cfg.hotkeys.emergency_kill)

    capture = MSSCapture(bot_cfg.capture)
    detector = YoloThreatDetector(
        model_path=bot_cfg.model_path,
        confidence=bot_cfg.thresholds.confidence,
        imgsz=bot_cfg.imgsz,
        threat_classes=bot_cfg.threat_classes,
    )
    sm = GameStateMachine(
        StateMachineConfig(
            threat_persistence_frames=bot_cfg.thresholds.threat_persistence_frames,
            side_switch_cooldown_s=bot_cfg.thresholds.side_switch_cooldown_s,
            max_evade_duration_s=bot_cfg.thresholds.max_evade_duration_s,
            stabilize_duration_s=bot_cfg.thresholds.stabilize_duration_s,
        )
    )
    input_controller = InputController(dry_run=(args.dry_run or bot_cfg.dry_run))
    status = StatusView(hz=bot_cfg.log_hz)

    flags = RuntimeFlags(active=bool(args.start_active), killed=False)
    lock = Lock()

    def on_press(key: Key | KeyCode | None) -> None:
        nonlocal flags
        with lock:
            if _hotkey_matches(key, toggle_hotkey):
                flags.active = not flags.active
                if not flags.active:
                    input_controller.apply(MoveDirection.NONE, hold_space=False)
                    sm.reset(time.monotonic())
            elif _hotkey_matches(key, kill_hotkey):
                flags.killed = True

    listener = Listener(on_press=on_press)
    listener.start()

    now = time.monotonic()
    sm.reset(now)
    decision = sm.update(ThreatSide.NONE, now)
    threat = ThreatObservation(side=ThreatSide.NONE, best=None, score=0.0)
    target_dt = 1.0 / max(bot_cfg.loop_hz, 1.0)
    print(
        f"[play] Ready. active={flags.active} dry_run={args.dry_run or bot_cfg.dry_run} "
        f"toggle={bot_cfg.hotkeys.toggle_active} emergency={bot_cfg.hotkeys.emergency_kill}",
        flush=True,
    )

    try:
        while True:
            loop_start = time.monotonic()
            with lock:
                if flags.killed:
                    break
                active = flags.active

            frame = capture.grab_bgr()
            detections = detector.detect(frame)
            threat = detector.threat_from(detections, frame_width=frame.shape[1], frame_height=frame.shape[0])

            if active:
                decision = sm.update(threat.side, loop_start)
                input_controller.apply(decision.move, hold_space=True)
            else:
                decision = sm.update(ThreatSide.NONE, loop_start)
                input_controller.apply(MoveDirection.NONE, hold_space=False)

            elapsed = time.monotonic() - loop_start
            status.draw(
                now=time.monotonic(),
                flags=flags,
                decision=decision,
                threat=threat,
                frame_ms=elapsed * 1000.0,
                capture_region=(capture.region.left, capture.region.top, capture.region.width, capture.region.height),
                hotkeys=(bot_cfg.hotkeys.toggle_active, bot_cfg.hotkeys.emergency_kill),
                game=bot_cfg.game,
            )

            remaining = target_dt - (time.monotonic() - loop_start)
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        pass
    finally:
        input_controller.release_all()
        capture.close()
        listener.stop()

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run(args)
