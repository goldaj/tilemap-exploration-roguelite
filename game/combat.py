# game/combat.py
from typing import List, Optional
from .units import Unit

class CombatManager:
    def __init__(self, player: Unit, enemy: Unit):
        self.player = player
        self.enemy = enemy
        self.turn_count = 0
        self.log: List[str] = []
        self.finished = False
        self.result: Optional[str] = None
        self.power_cooldown = 0  # power unavailable for 3 subsequent turns
        self._guard_this_turn = False

        # Sécurité : s’assurer que les deux ont les attributs de bouclier
        for u in (self.player, self.enemy):
            if not hasattr(u, "max_shield"): u.max_shield = 0
            if not hasattr(u, "shield"): u.shield = 0
        # Valeurs de soin (défaut = 0)
        for u in (self.player,):
            if not hasattr(u, "heal_per_turn"): u.heal_per_turn = 0
            if not hasattr(u, "heal_on_hit"): u.heal_on_hit = 0
            if not hasattr(u, "heal_on_combat_start"): u.heal_on_combat_start = 0
        # Soin de départ de combat (joueur seulement)
        start_heal = int(getattr(self.player, 'heal_on_combat_start', 0))
        if start_heal > 0 and getattr(self.player, 'hp', 0) > 0:
            before = int(self.player.hp)
            self.player.hp = min(self.player.max_hp, self.player.hp + start_heal)
            gained = int(self.player.hp) - before
            if gained > 0:
                self.log.append(f"Début de combat : YOU récupère +{gained} PV.")

    def _apply_damage(self, attacker: Unit, target: Unit, bonus: int = 0) -> int:
        """Defense and guard reduce damage before shield, then remaining HP."""
        dmg = max(0, int(round(attacker.atk)) + bonus)
        dmg = max(0, dmg - max(0, int(round(getattr(target, "defense", 0)))))
        if target is self.player and self._guard_this_turn:
            dmg = max(0, dmg - 2)
        total = 0

        # 1) bouclier
        if getattr(target, "shield", 0) > 0 and dmg > 0:
            absorb = min(target.shield, dmg)
            target.shield -= absorb
            dmg -= absorb
            total += absorb
            if absorb > 0:
                self.log.append(f"{attacker.name} brise {absorb} de bouclier de {target.name}.")

        # 2) PV
        if dmg > 0:
            before = int(target.hp)
            target.hp = max(0, target.hp - dmg)
            if target.hp <= 0:
                target.alive = False
            total += (before - int(target.hp))

        return total

    def step_turn(self, action: str = "attack"):
        """Complete one turn with a chosen player tactic; default remains auto attack.

        attack: regular hit; guard: skip hit, prevent up to two incoming damage;
        power: +max(1, round(ATK/2)) damage, then wait 3 normal turns.
        """
        if self.finished:
            return False
        if action not in ("attack", "guard", "power"):
            return False
        if action == "power" and self.power_cooldown > 0:
            return False  # no turn consumed
        if self.power_cooldown > 0:
            self.power_cooldown -= 1
        if action == "power":
            self.power_cooldown = 3
        self._guard_this_turn = action == "guard"
        self.turn_count += 1

        # Régénération par tour (joueur)
        hpt = int(getattr(self.player, 'heal_per_turn', 0))
        if hpt > 0 and getattr(self.player, 'hp', 0) > 0:
            before = int(self.player.hp)
            self.player.hp = min(self.player.max_hp, self.player.hp + hpt)
            gained = int(self.player.hp) - before
            if gained > 0:
                self.log.append(f"Tour {self.turn_count}: YOU régénère +{gained} PV.")

        actors = [(self.player.speed, "player"), (self.enemy.speed, "enemy")]
        actors.sort(reverse=True, key=lambda x: x[0])

        for _, who in actors:
            if self.finished:
                break

            if who == "player":
                if not getattr(self.player, "alive", True) or self.player.hp <= 0:
                    continue
                if action == "guard":
                    dealt = 0
                    self.log.append(f"Tour {self.turn_count}: PLAYER se protège (-2 dégâts ennemis).")
                else:
                    bonus = max(1, int(round(self.player.atk / 2))) if action == "power" else 0
                    dealt = self._apply_damage(self.player, self.enemy, bonus=bonus)
                    if action == "power":
                        self.log.append(f"Tour {self.turn_count}: FRAPPE PUISSANTE (+{bonus}).")
                self.log.append(
                    f"Tour {self.turn_count}: PLAYER inflige {dealt}  "
                    f"(EN HP {int(self.enemy.hp)}/{int(self.enemy.max_hp)} | "
                    f"BLD {int(self.enemy.shield)}/{int(self.enemy.max_shield)})"
                )
                # Vol de vie / soin à l'impact
                onhit = int(getattr(self.player, 'heal_on_hit', 0))
                if action != "guard" and onhit > 0 and dealt > 0 and getattr(self.player, 'hp', 0) > 0:
                    before = int(self.player.hp)
                    self.player.hp = min(self.player.max_hp, self.player.hp + onhit)
                    gained = int(self.player.hp) - before
                    if gained > 0:
                        self.log.append(f"YOU récupère +{gained} PV sur l'attaque.")
            else:
                if not getattr(self.enemy, "alive", True) or self.enemy.hp <= 0:
                    continue
                dealt = self._apply_damage(self.enemy, self.player)
                self.log.append(
                    f"Tour {self.turn_count}: ENNEMI inflige {dealt}  "
                    f"(PL HP {int(self.player.hp)}/{int(self.player.max_hp)} | "
                    f"BLD {int(self.player.shield)}/{int(self.player.max_shield)})"
                )

            if self.enemy.hp <= 0:
                self.finished = True
                self.result = "WIN"
                self.log.append("ENNEMI VAINCU.")
                break
            if self.player.hp <= 0:
                self.finished = True
                self.result = "LOSE"
                self.log.append("TU ES MORT.")
                break
        self._guard_this_turn = False
        return True
