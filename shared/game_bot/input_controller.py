"""Keyboard input control for deterministic gameplay actions."""

from __future__ import annotations

import sys
import time

from pynput.keyboard import Controller, Key

from shared.game_bot.state_machine import MoveDirection


class InputController:
    """Maintains key-down state for movement and sends periodic fire taps."""

    def __init__(self, dry_run: bool = False, fire_interval_s: float = 0.12) -> None:
        self._dry_run = dry_run
        self._fire_interval_s = max(0.01, fire_interval_s)
        self._controller = Controller()
        self._backend = "pynput"
        self._quartz_post = None
        self._quartz_create = None
        self._quartz_tap = None
        if sys.platform == "darwin":
            try:
                from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap

                self._quartz_create = CGEventCreateKeyboardEvent
                self._quartz_post = CGEventPost
                self._quartz_tap = kCGHIDEventTap
                self._backend = "quartz"
            except Exception:  # noqa: BLE001
                self._backend = "pynput"
        self._left_down = False
        self._right_down = False
        self._last_fire_tap_at = 0.0

    @property
    def backend(self) -> str:
        return self._backend

    def _keycode(self, key: Key | str) -> int | None:
        if key is Key.left:
            return 123
        if key is Key.right:
            return 124
        if key is Key.space:
            return 49
        if isinstance(key, str):
            token = key.lower()
            if token == "a":
                return 0
            if token == "d":
                return 2
        return None

    def _press_quartz(self, key: Key | str) -> bool:
        if self._quartz_post is None or self._quartz_create is None or self._quartz_tap is None:
            return False
        code = self._keycode(key)
        if code is None:
            return False
        event = self._quartz_create(None, code, True)
        self._quartz_post(self._quartz_tap, event)
        return True

    def _release_quartz(self, key: Key | str) -> bool:
        if self._quartz_post is None or self._quartz_create is None or self._quartz_tap is None:
            return False
        code = self._keycode(key)
        if code is None:
            return False
        event = self._quartz_create(None, code, False)
        self._quartz_post(self._quartz_tap, event)
        return True

    def _press(self, key: Key | str) -> None:
        if self._dry_run:
            return
        if self._press_quartz(key):
            return
        self._controller.press(key)

    def _release(self, key: Key | str) -> None:
        if self._dry_run:
            return
        if self._release_quartz(key):
            return
        self._controller.release(key)

    def _set_group(self, keys: tuple[Key | str, ...], down: bool, current: bool) -> bool:
        if down and not current:
            for key in keys:
                self._press(key)
            return True
        if not down and current:
            for key in keys:
                self._release(key)
            return False
        return current

    def _set_left(self, down: bool) -> None:
        # Mirror arrow and WASD movement for broader browser-game compatibility.
        self._left_down = self._set_group((Key.left, "a"), down, self._left_down)

    def _set_right(self, down: bool) -> None:
        self._right_down = self._set_group((Key.right, "d"), down, self._right_down)

    def _tap_fire(self) -> None:
        self._press(Key.space)
        self._release(Key.space)

    def apply(self, direction: MoveDirection, hold_space: bool) -> dict[str, bool | str]:
        if direction is MoveDirection.LEFT:
            self._set_left(True)
            self._set_right(False)
        elif direction is MoveDirection.RIGHT:
            self._set_left(False)
            self._set_right(True)
        else:
            self._set_left(False)
            self._set_right(False)

        fire_tapped = False
        if hold_space:
            now = time.monotonic()
            if now - self._last_fire_tap_at >= self._fire_interval_s:
                self._tap_fire()
                self._last_fire_tap_at = now
                fire_tapped = True

        return {
            "left_down": self._left_down,
            "right_down": self._right_down,
            "fire_tapped": fire_tapped,
            "dry_run": self._dry_run,
            "backend": self._backend,
        }

    def release_all(self) -> None:
        self._set_left(False)
        self._set_right(False)
