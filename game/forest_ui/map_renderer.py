# game/forest_ui/map_renderer.py
import os
import pygame
import settings as S

_THIS_DIR = os.path.dirname(__file__)
ASSET_DIR_V2 = os.path.join(_THIS_DIR, "assets", "forest_tiles_v2")
ASSET_DIR_V1 = os.path.join(_THIS_DIR, "assets", "forest_tiles")
MARKERS_DIR = os.path.join(_THIS_DIR, "assets", "markers")

# Taille logique (grille / gameplay)
TILE_SIZE = S.TILE_SIZE
# Taille affichée (zoom appliqué)
RENDER_TILE_SIZE = max(8, int(round(S.TILE_SIZE * getattr(S, "MAP_ZOOM", 1.0))))

_TILE_CACHE = None
_MARKER_CACHE = None

_KEYS = [
    "none",
    "N", "E", "S", "W",
    "NS", "EW", "NE", "NW", "SE", "SW",
    "NES", "NEW", "NSW", "ESW",
    "NESW"
]


def connectivity_key(north: bool, east: bool, south: bool, west: bool) -> str:
    s = frozenset(d for d, ok in (("N", north), ("E", east), ("S", south), ("W", west)) if ok)
    if not s: return "none"
    if s == frozenset({"N"}): return "N"
    if s == frozenset({"E"}): return "E"
    if s == frozenset({"S"}): return "S"
    if s == frozenset({"W"}): return "W"
    if s == frozenset({"N", "S"}): return "NS"
    if s == frozenset({"E", "W"}): return "EW"
    if s == frozenset({"N", "E"}): return "NE"
    if s == frozenset({"N", "W"}): return "NW"
    if s == frozenset({"S", "E"}): return "SE"
    if s == frozenset({"S", "W"}): return "SW"
    if s == frozenset({"N", "E", "S"}): return "NES"
    if s == frozenset({"N", "E", "W"}): return "NEW"
    if s == frozenset({"N", "S", "W"}): return "NSW"
    if s == frozenset({"E", "S", "W"}): return "ESW"
    if s == frozenset({"N", "E", "S", "W"}): return "NESW"
    return "none"


def _load_tile_set_from(folder):
    tiles = {}
    for k in _KEYS:
        fn = f"tile_{k}.png"
        path = os.path.join(folder, fn)
        if not os.path.isfile(path):
            continue
        img = pygame.image.load(path).convert_alpha()
        # IMPORTANT : nearest-neighbor pour garder le pixel art net
        tiles[k] = pygame.transform.scale(img, (RENDER_TILE_SIZE, RENDER_TILE_SIZE))
    if "none" not in tiles:
        surf = pygame.Surface((RENDER_TILE_SIZE, RENDER_TILE_SIZE), pygame.SRCALPHA)
        surf.fill((26, 49, 36))
        tiles["none"] = surf
    return tiles


def load_tiles():
    global _TILE_CACHE
    if _TILE_CACHE is not None:
        return _TILE_CACHE
    if os.path.isdir(ASSET_DIR_V2):
        tiles = _load_tile_set_from(ASSET_DIR_V2)
    else:
        tiles = _load_tile_set_from(ASSET_DIR_V1)
    none_tile = tiles.get("none")
    for k in _KEYS:
        if k not in tiles:
            tiles[k] = none_tile
    _TILE_CACHE = tiles
    print(f"[tiles] loaded {len(tiles)} tiles (render size {RENDER_TILE_SIZE}px)")
    return _TILE_CACHE


def load_markers():
    """Retourne dict {'encounter':surf, 'shop':surf, 'boss':surf} redimensionnés selon le zoom."""
    global _MARKER_CACHE
    if _MARKER_CACHE is not None:
        return _MARKER_CACHE

    d = {}
    # facteur de zoom
    z = max(1.0, getattr(S, "MAP_ZOOM", 1.0))
    m = max(0.1, getattr(S, "MARKER_SCALE", 1.0))
    scale = max(0.5, min(4.0, z * m))  # clamp pour éviter l’énorme ou minuscule

    def try_load(name, key):
        p = os.path.join(MARKERS_DIR, name)
        if os.path.isfile(p):
            img = pygame.image.load(p).convert_alpha()
            if abs(scale - 1.0) > 1e-3:
                w, h = img.get_size()
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                img = pygame.transform.scale(img, (nw, nh))  # nearest neighbor (net pour pixel art)
            d[key] = img

    try_load("marker_encounter.png", "encounter")
    try_load("marker_shop.png", "shop")
    try_load("marker_boss.png", "boss")
    try_load("marker_chest.png", "chest")

    _MARKER_CACHE = d
    print(f"[markers] loaded & scaled x{scale:.2f}")
    return _MARKER_CACHE


def render_grid(surface, grid, offset_px=(0, 0)):
    tiles = load_tiles()
    ox, oy = offset_px
    for gy, row in enumerate(grid):
        for gx, conns in enumerate(row):
            if conns is None:
                key = "none"
            else:
                key = connectivity_key(conns.get("N", False), conns.get("E", False),
                                       conns.get("S", False), conns.get("W", False))
            surface.blit(tiles[key], (ox + gx * RENDER_TILE_SIZE, oy + gy * RENDER_TILE_SIZE))
