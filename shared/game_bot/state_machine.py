"""Deterministic state machine for evasion decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from shared.game_bot.detector import ThreatSide


class BotState(str, Enum):
    SEARCH_THREAT = "SEARCH_THREAT"
    EVADE_LEFT = "EVADE_LEFT"
    EVADE_RIGHT = "EVADE_RIGHT"
    STABILIZE = "STABILIZE"


class MoveDirection(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


@dataclass(frozen=True)
class StateMachineConfig:
    threat_persistence_frames: int
    side_switch_cooldown_s: float
    max_evade_duration_s: float
    stabilize_duration_s: float


@dataclass(frozen=True)
class Decision:
    state: BotState
    move: MoveDirection
    observed_threat: ThreatSide
    persistent_threat: ThreatSide


def _threat_to_evasion(threat_side: ThreatSide) -> BotState | None:
    if threat_side is ThreatSide.LEFT:
        return BotState.EVADE_RIGHT
    if threat_side is ThreatSide.RIGHT:
        return BotState.EVADE_LEFT
    return None


class GameStateMachine:
    """Finite-state machine for consistent left/right evade outputs."""

    def __init__(self, config: StateMachineConfig) -> None:
        self._cfg = config
        self.state = BotState.SEARCH_THREAT
        self._state_entered_at = 0.0
        self._last_switch_at = -1e9
        self._pending_threat = ThreatSide.NONE
        self._pending_count = 0
        self._no_threat_frames = 0

    def reset(self, now: float) -> None:
        self.state = BotState.SEARCH_THREAT
        self._state_entered_at = now
        self._pending_threat = ThreatSide.NONE
        self._pending_count = 0
        self._no_threat_frames = 0

    def _transition(self, new_state: BotState, now: float, update_switch: bool = False) -> None:
        if self.state == new_state:
            return
        self.state = new_state
        self._state_entered_at = now
        if update_switch:
            self._last_switch_at = now

    def _persistent_threat(self, observed: ThreatSide) -> ThreatSide:
        if observed is ThreatSide.NONE:
            self._pending_threat = ThreatSide.NONE
            self._pending_count = 0
            self._no_threat_frames += 1
            return ThreatSide.NONE

        self._no_threat_frames = 0
        if observed is self._pending_threat:
            self._pending_count += 1
        else:
            self._pending_threat = observed
            self._pending_count = 1

        if self._pending_count >= max(1, self._cfg.threat_persistence_frames):
            return observed
        return ThreatSide.NONE

    def _move_for_state(self) -> MoveDirection:
        if self.state is BotState.EVADE_LEFT:
            return MoveDirection.LEFT
        if self.state is BotState.EVADE_RIGHT:
            return MoveDirection.RIGHT
        return MoveDirection.NONE

    def update(self, observed_threat: ThreatSide, now: float) -> Decision:
        persistent = self._persistent_threat(observed_threat)
        desired_state = _threat_to_evasion(persistent)

        if self.state is BotState.SEARCH_THREAT:
            if desired_state is not None:
                self._transition(desired_state, now, update_switch=True)

        elif self.state in (BotState.EVADE_LEFT, BotState.EVADE_RIGHT):
            if now - self._state_entered_at >= self._cfg.max_evade_duration_s:
                self._transition(BotState.STABILIZE, now)
            elif desired_state is not None and desired_state is not self.state:
                if (now - self._last_switch_at) >= self._cfg.side_switch_cooldown_s:
                    self._transition(desired_state, now, update_switch=True)
            elif self._no_threat_frames >= max(1, self._cfg.threat_persistence_frames):
                self._transition(BotState.STABILIZE, now)

        elif self.state is BotState.STABILIZE:
            if now - self._state_entered_at >= self._cfg.stabilize_duration_s:
                self._transition(BotState.SEARCH_THREAT, now)

        return Decision(
            state=self.state,
            move=self._move_for_state(),
            observed_threat=observed_threat,
            persistent_threat=persistent,
        )

