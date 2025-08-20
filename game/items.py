# game/items.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from .data import items_catalog as C


@dataclass
class ItemProto:
    id: str
    name: str
    slot: str  # "weapon" ou un parmi: gloves, helmet, boots, armor, belt
    cost: int
    bonuses: Dict[str, float]  # keys: max_hp, atk, defense, speed (optionnels)
    desc: str
    sprite: Optional[str] = None  # chemin sprite futur


def _mk(proto: dict) -> ItemProto:
    return ItemProto(
        id=proto["id"],
        name=proto["name"],
        slot=proto["slot"],
        cost=int(proto["cost"]),
        bonuses=dict(proto.get("bonuses", {})),
        desc=proto.get("desc", ""),
        sprite=proto.get("sprite")
    )


# Pools par catégories + pool complet pour les shops
WEAPONS: List[ItemProto] = list(map(_mk, C.WEAPONS))
GLOVES: List[ItemProto] = list(map(_mk, C.GLOVES))
HELMETS: List[ItemProto] = list(map(_mk, C.HELMETS))
BOOTS: List[ItemProto] = list(map(_mk, C.BOOTS))
ARMORS: List[ItemProto] = list(map(_mk, C.ARMORS))
BELTS: List[ItemProto] = list(map(_mk, C.BELTS))

SHOP_POOL: List[ItemProto] = list(map(_mk, C.SHOP_CATALOG))

ACCESSORY_SLOTS = {"gloves", "helmet", "boots", "armor", "belt"}


def format_bonuses(bonuses: dict) -> str:
    # Affiche aussi les nouveaux soins
    order = ["HP", "ATK", "SHD", "SPD", "HEAL_TURN", "HEAL_HIT", "HEAL_START"]
    labels = {
        "HP": "HP", "ATK": "ATK", "SHD": "BLD", "SPD": "SPD",
        "HEAL_TURN": "S/tour", "HEAL_HIT": "S/coup", "HEAL_START": "S/début"
    }
    parts = []
    for k in order:
        if k not in bonuses:
            continue
        try:
            n = int(round(float(bonuses.get(k, 0) or 0)))
        except Exception:
            n = 0
        if n == 0:
            continue
        sign = "+" if n > 0 else "−"
        parts.append(f"{sign}{abs(n)} {labels.get(k, k)}")
    return ", ".join(parts)


def _apply_bonuses(unit, bonuses: Dict[str, float], sign: float):
    hp_inc = bonuses.get("max_hp", 0.0) * sign
    if abs(hp_inc) > 1e-9:
        unit.max_hp += hp_inc
        unit.max_hp = max(1.0, unit.max_hp)
        unit.hp += hp_inc
        if unit.hp > unit.max_hp: unit.hp = unit.max_hp
        if unit.hp < 0: unit.hp = 0
    atk = bonuses.get("atk", 0.0) * sign
    if abs(atk) > 1e-9:
        unit.atk += atk
        if unit.atk < 0: unit.atk = 0.0
    df = bonuses.get("defense", 0.0) * sign
    if abs(df) > 1e-9:
        unit.defense += df
    sp = bonuses.get("speed", 0.0) * sign
    if abs(sp) > 1e-9:
        unit.speed += sp


def equip_item(equipment, unit, proto, logs=None):
    def apply_bon(bon: dict, sign: int):
        hp  = int(round(float(bon.get("HP", 0)  or 0))) * sign
        atk = int(round(float(bon.get("ATK", 0) or 0))) * sign
        shd = int(round(float(bon.get("SHD", 0) or 0))) * sign
        spd = int(round(float(bon.get("SPD", 0) or 0))) * sign

        heal_turn  = int(round(float(bon.get("HEAL_TURN", 0)  or 0))) * sign
        heal_hit   = int(round(float(bon.get("HEAL_HIT", 0)   or 0))) * sign
        heal_start = int(round(float(bon.get("HEAL_START", 0) or 0))) * sign

        if hp:
            unit.max_hp = max(1, unit.max_hp + hp)
            unit.hp = min(unit.hp, unit.max_hp)
        if atk:
            unit.atk = max(0, unit.atk + atk)
        if shd:
            # on ajuste la capacité max
            unit.max_shield = max(0, int(getattr(unit, "max_shield", 0)) + shd)
        if spd:
            unit.speed = max(0, unit.speed + spd)

        # *** SOINS cumulés sur le personnage (attributs dynamiques) ***
        unit.heal_per_turn = int(getattr(unit, "heal_per_turn", 0)) + heal_turn
        unit.heal_on_hit = int(getattr(unit, "heal_on_hit", 0)) + heal_hit
        unit.heal_on_combat_start = int(getattr(unit, "heal_on_combat_start", 0)) + heal_start

        # *** IMPORTANT : hors combat, le bouclier est toujours plein ***
        unit.shield = int(getattr(unit, "max_shield", 0))

    slot = getattr(proto, "slot", "accessory")
    if slot == "weapon":
        old = equipment.get("weapon")
        if old is not None:
            apply_bon(old.bonuses, -1)
        equipment["weapon"] = proto
        apply_bon(proto.bonuses, +1)
        if logs is not None:
            logs.append(f"Équipé arme : {getattr(proto, 'name','???')}")
        return True

    acc = equipment.setdefault("accessories", [])
    if len(acc) >= 4:
        if logs is not None:
            logs.append("Slots d'accessoires pleins (4/4).")
        return False

    acc.append(proto)
    apply_bon(proto.bonuses, +1)
    if logs is not None:
        logs.append(f"Équipé : {getattr(proto, 'name','???')}")
    return True
