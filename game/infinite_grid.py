# game/infinite_grid.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List
import random
import settings as S
from .node import NodeType  # on réutilise l'Enum existant pour ENCOUNTER/SHOP

# --- Modèle d'événement attaché à une tuile ---
@dataclass
class TileEvent:
    etype: str                     # "ENCOUNTER" | "SHOP"
    visited: bool = False          # déjà foulée au moins une fois
    event_done: bool = False       # consommé (combat fait) ; SHOP reste False
    shop_inventory: Optional[object] = None  # liste de ShopEntry (persistante par tuile)
    chest_choices: Optional[list] = None # les coffres

# --- Chunk de N x N tuiles ---
@dataclass
class Chunk:
    cx: int
    cy: int
    size: int
    cells: List[List[Optional[Dict[str,bool]]]] = field(default_factory=list)  # dict N/E/S/W ou None (forêt)
    events: Dict[Tuple[int,int], TileEvent] = field(default_factory=dict)      # (tx,ty) -> TileEvent

class InfiniteGrid:
    """
    Monde infini carrelé par chunks. Chaque cell est:
      - None : forêt (non praticable)
      - dict {'N','E','S','W': bool} : chemins praticables
    Propriétés:
      - Chaque chunk a au moins 1 sortie par bord => jamais enfermé
      - Couture bord à bord: on s'aligne sur les ouvertures des chunks voisins
      - Événements (ENCOUNTER/SHOP) posés sur certaines cases de chemin
    """
    def __init__(self, tile_size: int = 64, chunk_size: int = 24, world_seed: int = 1337):
        self.tile_size = tile_size
        self.chunk_size = chunk_size
        self.world_seed = int(world_seed)
        self.rng = random.Random(world_seed)
        self.chunks: Dict[Tuple[int,int], Chunk] = {}

    # ---------- Helpers coords ----------
    def _div_floor(self, a:int, b:int) -> Tuple[int,int]:
        # floor division compatible négatifs
        q = a // b
        r = a - q*b
        if r < 0:
            q -= 1
            r += b
        return q, r

    def tile_to_chunk(self, gx:int, gy:int) -> Tuple[int,int,int,int]:
        cx, tx = self._div_floor(gx, self.chunk_size)
        cy, ty = self._div_floor(gy, self.chunk_size)
        return cx, cy, tx, ty

    # ---------- Cell API ----------
    def get_cell(self, gx:int, gy:int) -> Optional[Dict[str,bool]]:
        ch = self._ensure_chunk_for_tile(gx, gy)
        _, _, tx, ty = self.tile_to_chunk(gx, gy)
        return ch.cells[ty][tx]

    def can_step(self, gx:int, gy:int, nx:int, ny:int) -> bool:
        if abs(nx-gx) + abs(ny-gy) != 1:
            return False
        cur = self.get_cell(gx, gy)
        nxt = self.get_cell(nx, ny)
        if cur is None or nxt is None:
            return False
        if nx == gx + 1:
            return cur.get('E',False) and nxt.get('W',False)
        if nx == gx - 1:
            return cur.get('W',False) and nxt.get('E',False)
        if ny == gy + 1:
            return cur.get('S',False) and nxt.get('N',False)
        if ny == gy - 1:
            return cur.get('N',False) and nxt.get('S',False)
        return False

    # ---------- Events ----------
    def get_event_at(self, gx:int, gy:int) -> Optional[TileEvent]:
        ch = self._ensure_chunk_for_tile(gx, gy)
        _, _, tx, ty = self.tile_to_chunk(gx, gy)
        return ch.events.get((tx,ty))

    # ---------- Fenêtre pour rendu ----------
    def window(self, center_gx:int, center_gy:int, rx:int, ry:int) -> Tuple[List[List[Optional[Dict[str,bool]]]], int, int]:
        """
        Retourne (grid2D, origin_gx, origin_gy) pour un rectangle centré sur (center_gx, center_gy)
        de demi-taille rx, ry (inclus). Taille = (2*rx+1, 2*ry+1).
        """
        cols = 2*rx + 1
        rows = 2*ry + 1
        ogx = center_gx - rx
        ogy = center_gy - ry
        grid = [[None for _ in range(cols)] for __ in range(rows)]
        for j in range(rows):
            gy = ogy + j
            for i in range(cols):
                gx = ogx + i
                grid[j][i] = self.get_cell(gx, gy)
        return grid, ogx, ogy

    def events_in_rect(self, ogx:int, ogy:int, cols:int, rows:int) -> List[Tuple[int,int,TileEvent]]:
        out = []
        for j in range(rows):
            for i in range(cols):
                gx, gy = ogx + i, ogy + j
                ev = self.get_event_at(gx, gy)
                if ev is not None:
                    out.append((gx, gy, ev))
        return out

    # ---------- Génération lazy ----------
    def _ensure_chunk_for_tile(self, gx:int, gy:int) -> Chunk:
        cx, cy, _, _ = self.tile_to_chunk(gx, gy)
        key = (cx, cy)
        ch = self.chunks.get(key)
        if ch is None:
            ch = self._generate_chunk(cx, cy)
            self.chunks[key] = ch
            # Coudre avec voisins existants (sécurité)
            self._stitch_neighbors(cx, cy)
        return ch

    def _generate_chunk(self, cx: int, cy: int) -> Chunk:
        N = self.chunk_size
        ch = Chunk(cx, cy, N, [[None for _ in range(N)] for __ in range(N)], {})
        # RNG déterministe par chunk
        rng = random.Random((self.world_seed * 73856093) ^ (cx * 19349663) ^ (cy * 83492791))

        # ---------- 1) Portes aux bords (couture avec voisins si présents) ----------
        portals = {"N": set(), "E": set(), "S": set(), "W": set()}

        def inherit_from_neighbor(ncx, ncy, side_from_neighbor, side_here):
            nb = self.chunks.get((ncx, ncy))
            if not nb: return
            Nn = nb.size
            if side_from_neighbor == "E":
                for y in range(Nn):
                    cell = nb.cells[y][Nn - 1]
                    if cell and cell.get('E', False):
                        portals[side_here].add(y)
            elif side_from_neighbor == "W":
                for y in range(Nn):
                    cell = nb.cells[y][0]
                    if cell and cell.get('W', False):
                        portals[side_here].add(y)
            elif side_from_neighbor == "S":
                for x in range(Nn):
                    cell = nb.cells[Nn - 1][x]
                    if cell and cell.get('S', False):
                        portals[side_here].add(x)
            elif side_from_neighbor == "N":
                for x in range(Nn):
                    cell = nb.cells[0][x]
                    if cell and cell.get('N', False):
                        portals[side_here].add(x)

        inherit_from_neighbor(cx, cy - 1, "S", "N")
        inherit_from_neighbor(cx + 1, cy, "W", "E")
        inherit_from_neighbor(cx, cy + 1, "N", "S")
        inherit_from_neighbor(cx - 1, cy, "E", "W")

        def ensure_min_portals():
            for side in ("N", "E", "S", "W"):
                if not portals[side]:
                    count = 1 if rng.random() < 0.7 else 2
                    if side in ("N", "S"):
                        for _ in range(count):
                            portals[side].add(rng.randrange(2, N - 2))
                    else:
                        for _ in range(count):
                            portals[side].add(rng.randrange(2, N - 2))

        ensure_min_portals()

        # ---------- helpers de carving ----------
        def cell(x: int, y: int) -> Dict[str, bool]:
            c = ch.cells[y][x]
            if c is None:
                c = {'N': False, 'E': False, 'S': False, 'W': False}
                ch.cells[y][x] = c
            return c

        def neighbor(x: int, y: int, d: str):
            if d == 'N': return x, y - 1
            if d == 'S': return x, y + 1
            if d == 'E': return x + 1, y
            if d == 'W': return x - 1, y
            return x, y

        def opposite(d: str) -> str:
            return {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[d]

        def open_between(x: int, y: int, d: str):
            nx, ny = neighbor(x, y, d)
            if 0 <= nx < N and 0 <= ny < N:
                a = cell(x, y);
                b = cell(nx, ny)
                a[d] = True;
                b[opposite(d)] = True

        def link(ax: int, ay: int, bx: int, by: int):
            # chemin Manhattan (horizontal puis vertical)
            x, y = ax, ay
            step_x = 1 if bx > x else -1
            while x != bx:
                open_between(x, y, 'E' if step_x == 1 else 'W')
                x += step_x
            step_y = 1 if by > y else -1
            while y != by:
                open_between(x, y, 'S' if step_y == 1 else 'N')
                y += step_y

        def degree(x: int, y: int) -> int:
            c = ch.cells[y][x]
            return 0 if c is None else int(c.get('N', 0)) + int(c.get('E', 0)) + int(c.get('S', 0)) + int(c.get('W', 0))

        # ---------- 2) Connexions principales (hub) ----------
        hubx, huby = N // 2, N // 2
        # Connecter chaque ouverture de bord au hub
        for x in portals['N']:
            link(x, 0, hubx, huby);
            cell(x, 0)['N'] = True
        for x in portals['S']:
            link(x, N - 1, hubx, huby);
            cell(x, N - 1)['S'] = True
        for y in portals['W']:
            link(0, y, hubx, huby);
            cell(0, y)['W'] = True
        for y in portals['E']:
            link(N - 1, y, hubx, huby);
            cell(N - 1, y)['E'] = True

        # ---------- 3) Branches supplémentaires (densifie) ----------
        # (plus qu'avant, pour casser l'effet tunnel)
        for _ in range(rng.randint(6, 10)):
            x1, y1 = rng.randrange(1, N - 1), rng.randrange(1, N - 1)
            x2, y2 = rng.randrange(1, N - 1), rng.randrange(1, N - 1)
            link(x1, y1, x2, y2)

        # ---------- 4) Graines de carrefours 3/4 voies (intérieur uniquement) ----------
        for _ in range(rng.randint(N // 2, N)):  # ~12–24 sur un chunk 24
            x = rng.randrange(2, N - 2);
            y = rng.randrange(2, N - 2)
            cell(x, y)
            dirs = list("NESW");
            rng.shuffle(dirs)
            target_deg = 4 if rng.random() < 0.35 else 3  # favorise 3 et 4 voies
            for d in dirs[:target_deg]:
                nx, ny = neighbor(x, y, d)
                if 1 <= nx < N - 1 and 1 <= ny < N - 1:
                    open_between(x, y, d)

        # ---------- 5) Réduction des culs-de-sac ----------
        for y in range(1, N - 1):
            for x in range(1, N - 1):
                if degree(x, y) == 1 and rng.random() < 0.95:
                    # ajoute une ouverture supplémentaire (évite dead-ends)
                    c = ch.cells[y][x]
                    if c is None: continue
                    dirs = [d for d in "NESW" if not c.get(d, False)]
                    rng.shuffle(dirs)
                    for d in dirs:
                        nx, ny = neighbor(x, y, d)
                        if 1 <= nx < N - 1 and 1 <= ny < N - 1:
                            open_between(x, y, d)
                            break

        # ---------- 6) Convertir lignes droites en T de temps en temps ----------
        for y in range(1, N - 1):
            for x in range(1, N - 1):
                c = ch.cells[y][x]
                if not c: continue
                straight_NS = c.get('N') and c.get('S') and not (c.get('E') or c.get('W'))
                straight_EW = c.get('E') and c.get('W') and not (c.get('N') or c.get('S'))
                if (straight_NS or straight_EW) and rng.random() < 0.65:
                    dirs = ['E', 'W'] if straight_NS else ['N', 'S']
                    d = rng.choice(dirs)
                    nx, ny = neighbor(x, y, d)
                    if 1 <= nx < N - 1 and 1 <= ny < N - 1:
                        open_between(x, y, d)

        # ---------- 6bis) Promotion des degrés vers 3/4 voies ----------
        # Paramètres de tuning
        PROMOTE_ONE_PROB = 0.90  # prob d'améliorer un degré 1
        PROMOTE_TWO_PROB = 0.55  # prob d'améliorer un degré 2
        P_TARGET4_FROM1 = 0.25  # part des degré-1 poussés jusqu'à 4 (sinon 3)
        P_TARGET4_FROM2 = 0.12  # part des degré-2 poussés jusqu'à 4 (sinon 3)

        def _candidate_dirs(x: int, y: int):
            """Directions encore fermées, à l'intérieur du chunk."""
            c = ch.cells[y][x]
            if not c: return []
            ds = []
            for d in "NESW":
                if c.get(d, False):
                    continue
                nx, ny = neighbor(x, y, d)
                if 1 <= nx < N - 1 and 1 <= ny < N - 1:
                    ds.append(d)
            rng.shuffle(ds)
            return ds

        # A) Promouvoir la plupart des degré-1 vers 3 (parfois 4)
        for y in range(1, N - 1):
            for x in range(1, N - 1):
                if ch.cells[y][x] is None:
                    continue
                if degree(x, y) == 1 and rng.random() < PROMOTE_ONE_PROB:
                    target = 4 if rng.random() < P_TARGET4_FROM1 else 3
                    for d in _candidate_dirs(x, y):
                        if degree(x, y) >= target:
                            break
                        open_between(x, y, d)

        # B) Promouvoir une partie des degré-2 vers 3 (parfois 4)
        for y in range(1, N - 1):
            for x in range(1, N - 1):
                if ch.cells[y][x] is None:
                    continue
                if degree(x, y) == 2 and rng.random() < PROMOTE_TWO_PROB:
                    target = 4 if rng.random() < P_TARGET4_FROM2 else 3
                    for d in _candidate_dirs(x, y):
                        if degree(x, y) >= target:
                            break
                        open_between(x, y, d)

        # ---------- 7) Placement d'événements plus fréquent ----------
        # Sélection sur les chemins intérieurs, densité ~8–12% des cases de chemin (clampée 7–12)
        path_cells = []
        for yy in range(2, N - 2):
            for xx in range(2, N - 2):
                if ch.cells[yy][xx] is not None:
                    path_cells.append((xx, yy))
        rng.shuffle(path_cells)

        base = max(7, min(12, int(len(path_cells) * 0.10)))  # densité “de base”
        k = min(len(path_cells), base * 3)  # ➜ 3x plus d’événements
        for i in range(min(k, len(path_cells))):
            x, y = path_cells[i]
            r = rng.random()
            if r < 0.25:
                etype = "CHEST"  # ~25%
            elif r < 0.45:
                etype = "SHOP"  # ~25%
            else:
                etype = "ENCOUNTER"  # ~50%
            ch.events[(x, y)] = TileEvent(etype=etype)

        return ch

    def _stitch_neighbors(self, cx: int, cy: int):
        """Assure la continuité des liaisons avec tous les voisins déjà générés."""
        N = self.chunk_size
        me = self.chunks[(cx, cy)]

        def cell(ch: Chunk, x: int, y: int) -> Dict[str, bool]:
            c = ch.cells[y][x]
            if c is None:
                c = {'N': False, 'E': False, 'S': False, 'W': False}
                ch.cells[y][x] = c
            return c

        # --- gauche (cx-1, cy) ---
        left = self.chunks.get((cx - 1, cy))
        if left:
            for y in range(N):
                a = left.cells[y][N - 1]
                b = me.cells[y][0]
                if a and a.get('E', False):
                    bb = cell(me, 0, y);
                    bb['W'] = True
                    aa = cell(left, N - 1, y);
                    aa['E'] = True
                if b and b.get('W', False):
                    aa = cell(left, N - 1, y);
                    aa['E'] = True
                    bb = cell(me, 0, y);
                    bb['W'] = True

        # --- droite (cx+1, cy) ---
        right = self.chunks.get((cx + 1, cy))
        if right:
            for y in range(N):
                a = me.cells[y][N - 1]
                b = right.cells[y][0]
                if a and a.get('E', False):
                    bb = cell(right, 0, y);
                    bb['W'] = True
                    aa = cell(me, N - 1, y);
                    aa['E'] = True
                if b and b.get('W', False):
                    aa = cell(me, N - 1, y);
                    aa['E'] = True
                    bb = cell(right, 0, y);
                    bb['W'] = True

        # --- haut (cx, cy-1) ---
        up = self.chunks.get((cx, cy - 1))
        if up:
            for x in range(N):
                a = up.cells[N - 1][x]
                b = me.cells[0][x]
                if a and a.get('S', False):
                    bb = cell(me, x, 0);
                    bb['N'] = True
                    aa = cell(up, x, N - 1);
                    aa['S'] = True
                if b and b.get('N', False):
                    aa = cell(up, x, N - 1);
                    aa['S'] = True
                    bb = cell(me, x, 0);
                    bb['N'] = True

        # --- bas (cx, cy+1) ---
        down = self.chunks.get((cx, cy + 1))
        if down:
            for x in range(N):
                a = me.cells[N - 1][x]
                b = down.cells[0][x]
                if a and a.get('S', False):
                    bb = cell(down, x, 0);
                    bb['N'] = True
                    aa = cell(me, x, N - 1);
                    aa['S'] = True
                if b and b.get('N', False):
                    aa = cell(me, x, N - 1);
                    aa['S'] = True
                    bb = cell(down, x, 0);
                    bb['N'] = True
