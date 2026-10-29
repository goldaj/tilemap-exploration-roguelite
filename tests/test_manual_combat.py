"""Pure combat tests: no Pygame/display/assets or external dependencies."""
import unittest

from game.combat import CombatManager
from game.units import Unit, generate_enemy


def fighter(name="YOU", hp=10, atk=1, defense=0, speed=0):
    return Unit(name, float(hp), float(hp), float(atk), float(defense), float(speed))


class ManualCombatTests(unittest.TestCase):
    def test_default_auto_attack_remains_compatible(self):
        cm = CombatManager(fighter(), fighter("Mob", 3, 1))
        self.assertTrue(cm.step_turn())
        self.assertEqual(cm.turn_count, 1)
        self.assertEqual(cm.enemy.hp, 2)
        self.assertEqual(cm.player.hp, 9)

    def test_guard_skips_attack_and_blocks_two_damage_once(self):
        cm = CombatManager(fighter(), fighter("Mob", 6, 2))
        self.assertTrue(cm.step_turn("guard"))
        self.assertEqual(cm.enemy.hp, 6)
        self.assertEqual(cm.player.hp, 10)
        self.assertEqual(cm.turn_count, 1)
        self.assertTrue(cm.step_turn("attack"))
        self.assertEqual(cm.enemy.hp, 5)
        self.assertEqual(cm.player.hp, 8)

    def test_power_strike_cooldown_rejects_free_turns(self):
        cm = CombatManager(fighter(), fighter("Tank", 20, 0))
        self.assertTrue(cm.step_turn("power"))
        self.assertEqual(cm.enemy.hp, 18)
        self.assertEqual(cm.power_cooldown, 3)
        self.assertFalse(cm.step_turn("power"))
        self.assertEqual(cm.turn_count, 1)
        for remaining in (2, 1, 0):
            self.assertTrue(cm.step_turn("attack"))
            self.assertEqual(cm.power_cooldown, remaining)
        self.assertTrue(cm.step_turn("power"))
        self.assertEqual(cm.turn_count, 5)

    def test_defense_then_shield_then_hp(self):
        attacker = fighter("Attacker", atk=5)
        defender = fighter("Defender", hp=10, defense=2)
        defender.max_shield = 2
        defender.shield = 2
        cm = CombatManager(attacker, defender)
        dealt = cm._apply_damage(attacker, defender)
        self.assertEqual(dealt, 3)
        self.assertEqual(defender.shield, 0)
        self.assertEqual(defender.hp, 9)

    def test_no_heal_on_guard_or_blocked_damage(self):
        player = fighter(hp=10)
        player.hp = 5
        player.heal_on_hit = 3
        enemy = fighter("Mob", hp=10, atk=0)
        enemy.defense = 99
        cm = CombatManager(player, enemy)
        cm.step_turn("guard")
        self.assertEqual(player.hp, 5)
        cm.step_turn("attack")
        self.assertEqual(player.hp, 5)

    def test_invalid_action_never_advances(self):
        cm = CombatManager(fighter(), fighter("Mob"))
        self.assertFalse(cm.step_turn("heal_to_full"))
        self.assertEqual(cm.turn_count, 0)

    def test_win_and_lose_still_terminal(self):
        win = CombatManager(fighter(atk=4), fighter("Mob", hp=3, atk=1))
        win.step_turn()
        self.assertTrue(win.finished)
        self.assertEqual(win.result, "WIN")
        self.assertFalse(win.enemy.alive)
        self.assertFalse(win.step_turn())
        lose = CombatManager(fighter(hp=1, atk=1), fighter("Boss", hp=4, atk=4))
        lose.step_turn()
        self.assertTrue(lose.finished)
        self.assertEqual(lose.result, "LOSE")
        self.assertFalse(lose.player.alive)

    def test_early_game_balance_is_not_trivial_or_unwinnable(self):
        for seed in range(20):
            enemy = generate_enemy(seed, boss=False, encounter_idx=0)
            cm = CombatManager(fighter(), enemy)
            for _ in range(20):
                if cm.finished:
                    break
                cm.step_turn()
            self.assertEqual(cm.result, "WIN")
            self.assertGreater(cm.player.hp, 0)
            self.assertLess(cm.player.hp, 10)

    def test_player_speed_can_change_turn_order(self):
        enemy = fighter("Fast", hp=5, atk=1, speed=5)
        player = fighter(hp=1, atk=5)
        cm = CombatManager(player, enemy)
        cm.step_turn()
        self.assertEqual(cm.result, "LOSE")


if __name__ == "__main__":
    unittest.main()
