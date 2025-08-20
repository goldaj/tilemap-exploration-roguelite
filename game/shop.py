# game/shop.py
import random
from typing import List, Tuple, Optional
from .items import SHOP_POOL, ItemProto

class ShopEntry:
    __slots__ = ("proto", "name", "desc", "cost", "_sold")
    def __init__(self, proto: ItemProto):
        self.proto = proto
        self.name = proto.name
        self.desc = proto.desc
        self.cost = int(proto.cost)
        self._sold = False

class Shop:
    def __init__(self, rng_seed: int = 12345):
        self.rng = random.Random(rng_seed)

    def _gen_inventory(self) -> List[ShopEntry]:
        pool = list(SHOP_POOL)
        self.rng.shuffle(pool)
        chosen = pool[:3] if len(pool) >= 3 else pool
        return [ShopEntry(p) for p in chosen]

    def open(self, inventory: Optional[List[ShopEntry]] = None) -> List[ShopEntry]:
        if inventory is None or not inventory:
            return self._gen_inventory()
        return inventory

    def buy(self, idx: int, gold: int, inventory: List[ShopEntry]) -> Tuple[bool, int, str, Optional[ItemProto]]:
        visible = [it for it in inventory if not it._sold]
        if not (0 <= idx < len(visible)):
            return False, gold, "Choix invalide.", None
        entry = visible[idx]
        if entry._sold:
            return False, gold, "Déjà acheté.", None
        if gold < entry.cost:
            return False, gold, "Pas assez d'or.", None
        entry._sold = True
        new_gold = gold - entry.cost
        return True, new_gold, f"Acheté: {entry.name} (-{entry.cost} or)", entry.proto
