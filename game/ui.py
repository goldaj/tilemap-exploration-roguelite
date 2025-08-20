# game/ui.py
import pygame
from .node import NodeType
import settings as stngs  # top-level settings

FONT_NAME = stngs.FONT_NAME


def draw_text(surf, s, x, y, font, color):
    surf.blit(font.render(s, True, color), (x, y))


class UI:
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        self.FONT = pygame.font.SysFont(FONT_NAME, 18)
        self.BIG = pygame.font.SysFont(FONT_NAME, 26)
        self.TITLE = pygame.font.SysFont(FONT_NAME, 34)

    def draw(self, game_state):
        # update the surface reference (in case App changed the screen)
        self.screen = game_state and self.screen or self.screen
        w, h = self.screen.get_size()
        surf = self.screen
        surf.fill(stngs.BG)
        self.draw_map(surf, game_state)
        self.draw_top_panel(surf, game_state)
        self.draw_side_panel(surf, game_state, w, h)
        self.draw_bottom_logs(surf, game_state, w, h)
        if game_state.state == "READY_COMBAT":
            self.draw_ready_overlay(surf, w, h)
        # combat/shop overlays are drawn by App for now

    def draw_map(self, surf, gs):
        """
        Draw the graph centered on the player's current node.
        The visible map area is the rectangle between the top UI panel and the bottom logs area.
        """
        w, h = surf.get_size()
        # layout constants (must be consistent with App / top panel / bottom logs)
        panel_top_h = 110  # hauteur du panneau supérieur (same as in app.py)
        panel_bottom_h = 120  # hauteur zone logs en bas

        map_top = panel_top_h
        map_bottom = h - panel_bottom_h

        # centre de la zone de jeu (où on veut placer le joueur)
        center_x = w // 2
        center_y = (map_top + map_bottom) // 2

        # compute camera offset so player_node maps to (center_x, center_y)
        player_node = gs.map.nodes[gs.player_node]
        offset_x = center_x - player_node.x
        offset_y = center_y - player_node.y

        # draw edges (with offset)
        for a, b in gs.map.edges:
            n1, n2 = gs.map.nodes[a], gs.map.nodes[b]
            x1, y1 = n1.x + offset_x, n1.y + offset_y
            x2, y2 = n2.x + offset_x, n2.y + offset_y
            pygame.draw.line(surf, stngs.EDGE_COL, (x1, y1), (x2, y2), 3)

        # draw nodes (with offset)
        for nid, node in gs.map.nodes.items():
            nx, ny = node.x + offset_x, node.y + offset_y
            col = stngs.EMPTY_COL
            if node.ntype == NodeType.ENCOUNTER: col = stngs.EN_COL
            if node.ntype == NodeType.SHOP: col = stngs.SHOP_COL
            if node.ntype == NodeType.BOSS: col = stngs.BOSS_COL
            if node.ntype == NodeType.START: col = stngs.ACCENT
            # outline
            pygame.draw.circle(surf, (8, 8, 8), (int(nx), int(ny)), stngs.NODE_RADIUS + 3)
            pygame.draw.circle(surf, col, (int(nx), int(ny)), stngs.NODE_RADIUS)
            if node.visited:
                pygame.draw.circle(surf, (18, 18, 18), (int(nx), int(ny)), stngs.NODE_RADIUS - 8)
        # draw selected neighbor highlight (with offset)
        if gs.selected_neighbor is not None:
            sel = gs.map.nodes[gs.selected_neighbor]
            sx, sy = sel.x + offset_x, sel.y + offset_y
            pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), stngs.NODE_RADIUS + 2, 2)

        # draw player marker at the exact center of the map-area (visual player)
        pygame.draw.circle(surf, stngs.HIGHLIGHT, (center_x, center_y), stngs.NODE_RADIUS + 8, 4)
        # inner player square to match previous aesthetic
        rect_w = 36
        rect_h = 36
        pygame.draw.rect(surf, (0, 0, 0),
                         (center_x - rect_w // 2 - 2, center_y - rect_h // 2 - 2, rect_w + 4, rect_h + 4))
        pygame.draw.rect(surf, stngs.PLAYER_COL, (center_x - rect_w // 2, center_y - rect_h // 2, rect_w, rect_h))

    def draw_top_panel(self, surf, gs):
        w, h = surf.get_size()
        panel_h = 110
        pygame.draw.rect(surf, stngs.PANEL, (0, 0, w, panel_h))
        draw_text(surf, "HeIsComing-like v3 (modulaire) — caméra centrée", 10, 6, self.TITLE, stngs.ACCENT)
        draw_text(surf, f"HP: {int(gs.player_unit.hp)}/{int(gs.player_unit.max_hp)}", 10, 56, self.BIG, stngs.WHITE)
        draw_text(surf,
                  f"ATK: {gs.player_unit.atk:.1f}  DEF: {gs.player_unit.defense:.1f}  SPD: {gs.player_unit.speed:.2f}",
                  220, 56, self.BIG, stngs.WHITE)
        draw_text(surf, f"Visited distinct nodes: {gs.nodes_visited_count}", 10, 90, self.FONT, stngs.WHITE)
        draw_text(surf, f"State: {gs.state}", 320, 90, self.FONT, stngs.WHITE)

    def draw_side_panel(self, surf, gs, w, h):
        panel_h = 110
        bx = w - 340
        pygame.draw.rect(surf, stngs.PANEL, (bx, panel_h, 340, h - panel_h - 120))
        draw_text(surf, "Node Info", bx + 12, panel_h + 8, self.BIG, stngs.WHITE)
        node = gs.map.nodes[gs.player_node]
        draw_text(surf, f"ID: {node.id}", bx + 12, panel_h + 48, self.FONT, stngs.WHITE)
        draw_text(surf, f"Type: {node.ntype}", bx + 12, panel_h + 68, self.FONT, stngs.WHITE)
        draw_text(surf, f"Visited: {node.visited}", bx + 12, panel_h + 88, self.FONT, stngs.WHITE)
        draw_text(surf, "Neighbors:", bx + 12, panel_h + 116, self.FONT, stngs.WHITE)
        for i, n in enumerate(gs.map.neighbors(gs.player_node)):
            nn = gs.map.nodes[n]
            draw_text(surf, f" - [{n}] {nn.ntype} {'(v)' if nn.visited else ''}", bx + 32, panel_h + 140 + i * 20,
                      self.FONT, stngs.WHITE)

    def draw_bottom_logs(self, surf, gs, w, h):
        pygame.draw.rect(surf, (18, 18, 18), (0, h - 120, w, 120))
        draw_text(surf, "LOGS:", 8, h - 116, self.BIG, stngs.WHITE)
        lines = gs.logs[-6:]
        for i, ln in enumerate(lines):
            draw_text(surf, ln, 12, h - 88 + i * 18, self.FONT, stngs.WHITE)

    def draw_ready_overlay(self, surf, w, h):
        box_w, box_h = 560, 140
        bx = w // 2 - box_w // 2
        by = h // 2 - box_h - 40
        pygame.draw.rect(surf, stngs.PANEL, (bx, by, box_w, box_h))
        draw_text(surf, "Salle ENCOUNTER - PRÊT ?", bx + 18, by + 12, self.BIG, stngs.WHITE)
        draw_text(surf, "Appuie sur SPACE pour démarrer le combat (ou déplace-toi ailleurs).", bx + 18, by + 56,
                  self.FONT, stngs.WHITE)
