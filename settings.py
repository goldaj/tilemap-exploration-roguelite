# settings.py
# Centralise les paramètres modifiables

INITIAL_W, INITIAL_H = 1100, 720
FPS = 60
NODE_COUNT = 14
START_GOLD = 0

# Combat speeds (s per turn)
SLOW_TURN = 0.9
FAST_TURN = 0.12

# Visuals / colors
BG = (16, 16, 20)
PANEL = (28, 28, 32)
WHITE = (235, 235, 235)
ACCENT = (220, 180, 50)
PLAYER_COL = (70, 200, 130)
EN_COL = (200, 80, 80)
BOSS_COL = (170, 90, 190)
SHOP_COL = (80, 140, 220)
EMPTY_COL = (110, 110, 120)
EDGE_COL = (60, 60, 70)
HIGHLIGHT = (240, 220, 120)

FONT_NAME = "consolas"
NODE_RADIUS = 24

# --- Tilemap UI ---
USE_TILEMAP_UI = True
TILE_SIZE = 64
PANEL_TOP_H = 110
PANEL_BOTTOM_H = 120
# Taille logique de la tuile = 64 px (ne pas changer si tes assets sont 64x64)
# MAP_ZOOM > 1.0 => on affiche la tuile plus grosse à l'écran (on voit moins de tuiles)
MAP_ZOOM = 1.75  # essaie 1.5 à 2.0 si tu veux plus/moins de zoom


# --- Déplacement tuile->tuile ---
TILEMOVE_DURATION = 0.18     # 0.22 -> 0.18 un peu plus vif
MOVE_EASING = "ease_in_out"  # "linear" ou "ease_in_out"
# Répétition clavier (maintenir une flèche pour enchaîner)
INPUT_HOLD_DELAY = 0.18      # délai avant répétition
INPUT_HOLD_INTERVAL = 0.10   # intervalle entre répétitions
# (Facultatif) si tu veux une caméra encore plus "fluide", je peux ajouter un CAMERA_LERP
# Anticipation du prochain pas (en secondes avant la fin du déplacement)
SMOOTH_CHAIN_EARLY = 0.06     # fenêtre d’anticipation avant la fin du pas
HOLD_CHAIN_DELAY   = 0.14     # durée minimale de maintien pour autoriser le chaînage

# --- Markers overlays ---
SHOW_MARKERS = True
MARKER_SCALE = 2.2   # >1.0 = plus gros que les tuiles ; essaye 1.8–2.6 selon ton goût

# --- Monde / seed ---
# Mettre un entier pour un monde fixe (ex: 1337), "random" pour un monde différent à chaque run,
# ou "daily" pour un monde qui change chaque jour (même seed toute la journée).
WORLD_SEED = "random"   # "random" | "daily" | int

# Tous les X événements découverts, un boss apparaît
BOSS_INTERVAL_NODES = 5

# --- Player sprite ---
PLAYER_TILE_RATIO = 0.6          # ~2/3 d'une tuile (modifie ici si besoin)
PLAYER_TRIM_TRANSPARENT = True    # rogne les marges vides éventuelles du PNG

