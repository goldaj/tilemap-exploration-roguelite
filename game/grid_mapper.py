# game/grid_mapper.py
from typing import Dict, Tuple, List, Optional
from .world import MapGraph

class GridMapper:
    """
    Construit une grille normalisée à partir du graphe:
      - Place chaque node sur une cellule de grille (gx, gy).
      - 'Creuse' des corridors Manhattan entre nodes reliés (N/E/S/W).
    Fournit:
      - grid[gy][gx] -> dict {'N','E','S','W'} ou None (forêt sans chemin)
      - can_step(gx,gy,nx,ny) : pas autorisé si et seulement si les DEUX cells ont la connexion opposée.
      - node_grid(nid) : (gx,gy) normalisés
      - node_at(gx,gy) : id du node présent sur cette cell (ou None)
    """
    def __init__(self, tile_size: int = 64):
        if tile_size <= 0:
            raise ValueError("tile_size must be positive")
        self.tile = tile_size
        self.pos_by_id: Dict[int, Tuple[int,int]] = {}
        self.min_gx = self.min_gy = 0
        self.max_gx = self.max_gy = 0
        self.cols = self.rows = 0
        self.grid: List[List[Optional[Dict[str,bool]]]] = []
        self._grid_to_node: Dict[Tuple[int,int], int] = {}

    # ---------- placement de base ----------
    def _world_to_grid_guess(self, x:int, y:int) -> Tuple[int,int]:
        return round(x / self.tile), round(y / self.tile)

    def _place_unique(self, gx:int, gy:int, used:set) -> Tuple[int,int]:
        if (gx,gy) not in used: return gx,gy
        spiral = [(0,0),(1,0),(0,1),(-1,0),(0,-1),(2,0),(0,2),(-2,0),(0,-2),
                  (1,1),(-1,1),(1,-1),(-1,-1),(3,0),(0,3),(-3,0),(0,-3)]
        for dx,dy in spiral:
            p=(gx+dx, gy+dy)
            if p not in used: return p
        r=4
        while True:
            for dx in range(-r, r+1):
                for dy in range(-r, r+1):
                    p=(gx+dx, gy+dy)
                    if p not in used: return p
            r += 1

    # ---------- helpers grille ----------
    def _alloc_grid(self):
        self.cols = self.max_gx - self.min_gx + 1
        self.rows = self.max_gy - self.min_gy + 1
        self.grid = [[None for _ in range(self.cols)] for __ in range(self.rows)]
        self._grid_to_node.clear()

    def _cell(self, gx:int, gy:int) -> Dict[str,bool]:
        gi = gy - self.min_gy
        gj = gx - self.min_gx
        cell = self.grid[gi][gj]
        if cell is None:
            cell = {'N':False,'E':False,'S':False,'W':False}
            self.grid[gi][gj] = cell
        return cell

    def _link_adjacent(self, x1:int, y1:int, x2:int, y2:int):
        """Relie deux cells adjacentes (distance Manhattan=1)."""
        a = self._cell(x1, y1)
        b = self._cell(x2, y2)
        if x2 == x1 + 1:  # Est
            a['E'] = True; b['W'] = True
        elif x2 == x1 - 1:  # Ouest
            a['W'] = True; b['E'] = True
        elif y2 == y1 + 1:  # Sud
            a['S'] = True; b['N'] = True
        elif y2 == y1 - 1:  # Nord
            a['N'] = True; b['S'] = True

    def _carve_corridor(self, ax:int, ay:int, bx:int, by:int):
        """Corridor en L (horizontal puis vertical) entre (ax,ay) et (bx,by)."""
        x,y = ax, ay
        step_x = 1 if bx > x else -1
        while x != bx:
            nx, ny = x + step_x, y
            self._link_adjacent(x,y,nx,ny)
            x, y = nx, ny
        step_y = 1 if by > y else -1
        while y != by:
            nx, ny = x, y + step_y
            self._link_adjacent(x,y,nx,ny)
            x, y = nx, ny

    # ---------- API ----------
    def rebuild(self, gmap: MapGraph):
        used=set()
        self.pos_by_id.clear()
        if not gmap.nodes:
            self.min_gx = self.min_gy = 0
            self.max_gx = self.max_gy = 0
            self.cols = self.rows = 0
            self.grid = []
            self._grid_to_node.clear()
            return
        # 1) places
        for nid, node in gmap.nodes.items():
            gx, gy = self._world_to_grid_guess(node.x, node.y)
            gx, gy = self._place_unique(gx, gy, used)
            used.add((gx,gy))
            self.pos_by_id[nid] = (gx, gy)
        # 2) bbox
        self.min_gx = min(g for g,_ in self.pos_by_id.values())
        self.max_gx = max(g for g,_ in self.pos_by_id.values())
        self.min_gy = min(g for _,g in self.pos_by_id.values())
        self.max_gy = max(g for _,g in self.pos_by_id.values())
        # 3) grid
        self._alloc_grid()
        # 4) corridors pour chaque arête
        for nid, (gx,gy) in self.pos_by_id.items():
            for vid in gmap.neighbors(nid):
                if vid < nid:  # éviter doublons
                    continue
                ngx, ngy = self.pos_by_id[vid]
                self._carve_corridor(gx, gy, ngx, ngy)
        # 5) mapping cell -> node (normalisé)
        for nid, (gx,gy) in self.pos_by_id.items():
            self._grid_to_node[(gx - self.min_gx, gy - self.min_gy)] = nid

    def can_step(self, gx:int, gy:int, nx:int, ny:int) -> bool:
        """Autorise le pas si les 2 cells ont la sortie/entrée opposée."""
        if abs(nx-gx) + abs(ny-gy) != 1: return False
        if not (0 <= gx < self.cols and 0 <= gy < self.rows): return False
        if not (0 <= nx < self.cols and 0 <= ny < self.rows): return False
        cur = self.grid[gy][gx]
        nxt = self.grid[ny][nx]
        if cur is None or nxt is None:
            return False
        if nx == gx + 1:   # E
            return cur['E'] and nxt['W']
        if nx == gx - 1:   # W
            return cur['W'] and nxt['E']
        if ny == gy + 1:   # S
            return cur['S'] and nxt['N']
        if ny == gy - 1:   # N
            return cur['N'] and nxt['S']
        return False

    def node_grid(self, nid:int) -> Tuple[int,int]:
        gx, gy = self.pos_by_id[nid]
        return gx - self.min_gx, gy - self.min_gy

    def node_at(self, gx:int, gy:int) -> Optional[int]:
        return self._grid_to_node.get((gx,gy))
