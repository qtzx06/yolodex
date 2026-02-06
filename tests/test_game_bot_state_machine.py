"""Unit tests for deterministic gameplay state machine behavior."""

from __future__ import annotations

import unittest

from shared.game_bot.state_machine import BotState, GameStateMachine, MoveDirection, StateMachineConfig
from shared.game_bot.types import ThreatSide


class GameStateMachineTests(unittest.TestCase):
    def test_persistent_threat_triggers_evade(self) -> None:
        sm = GameStateMachine(
            StateMachineConfig(
                threat_persistence_frames=2,
                side_switch_cooldown_s=0.25,
                max_evade_duration_s=0.6,
                stabilize_duration_s=0.1,
            )
        )
        sm.reset(0.0)

        d1 = sm.update(ThreatSide.LEFT, 0.01)
        self.assertEqual(d1.state, BotState.SEARCH_THREAT)
        self.assertEqual(d1.move, MoveDirection.NONE)

        d2 = sm.update(ThreatSide.LEFT, 0.02)
        self.assertEqual(d2.state, BotState.EVADE_RIGHT)
        self.assertEqual(d2.move, MoveDirection.RIGHT)

    def test_switch_respects_cooldown(self) -> None:
        sm = GameStateMachine(
            StateMachineConfig(
                threat_persistence_frames=1,
                side_switch_cooldown_s=0.5,
                max_evade_duration_s=2.0,
                stabilize_duration_s=0.1,
            )
        )
        sm.reset(0.0)

        d1 = sm.update(ThreatSide.LEFT, 0.01)
        self.assertEqual(d1.state, BotState.EVADE_RIGHT)

        # Opposite threat before cooldown expires: keep current evade.
        d2 = sm.update(ThreatSide.RIGHT, 0.2)
        self.assertEqual(d2.state, BotState.EVADE_RIGHT)

        # After cooldown: switch allowed.
        d3 = sm.update(ThreatSide.RIGHT, 0.7)
        self.assertEqual(d3.state, BotState.EVADE_LEFT)

    def test_evade_times_out_to_stabilize_then_search(self) -> None:
        sm = GameStateMachine(
            StateMachineConfig(
                threat_persistence_frames=1,
                side_switch_cooldown_s=0.1,
                max_evade_duration_s=0.3,
                stabilize_duration_s=0.2,
            )
        )
        sm.reset(0.0)

        d1 = sm.update(ThreatSide.RIGHT, 0.01)
        self.assertEqual(d1.state, BotState.EVADE_LEFT)

        d2 = sm.update(ThreatSide.RIGHT, 0.35)
        self.assertEqual(d2.state, BotState.STABILIZE)

        d3 = sm.update(ThreatSide.NONE, 0.6)
        self.assertEqual(d3.state, BotState.SEARCH_THREAT)


if __name__ == "__main__":
    unittest.main()
