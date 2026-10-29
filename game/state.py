# game/state.py
import random
from typing import Optional
import settings as S
from .world import MapGraph
from .node import NodeType
from .units import Unit, generate_enemy
from .combat import CombatManager
from .shop import Shop
from .items import SHOP_POOL
from .items import ItemProto, equip_item, format_bonuses
# remplace MapGraph/GridMapper par :
from .infinite_grid import InfiniteGrid, TileEvent
from .node import NodeType
from datetime import date


class GameState:
    def __init__(self, w: int, h: int):
        # monde & joueur
        self.map = MapGraph(w, h, S.NODE_COUNT)
        # --- SUPPRIMER LES BOSS DE LA CARTE ---
        from .node import NodeType
        for node in self.map.nodes.values():
            if node.ntype == NodeType.BOSS:
                # on convertit tout boss en rencontre standard
                node.ntype = NodeType.ENCOUNTER
                node.event_done = False
        self.player_node = self.map.start_id
        self.gold = S.START_GOLD
        self.items = []
        self.player_unit = Unit("YOU", 10, 10, 1.0, 0.0, 0.0)
        # Bouclier (pool séparé des PV)
        self.player_unit.max_shield = 0
        self.player_unit.shield = 0
        # Soins cumulés (nouvelles mécaniques)
        self.player_unit.heal_per_turn = 0
        self.player_unit.heal_on_hit = 0
        self.player_unit.heal_on_combat_start = 0

        # ÉQUIPEMENT
        self.equipment = {"weapon": None, "accessories": []}  # 4 accessoires max

        # états
        self.state = "EXPLORE"  # EXPLORE, READY_COMBAT, IN_COMBAT, SHOP, DEAD
        self.current_combat: Optional[CombatManager] = None
        self.current_enemy_seed = None

        # progression
        self.nodes_visited_count = 1
        self.map.nodes[self.player_node].visited = True
        self.encounters_done = 0

        # --- boss récurrents ---
        self.boss_interval = getattr(S, "BOSS_INTERVAL_NODES", 5)
        self.next_boss_at = self.boss_interval
        self.boss_count = 0  # juste informatif / si tu veux scaler plus tard

        # combat timing
        self.auto_play = True
        self.turn_delay = S.SLOW_TURN
        self.time_since_last_turn = 0.0

        # boutique
        self.shop = Shop()
        self.shop_choices = []

        # coffre
        self.chest_choices = []  # liste courante à afficher dans l’overlay coffre

        # logs
        self.logs = ["Déplacement libre sur tuiles — visite 5 nœuds distincts pour déclencher le boss."]

        # --- Monde infini (chunks) ---
        # Détermine le seed du monde
        ws = getattr(S, "WORLD_SEED", "random")
        if isinstance(ws, int):
            world_seed = ws
        elif isinstance(ws, str) and ws.lower() == "daily":
            world_seed = int(date.today().strftime("%Y%m%d"))
        else:
            # aléatoire à chaque run (cryptographiquement robuste)
            world_seed = random.SystemRandom().randrange(1, 2 ** 31 - 1)

        self.grid = InfiniteGrid(tile_size=S.TILE_SIZE, chunk_size=24, world_seed=world_seed)

        # Log pour vérifier facilement
        self.logs.insert(0, f"Seed monde: {world_seed}")

        # Position de départ = centre (0,0) sur un chemin (le chunk se crée à la volée)
        self.gx, self.gy = 0, 0
        # Force la génération d'une case praticable autour de (0,0) si besoin : on "téléporte" au hub du premier chunk
        ch0 = self.grid._ensure_chunk_for_tile(self.gx, self.gy)
        hub = ch0.size // 2
        self.gx = ch0.cx * ch0.size + hub
        self.gy = ch0.cy * ch0.size + hub

        # déplacement animé 1 tuile
        self.moving = False
        self.move_t = 0.0
        self.move_dur = S.TILEMOVE_DURATION
        self.next_dir = None  # direction en file pour enchaîner quand on maintient la flèche
        self.move_src = (float(self.gx), float(self.gy))
        self.move_dst = (float(self.gx), float(self.gy))
        self.held_dir = None  # direction actuellement maintenue (mise à jour par App)
        self.move_dir = None  # "up"/"down"/"left"/"right" du pas en cours
        self._hold_timer = 0.0  # durée de maintien dans la même direction que move_dir
        self._hold_eligible = False  # vrai si on a tenu assez longtemps pour autoriser le chaînage

        # sélection voisine n'est plus utile, on garde None pour compat UI
        self.selected_neighbor = None

        self.pending = {}  # infos de preview/remplacement
        # self.pending = {
        #   'from': 'SHOP'|'CHEST',
        #   'entry': <ShopEntry or chest entry>,
        #   'proto': <ItemProto>,
        #   'shop_event': <TileEvent> (pour SHOP),
        #   'shop_entry_ref': <ref exact du choix dans la liste visible> (facultatif),
        #   'chest_event': <TileEvent> (pour CHEST),
        #   'replace_kind': 'weapon'|'accessory',
        #   'replace_index': int|None
        # }

    # -------- caméra (UI lit cette position interpolée) --------
    def get_camera_center_grid(self) -> tuple[float, float]:
        if self.moving:
            t = self.move_t / max(1e-6, S.TILEMOVE_DURATION)
            p = self._ease01(t)
            x = self.move_src[0] + (self.move_dst[0] - self.move_src[0]) * p
            y = self.move_src[1] + (self.move_dst[1] - self.move_src[1]) * p
            return (x, y)
        return (float(self.gx), float(self.gy))

    def _ease01(self, t: float) -> float:
        if getattr(S, "MOVE_EASING", "ease_in_out") == "linear":
            return max(0.0, min(1.0, t))
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    def set_held_dir(self, d: str | None):
        self.held_dir = d

    def _queue_dir_if_possible(self, direction: str):
        if not direction or self.state != "EXPLORE": return
        dx, dy = self._dir_to_delta(direction)
        # on évalue depuis la prochaine case (move_dst) pour l'enchaînement
        base_x, base_y = (self.move_dst if self.moving else (self.gx, self.gy))
        nx, ny = base_x + dx, base_y + dy
        if self.grid.can_step(base_x, base_y, nx, ny):
            self.next_dir = direction

    def _dir_to_delta(self, d: str) -> tuple[int, int]:
        return {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(d, (0, 0))

    def request_move(self, direction: str) -> bool:
        if self.state != "EXPLORE":
            return False
        dx, dy = self._dir_to_delta(direction)
        if dx == dy == 0:
            return False

        # Si déjà en mouvement, on *file* la dir demandée (queue), mais on ne déclenche pas tout de suite
        if self.moving:
            self.next_dir = direction
            return True

        nx, ny = self.gx + dx, self.gy + dy
        if not self.grid.can_step(self.gx, self.gy, nx, ny):
            return False

        # Démarre le pas
        self.moving = True
        self.move_src = (self.gx, self.gy)
        self.move_dst = (nx, ny)
        self.move_t = 0.0
        self.move_dir = direction
        # reset du tracking de maintien
        self._hold_timer = 0.0
        self._hold_eligible = False
        return True

    # -------- input depuis App (flèches) --------
    def try_move_dir(self, dx: int, dy: int):
        """Demande de bouger d'une tuile (dx,dy) si état le permet."""
        if self.state not in ("EXPLORE", "READY_COMBAT"):  # en combat/shop: no move
            return
        if self.moving:
            return
        nx, ny = self.gx + dx, self.gy + dy
        if not self.grid.can_step(self.gx, self.gy, nx, ny):
            return
        # lancer l'anim
        self.move_src = (float(self.gx), float(self.gy))
        self.move_dst = (float(nx), float(ny))
        self.move_t = 0.0
        self.moving = True

    # -------- arrivée sur une tuile --------
    def _arrive_on_tile(self):
        # fin d'anim
        self.gx, self.gy = int(self.move_dst[0]), int(self.move_dst[1])
        self.moving = False
        self.move_t = 0.0

        ev = self.grid.get_event_at(self.gx, self.gy)

        if ev is None:
            # case chemin sans événement
            if self.state != "IN_COMBAT" and self.state != "SHOP":
                self.state = "EXPLORE"
            return

        # première visite => incrémente progression
        if not ev.visited:
            ev.visited = True
            self.nodes_visited_count += 1
            self.logs.append(f"Découverte d'une case spéciale ({ev.etype}).")

        # Boss récurrent : dès qu'on atteint la prochaine cible, on lance le boss
        if self.nodes_visited_count >= self.next_boss_at:
            self.spawn_boss()
            # prépare la prochaine vague
            self.next_boss_at += self.boss_interval
            return

        if ev.etype == "CHEST" and not ev.event_done:
            # génère 3 items gratuits ; on réutilise le générateur du shop pour piocher des items variés
            if ev.chest_choices is None:
                # self.shop.open(None) te renverra une liste de 3 propositions (ShopEntry) -> on s’en sert comme "loot"
                ev.chest_choices = self.shop.open(None)
            self.chest_choices = list(ev.chest_choices)[:3]
            self.state = "CHEST"
            self.logs.append("Coffre trouvé : choisissez 1 item gratuit (1/2/3) ou sortez (E/SPACE).")
            return

        # Résolution d'événement
        if ev.etype == "ENCOUNTER" and not ev.event_done:
            from .units import Unit, generate_enemy
            enemy = generate_enemy(random.randint(0, 999999), boss=False, encounter_idx=self.encounters_done)

            # Mapper l’ancienne DEF éventuelle -> bouclier de l’ennemi (si présent)
            enemy.max_shield = max(0, int(round(getattr(enemy, "defense", 0) or 0)))
            enemy.shield = enemy.max_shield

            # Clone du joueur pour le combat, + bouclier
            player_clone = Unit(self.player_unit.name, self.player_unit.max_hp, self.player_unit.hp,
                                self.player_unit.atk, 0.0, self.player_unit.speed)
            player_clone.max_shield = int(getattr(self.player_unit, "max_shield", 0))
            player_clone.shield = int(getattr(self.player_unit, "shield", 0))
            # Propager les soins
            player_clone.heal_per_turn = int(getattr(self.player_unit, "heal_per_turn", 0))
            player_clone.heal_on_hit = int(getattr(self.player_unit, "heal_on_hit", 0))
            player_clone.heal_on_combat_start = int(getattr(self.player_unit, "heal_on_combat_start", 0))

            cm = CombatManager(player_clone, enemy)
            self.current_combat = cm
            self.state = "IN_COMBAT"
            self.logs.append(f"Combat ENNEMI auto-lancé (HP {int(enemy.hp)} | BLD {int(enemy.shield)})")
            self.auto_play = True
            self.time_since_last_turn = 0.0
            ev.event_done = True
            return

        if ev.etype == "SHOP":
            # shop persistant par tuile
            if ev.shop_inventory is None:
                ev.shop_inventory = self.shop.open(None)
            else:
                ev.shop_inventory = self.shop.open(ev.shop_inventory)

            self.shop_choices = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]

            if not self.shop_choices:
                ev.event_done = True
                self.logs.append("Boutique épuisée : plus rien à acheter.")
                self.state = "EXPLORE"
                return

            self.state = "SHOP"
            self.logs.append("Boutique : 1/2/3 acheter — E/SPACE/ENTRÉE pour quitter.")
            return

        # sinon retour à l'exploration
        if self.state != "IN_COMBAT":
            self.state = "EXPLORE"

    # -------- boss / combats / shop (inchangé sauf soins propagés) --------
    def spawn_boss(self):
        self.boss_count += 1
        enemy = generate_enemy(random.randint(0, 999999), boss=True, encounter_idx=self.encounters_done)
        player_clone = Unit(self.player_unit.name, self.player_unit.max_hp, self.player_unit.hp,
                            self.player_unit.atk, self.player_unit.defense, self.player_unit.speed)
        # Propager les soins
        player_clone.heal_per_turn = int(getattr(self.player_unit, "heal_per_turn", 0))
        player_clone.heal_on_hit = int(getattr(self.player_unit, "heal_on_hit", 0))
        player_clone.heal_on_combat_start = int(getattr(self.player_unit, "heal_on_combat_start", 0))
        cm = CombatManager(player_clone, enemy)
        self.current_combat = cm
        self.state = "IN_COMBAT"
        self.logs.append(f"=== BOSS #{self.boss_count} APPARAÎT ! Combat lancé ===")
        self.auto_play = True
        self.time_since_last_turn = 0.0

    def finish_combat(self):
        cm = self.current_combat
        if cm is None: return
        if cm.result == "WIN":
            reward = 12 + (30 if cm.enemy.is_boss else 0)
            self.gold += reward
            self.logs.append(f"VICTOIRE ! +{reward} or")
            self.player_unit.hp = cm.player.hp
            # --- régénération du bouclier après le combat ---
            self.player_unit.shield = int(getattr(self.player_unit, "max_shield", 0))
            self.encounters_done += 1
            self.state = "EXPLORE"
        else:
            self.player_unit.hp = 0
            self.state = "DEAD"
            self.logs.append("Tu es mort. R pour recommencer.")
        self.current_combat = None

    # shop
    def begin_shop_preview(self, idx: int):
        if self.state != "SHOP":
            return
        ev = self.grid.get_event_at(self.gx, self.gy)
        if not ev or ev.etype != "SHOP" or ev.shop_inventory is None:
            self.logs.append("Pas de boutique ici.")
            return

        visible = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]
        if not (0 <= idx < len(visible)):
            self.logs.append("Choix invalide.")
            return

        entry = visible[idx]
        if self.gold < entry.cost:
            self.logs.append("Or insuffisant.")
            return

        proto = entry.proto

        # Cas ARME : si aucune arme équipée => premier équipement direct (pas d'échange)
        if getattr(proto, "slot", "accessory") == "weapon":
            if self.equipment.get("weapon") is None:
                # Achat direct puis équipement
                success, new_gold, msg, _proto = self.shop.buy(idx, self.gold, ev.shop_inventory)
                if not success:
                    self.logs.append(msg)
                    return
                self.gold = new_gold
                self.logs.append(msg)
                equip_item(self.equipment, self.player_unit, proto, self.logs)

                # Mettre à jour la liste des articles restants (non vendus)
                self.shop_choices = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]

                # Si stock vide -> on ferme + marque l'événement épuisé ; sinon on reste au shop
                if not self.shop_choices:
                    ev.event_done = True
                    self.logs.append("Boutique épuisée : plus rien à acheter.")
                    self.state = "EXPLORE"
                else:
                    self.state = "SHOP"
                return

            # Sinon, on possède déjà une arme -> menu d'échange
            self.pending = {
                'from': 'SHOP',
                'entry': entry,
                'proto': proto,
                'shop_event': ev,
                'replace_kind': 'weapon',
                'replace_index': None
            }
            self.state = "CONFIRM_REPLACE"
            return

        # Cas ACCESSOIRE
        acc = self.equipment.get("accessories", [])
        if len(acc) >= 4:
            # inventaire plein -> sélection de l'accessoire à retirer
            self.pending = {
                'from': 'SHOP',
                'entry': entry,
                'proto': proto,
                'shop_event': ev,
                'replace_kind': 'accessory',
                'replace_index': None
            }
            self.state = "SELECT_DROP"
            return

        # Achat direct + ajout (pas de confirmation)
        success, new_gold, msg, _proto = self.shop.buy(idx, self.gold, ev.shop_inventory)
        if not success:
            self.logs.append(msg)
            return
        self.gold = new_gold
        self.logs.append(msg)
        equip_item(self.equipment, self.player_unit, proto, self.logs)

        # MAJ des choix restants
        self.shop_choices = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]

        # Fermer seulement si plus rien en stock ; sinon on reste au shop
        if not self.shop_choices:
            ev.event_done = True
            self.logs.append("Boutique épuisée : plus rien à acheter.")
            self.state = "EXPLORE"
        else:
            self.state = "SHOP"

    def exit_shop(self):
        if self.state == "SHOP":
            ev = self.grid.get_event_at(self.gx, self.gy)
            # calcule le stock restant si possible
            if ev and ev.etype == "SHOP" and ev.shop_inventory:
                left = len([it for it in ev.shop_inventory if not getattr(it, "_sold", False)])
                if left == 0:
                    ev.event_done = True
                    self.logs.append("La boutique est désormais épuisée.")
            self.state = "EXPLORE"
            self.shop_choices = []
            self.logs.append("Sorti de la boutique (tu peux revenir tant qu’il reste du stock).")

    def select_drop_index(self, idx: int):
        if self.state != "SELECT_DROP":
            return
        acc = self.equipment.get("accessories", [])
        if not (0 <= idx < len(acc)):
            self.logs.append("Index invalide.")
            return
        self.pending['replace_index'] = idx
        self.state = "CONFIRM_REPLACE"

    def cancel_preview(self):
        # Retourne à SHOP ou CHEST sans rien changer
        if self.pending.get('from') == 'SHOP':
            self.state = "SHOP"
        elif self.pending.get('from') == 'CHEST':
            self.state = "CHEST"
        self.pending.clear()

    def confirm_replace(self, accept: bool):
        if self.state != "CONFIRM_REPLACE":
            return
        if not accept:
            return self.cancel_preview()

        src = self.pending.get('from')
        proto = self.pending.get('proto')
        kind = self.pending.get('replace_kind')

        # 1) SHOP : réaliser l'achat maintenant si nécessaire
        if src == 'SHOP':
            ev = self.pending.get('shop_event')
            entry = self.pending.get('entry')
            visible = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]
            try:
                vidx = visible.index(entry)
            except ValueError:
                self.logs.append("Article indisponible.")
                self.pending.clear()
                self.state = "SHOP"
                return
            success, new_gold, msg, _p = self.shop.buy(vidx, self.gold, ev.shop_inventory)
            if not success:
                self.logs.append(msg)
                self.pending.clear()
                self.state = "SHOP"
                return
            self.gold = new_gold
            self.logs.append(msg)

        # 2) Appliquer le remplacement
        if kind == 'weapon':
            equip_item(self.equipment, self.player_unit, proto, self.logs)
        elif kind == 'accessory':
            idx = self.pending.get('replace_index')
            acc = self.equipment.setdefault("accessories", [])
            if not (isinstance(idx, int) and 0 <= idx < len(acc)):
                self.logs.append("Index de remplacement invalide.")
            else:
                old = acc.pop(idx)
                bon = getattr(old, "bonuses", {}) or {}

                hp = int(round(float(bon.get("HP", 0) or 0)))
                atk = int(round(float(bon.get("ATK", 0) or 0)))
                shd = int(round(float(bon.get("SHD", 0) or 0)))
                spd = int(round(float(bon.get("SPD", 0) or 0)))

                if hp:
                    self.player_unit.max_hp = max(1, self.player_unit.max_hp - hp)
                    self.player_unit.hp = min(self.player_unit.hp, self.player_unit.max_hp)
                if atk:
                    self.player_unit.atk = max(0, self.player_unit.atk - atk)
                if shd:
                    self.player_unit.max_shield = max(0, int(getattr(self.player_unit, "max_shield", 0)) - shd)
                    self.player_unit.shield = int(getattr(self.player_unit, "max_shield", 0))
                if spd:
                    self.player_unit.speed = max(0, self.player_unit.speed - spd)

                self.logs.append(f"Retiré : {getattr(old, 'name', '?')}")
                equip_item(self.equipment, self.player_unit, proto, self.logs)

        # 3) Fin selon la source
        if src == 'SHOP':
            ev = self.pending.get('shop_event')
            self.shop_choices = [it for it in ev.shop_inventory if not getattr(it, "_sold", False)]
            if not self.shop_choices:
                ev.event_done = True
                self.state = "EXPLORE"
            else:
                self.state = "SHOP"

        elif src == 'CHEST':
            ev = self.pending.get('chest_event')
            ev.event_done = True
            self.chest_choices = []
            self.state = "EXPLORE"

        self.pending.clear()

    def begin_chest_preview(self, idx: int):
        if self.state != "CHEST":
            return
        ev = self.grid.get_event_at(self.gx, self.gy)
        if not ev or ev.etype != "CHEST" or ev.event_done:
            return

        loot = (ev.chest_choices or [])[:3]
        if not (0 <= idx < len(loot)):
            self.logs.append("Choix invalide.")
            return

        entry = loot[idx]
        proto = getattr(entry, "proto", None)
        if proto is None:
            self.logs.append("Loot invalide.")
            return

        # Cas ARME : si aucune arme équipée -> prise directe (gratuite), pas d'échange
        if getattr(proto, "slot", "accessory") == "weapon":
            if self.equipment.get("weapon") is None:
                equip_item(self.equipment, self.player_unit, proto, self.logs)
                ev.event_done = True
                self.chest_choices = []
                self.state = "EXPLORE"
                self.logs.append(f"Vous prenez: {entry.name} (gratuit).")
                return

            # Sinon, on possède déjà une arme -> menu d'échange
            self.pending = {
                'from': 'CHEST',
                'entry': entry,
                'proto': proto,
                'chest_event': ev,
                'replace_kind': 'weapon',
                'replace_index': None
            }
            self.state = "CONFIRM_REPLACE"
            return

        # Cas ACCESSOIRE
        acc = self.equipment.get("accessories", [])
        if len(acc) >= 4:
            self.pending = {
                'from': 'CHEST',
                'entry': entry,
                'proto': proto,
                'chest_event': ev,
                'replace_kind': 'accessory',
                'replace_index': None
            }
            self.state = "SELECT_DROP"
            return

        # Ajout direct, gratuit
        equip_item(self.equipment, self.player_unit, proto, self.logs)
        ev.event_done = True
        self.chest_choices = []
        self.state = "EXPLORE"
        self.logs.append(f"Vous prenez: {entry.name} (gratuit).")

    def exit_chest(self):
        if self.state != "CHEST":
            return
        ev = self.grid.get_event_at(self.gx, self.gy)
        if ev and ev.etype == "CHEST":
            ev.event_done = True  # quitter = coffre consommé, pas de retour
        self.chest_choices = []
        self.state = "EXPLORE"
        self.logs.append("Coffre fermé.")

    # vitesse tours combat
    def toggle_speed(self):
        self.turn_delay = S.FAST_TURN if abs(self.turn_delay - S.SLOW_TURN) < 0.01 else S.SLOW_TURN
        self.logs.append(f"Turn speed: {self.turn_delay:.2f}s")

    def toggle_auto(self):
        self.auto_play = not self.auto_play
        self.time_since_last_turn = 0.0
        self.logs.append(f"Auto-play {'ON' if self.auto_play else 'OFF'}")

    def _advance_combat(self, action: str) -> bool:
        cm = self.current_combat
        if self.state != "IN_COMBAT" or cm is None or cm.finished:
            return False
        before = len(cm.log)
        accepted = cm.step_turn(action)
        if not accepted:
            if action == "power" and cm.power_cooldown:
                self.logs.append(f"Frappe puissante : encore {cm.power_cooldown} tour(s) de recharge.")
            return False
        self.logs.extend(cm.log[before:])
        if cm.finished:
            self.finish_combat()
        return True

    def manual_combat_action(self, action: str) -> bool:
        if self.auto_play:
            return False
        return self._advance_combat(action)

    # -------- update --------
    def update(self, dt: float):
        # anim déplacement
        # --- animation de déplacement tuile->tuile ---
        if self.moving:
            self.move_t += dt

            # 1) Suivi du maintien : on n'autorise le chaînage que si même direction tenue assez longtemps
            if self.held_dir == self.move_dir:
                self._hold_timer += dt
                if not self._hold_eligible and self._hold_timer >= getattr(S, "HOLD_CHAIN_DELAY", 0.14):
                    self._hold_eligible = True
            else:
                # relâchée/changée -> on repart à zéro pour l’éligibilité
                self._hold_timer = 0.0
                self._hold_eligible = False

            # 2) Anticipation : remplir next_dir dans la fenêtre de fin uniquement si éligible
            early = getattr(S, "SMOOTH_CHAIN_EARLY", 0.06)
            if (self.next_dir is None and
                    self._hold_eligible and
                    self.held_dir and
                    self.move_t >= (S.TILEMOVE_DURATION - early)):
                # on tente de chaîner depuis la case d'arrivée
                dx, dy = self._dir_to_delta(self.held_dir)
                bx, by = self.move_dst
                if self.grid.can_step(bx, by, bx + dx, by + dy):
                    self.next_dir = self.held_dir

            # 3) Arrivée
            if self.move_t >= S.TILEMOVE_DURATION:
                self.gx, self.gy = self.move_dst
                just_next = self.next_dir
                self.next_dir = None
                self._arrive_on_tile()  # peut changer self.state

                if self.state == "EXPLORE" and just_next:
                    # Enchaîne immédiatement
                    self.moving = True
                    self.move_src = (self.gx, self.gy)
                    dx, dy = self._dir_to_delta(just_next)
                    nx, ny = self.gx + dx, self.gy + dy
                    if self.grid.can_step(self.gx, self.gy, nx, ny):
                        self.move_dst = (nx, ny)
                        self.move_t = 0.0
                        self.move_dir = just_next
                        # reset tracking de maintien pour le nouveau pas
                        self._hold_timer = 0.0
                        # on garde _hold_eligible = False; il se réactivera si la touche reste tenue
                        self._hold_eligible = False
                    else:
                        self.moving = False
                        self.move_t = 0.0
                        self.move_dir = None
                else:
                    self.moving = False
                    self.move_t = 0.0
                    self.move_dir = None

        # combats auto
        if self.state == "IN_COMBAT" and self.current_combat:
            if self.current_combat.finished:
                self.finish_combat()
                return
            if self.auto_play:
                self.time_since_last_turn += dt
                if self.time_since_last_turn >= self.turn_delay:
                    self.time_since_last_turn = 0.0
                    self._advance_combat("attack")
