"""Keyboard input control for deterministic gameplay actions."""

from __future__ import annotations

from pynput.keyboard import Controller, Key

from shared.game_bot.state_machine import MoveDirection


class InputController:
    """Maintains key-down state for left/right movement and hold-to-shoot."""

    def __init__(self, dry_run: bool = False) -> None:
        self._dry_run = dry_run
        self._controller = Controller()
        self._left_down = False
        self._right_down = False
        self._space_down = False

    def _press(self, key: Key) -> None:
        if self._dry_run:
            return
        self._controller.press(key)

    def _release(self, key: Key) -> None:
        if self._dry_run:
            return
        self._controller.release(key)

    def _set_left(self, down: bool) -> None:
        if down and not self._left_down:
            self._press(Key.left)
            self._left_down = True
        elif not down and self._left_down:
            self._release(Key.left)
            self._left_down = False

    def _set_right(self, down: bool) -> None:
        if down and not self._right_down:
            self._press(Key.right)
            self._right_down = True
        elif not down and self._right_down:
            self._release(Key.right)
            self._right_down = False

    def _set_space(self, down: bool) -> None:
        if down and not self._space_down:
            self._press(Key.space)
            self._space_down = True
        elif not down and self._space_down:
            self._release(Key.space)
            self._space_down = False

    def apply(self, direction: MoveDirection, hold_space: bool) -> None:
        if direction is MoveDirection.LEFT:
            self._set_left(True)
            self._set_right(False)
        elif direction is MoveDirection.RIGHT:
            self._set_left(False)
            self._set_right(True)
        else:
            self._set_left(False)
            self._set_right(False)
        self._set_space(hold_space)

    def release_all(self) -> None:
        self._set_left(False)
        self._set_right(False)
        self._set_space(False)

