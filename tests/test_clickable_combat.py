"""Offline mouse-routing tests that use the actual game combat rules."""
import unittest

from game.combat import CombatManager
from game.combat_controls import available_actions, route_combat_click
from game.units import Unit


class FakeState:
    def __init__(self):
        self.state = "IN_COMBAT"
        self.auto_play = True
        self.turn_delay = 0.6
        player = Unit("YOU", 10, 10, 1, 0, 0)
        enemy = Unit("Mob", 30, 30, 2, 0, 0)
        self.current_combat = CombatManager(player, enemy)
        self.calls = []

    def toggle_auto(self):
        self.calls.append("auto")
        self.auto_play = not self.auto_play

    def toggle_speed(self):
        self.calls.append("speed")
        self.turn_delay = 0.2 if self.turn_delay == 0.6 else 0.6

    def manual_combat_action(self, name):
        self.calls.append(name)
        return self.current_combat.step_turn(name)


class ClickRoutingTests(unittest.TestCase):
    def test_clickable_toggle_and_speed_only_auto(self):
        state = FakeState()
        self.assertFalse(route_combat_click(state, "combat_attack"))
        self.assertTrue(route_combat_click(state, "combat_speed"))
        self.assertEqual(state.turn_delay, 0.2)
        self.assertTrue(route_combat_click(state, "combat_auto"))
        self.assertFalse(state.auto_play)
        self.assertFalse(route_combat_click(state, "combat_speed"))
        self.assertEqual(state.turn_delay, 0.2)
        self.assertEqual(state.current_combat.turn_count, 0)

    def test_each_click_executes_exactly_one_real_combat_turn(self):
        state = FakeState()
        state.toggle_auto()
        self.assertTrue(route_combat_click(state, "combat_attack"))
        self.assertEqual(state.current_combat.turn_count, 1)
        self.assertEqual(state.current_combat.enemy.hp, 29)
        self.assertTrue(route_combat_click(state, "combat_guard"))
        self.assertEqual(state.current_combat.turn_count, 2)
        self.assertEqual(state.current_combat.player.hp, 8)
        self.assertTrue(route_combat_click(state, "combat_power"))
        self.assertEqual(state.current_combat.turn_count, 3)
        self.assertEqual(state.current_combat.power_cooldown, 3)
        self.assertEqual(state.current_combat.enemy.hp, 26)

    def test_power_is_disabled_during_recharge_without_spending_turn(self):
        state = FakeState()
        state.toggle_auto()
        self.assertTrue(route_combat_click(state, "combat_power"))
        self.assertEqual(state.current_combat.power_cooldown, 3)
        self.assertFalse(available_actions(state)["power"])
        initial = state.current_combat.turn_count
        self.assertFalse(route_combat_click(state, "combat_power"))
        self.assertEqual(state.current_combat.turn_count, initial)
        for remaining in (2, 1, 0):
            self.assertTrue(route_combat_click(state, "combat_attack"))
            self.assertEqual(state.current_combat.power_cooldown, remaining)
        self.assertTrue(available_actions(state)["power"])

    def test_disabled_in_auto_outside_combat_and_after_death(self):
        state = FakeState()
        self.assertEqual(available_actions(state),
                         {"attack": False, "guard": False, "power": False})
        state.state = "EXPLORE"
        self.assertFalse(route_combat_click(state, "combat_auto"))
        self.assertFalse(route_combat_click(state, "combat_attack"))
        state.state = "IN_COMBAT"
        state.toggle_auto()
        state.current_combat.finished = True
        self.assertEqual(available_actions(state)["attack"], False)
        self.assertFalse(route_combat_click(state, "combat_guard"))

    def test_invalid_hotspot_rejected(self):
        state = FakeState()
        state.toggle_auto()
        self.assertFalse(route_combat_click(state, "combat_self_destruct"))
        self.assertEqual(state.current_combat.turn_count, 0)


if __name__ == "__main__":
    unittest.main()
