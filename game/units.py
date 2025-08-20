# game/units.py
import random
from dataclasses import dataclass
import random


@dataclass
class Unit:
    name: str
    max_hp: float
    hp: float
    atk: float
    defense: float
    speed: float
    alive: bool = True
    is_boss: bool = False

    def take_damage(self, dmg: float) -> float:
        real = max(0.0, dmg - self.defense)
        self.hp -= real
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return real


def generate_enemy(seed: int, boss: bool = False, encounter_idx: int = 0):
    """
    Ennemis rééquilibrés pour un joueur 10 PV / 1 ATK / 0 DEF / 0 SPD.
    - ENCOUNTER (normal) : au début ~3 PV / 1 ATK, puis augmente doucement.
    - BOSS : plus solide (~8 PV + 2 par palier), ATK augmente plus tard.
    Le paramètre encounter_idx reflète la progression (nb de combats gagnés).
    """
    rng = random.Random(seed)

    tier = max(0, int(encounter_idx))

    if not boss:
        # ENNEMI NORMAL — progression douce
        max_hp = 3 + tier            # 3,4,5,... (reste bas au début)
        atk    = 1 + (1 if tier >= 6 else 0)   # passe à 2 seulement assez tard
        defense = 0.0
        speed   = 0.0                # même vitesse que le joueur (alternance simple)
        name = f"Mob T{tier}"
    else:
        # BOSS — plus costaud mais jouable avec 10 PV / 1 ATK
        max_hp = 8 + 2*tier          # 8,10,12,...
        atk    = 1 + (1 if tier >= 3 else 0)  # passe à 2 un peu plus tard
        defense = 0.0
        speed   = 0.0
        name = f"Boss T{tier}"

    # Petit flottement aléatoire très léger pour éviter trop d'uniformité
    max_hp = max(1, int(max_hp + rng.choice([0,0,0,1])))
    # hp de départ = hp max
    enemy = Unit(name, max_hp, float(max_hp), float(atk), float(defense), float(speed))
    enemy.is_boss = boss
    return enemy

