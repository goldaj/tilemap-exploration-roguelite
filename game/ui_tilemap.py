# game/ui_tilemap.py
import pygame
import settings as S
from .node import NodeType
from .items import format_bonuses
from .forest_ui.map_renderer import render_grid, load_markers, RENDER_TILE_SIZE


def draw_text(surf, s, x, y, font, color):
    surf.blit(font.render(s, True, color), (x, y))


class UITilemap:
    RIGHT_PANEL_W = 340

    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        self.FONT = pygame.font.SysFont(S.FONT_NAME, 18)
        self.BIG = pygame.font.SysFont(S.FONT_NAME, 26)
        self.TITLE = pygame.font.SysFont(S.FONT_NAME, 34)
        self.markers = load_markers()  # {'encounter':surf, 'shop':surf, 'boss':surf}

        # état d’affichage du panneau de droite
        self.right_panel_visible = True
        self._btn_right_toggle_rect = None  # rect cliquable du bouton

        # upscale markers selon le zoom (facultatif)
        z = max(1.0, getattr(S, "MAP_ZOOM", 1.0))
        if z > 1.01 and self.markers:
            for k, img in list(self.markers.items()):
                w, h = img.get_size()
                # on grossit doucement (pas plein zoom pour garder lisibilité)
                scale = min(2.0, 0.8 * z)
                nw, nh = int(w * scale), int(h * scale)
                self.markers[k] = pygame.transform.scale(img, (nw, nh))

    # ----------------- Entrées souris -----------------
    def on_mouse_down(self, pos):
        if self._btn_right_toggle_rect and self._btn_right_toggle_rect.collidepoint(pos):
            self.right_panel_visible = not self.right_panel_visible

    # ----------------- Rendu principal -----------------
    def draw(self, gs):
        surf = self.screen
        w, h = surf.get_size()
        surf.fill(S.BG)

        # zone map
        map_top = S.PANEL_TOP_H
        map_bottom = h - S.PANEL_BOTTOM_H
        center_x = w // 2
        center_y = (map_top + map_bottom) // 2

        # caméra centrée sur joueur (interpolée)
        cam_gx, cam_gy = gs.get_camera_center_grid()
        player_cx = int(cam_gx * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2)
        player_cy = int(cam_gy * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2)
        ox = center_x - player_cx
        oy = center_y - player_cy

        # --- calcul de la fenêtre visible en tuiles ---
        left_panel_w = 320
        right_panel_w = self.RIGHT_PANEL_W if self.right_panel_visible else 0

        map_top = S.PANEL_TOP_H
        map_bottom = h - S.PANEL_BOTTOM_H
        map_h_px = max(0, map_bottom - map_top)
        map_w_px = max(0, w - left_panel_w - right_panel_w)

        # centre de la zone carte (on garde le joueur centré visuellement)
        center_x = left_panel_w + map_w_px // 2
        center_y = (map_top + map_bottom) // 2

        # demi-tailles en tuiles
        rx = max(2, map_w_px // (2 * RENDER_TILE_SIZE) + 2)
        ry = max(2, map_h_px // (2 * RENDER_TILE_SIZE) + 2)

        # fenêtre de tuiles depuis la carte infinie
        cam_gx, cam_gy = gs.get_camera_center_grid()  # déjà présent plus haut
        cix, ciy = int(round(cam_gx)), int(round(cam_gy))

        grid2d, ogx, ogy = gs.grid.window(cix, ciy, rx, ry)

        # indices locaux du joueur selon la caméra (fractionnaires -> offset smooth)
        plx = cam_gx - ogx
        ply = cam_gy - ogy

        ox = center_x - (plx * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2)
        oy = center_y - (ply * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2)

        # dessine la grille visible
        render_grid(surf, grid2d, offset_px=(ox, oy))

        # MARKERS (uniquement si la case est encore exploitable)
        if getattr(S, "SHOW_MARKERS", True) and self.markers:
            rows = len(grid2d)
            cols = len(grid2d[0]) if rows else 0

            def is_event_usable(ev):
                if ev is None:
                    return False
                # ENCOUNTER / CHEST : masque si consommé
                if ev.etype in ("ENCOUNTER", "CHEST"):
                    return not ev.event_done
                # SHOP : visible par défaut (non visité => stock inconnu => on affiche)
                if ev.etype == "SHOP":
                    if ev.event_done:
                        return False
                    if ev.shop_inventory is None:
                        return True  # pas encore ouvert -> on suppose utilisable
                    left = sum(1 for it in ev.shop_inventory if not getattr(it, "_sold", False))
                    return left > 0
                return False

            for gx, gy, ev in gs.grid.events_in_rect(ogx, ogy, cols, rows):
                if not is_event_usable(ev):
                    continue
                key = {"ENCOUNTER": "encounter", "SHOP": "shop", "CHEST": "chest"}.get(ev.etype)
                if not key:
                    continue
                icon = self.markers.get(key)
                if not icon:
                    continue
                lx = gx - ogx
                ly = gy - ogy
                sx = ox + lx * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2
                sy = oy + ly * RENDER_TILE_SIZE + RENDER_TILE_SIZE // 2
                mw, mh = icon.get_size()
                offset_y = int(0.35 * mh)
                rect = icon.get_rect(center=(sx, sy - offset_y))
                surf.blit(icon, rect.topleft)

        # joueur (losange centré)
        pygame.draw.polygon(
            surf, S.HIGHLIGHT,
            [(center_x, center_y - 10),
             (center_x + 10, center_y),
             (center_x, center_y + 10),
             (center_x - 10, center_y)], width=3
        )

        # panneaux
        self._draw_top_panel(gs)
        self._draw_left_inventory(gs, w, h)

        if self.right_panel_visible:
            self._draw_right_nodeinfo(gs, w, h)

        # bouton de masquage/affichage du panneau droit (toujours visible)
        self._draw_right_panel_toggle(w, h)

        self._draw_bottom_logs(gs, w, h)

        if gs.state == "READY_COMBAT":
            self._draw_ready_overlay(w, h)

    # ----------------- Panneaux et éléments -----------------
    def _draw_top_panel(self, gs):
        surf = self.screen
        w, h = surf.get_size()

        # Bandeau de haut
        pygame.draw.rect(surf, S.PANEL, (0, 0, w, S.PANEL_TOP_H))

        # Titre
        y = 8
        draw_text(surf, "HeIsComing-like — tuiles v2 + markers overlays", 10, y, self.TITLE, S.ACCENT)
        y += 34

        # --- Stats sur UNE SEULE LIGNE ---
        hp = int(getattr(gs.player_unit, "hp", 0))
        max_hp = int(getattr(gs.player_unit, "max_hp", 0))
        sh = int(getattr(gs.player_unit, "shield", 0))
        max_sh = int(getattr(gs.player_unit, "max_shield", 0))
        atk = int(getattr(gs.player_unit, "atk", 0))
        spd = int(getattr(gs.player_unit, "speed", 0))

        # Bouclier : Y/X en combat, X hors combat
        bld_txt = f"{sh}/{max_sh}" if gs.state == "IN_COMBAT" else f"{max_sh}"

        stats_line = f"HP: {hp}/{max_hp}  •  BLD: {bld_txt}  •  ATK: {atk}  •  SPD: {spd}"
        draw_text(surf, stats_line, 10, y, self.BIG, S.WHITE)

    def _draw_left_inventory(self, gs, w, h):
        bx = 0
        panel_w = 320
        panel_h = h - S.PANEL_TOP_H - S.PANEL_BOTTOM_H
        by = S.PANEL_TOP_H
        pygame.draw.rect(self.screen, S.PANEL, (bx, by, panel_w, panel_h))

        y = by + 8
        max_y = by + panel_h - 10  # marge basse

        def line(text, font, color=S.WHITE, indent=0, dy=20):
            nonlocal y
            if y + dy > max_y:
                return False
            draw_text(self.screen, text, bx + 12 + indent, y, font, color)
            y += dy
            return True

        # OR
        if not line(f"Or : {gs.gold}", self.BIG, S.ACCENT, indent=0, dy=26):
            return

        # Titre
        if not line("Inventaire", self.BIG, S.WHITE, indent=0, dy=26):
            return

        # Arme
        weapon = gs.equipment.get("weapon")
        wname = weapon.name if weapon else "—"
        wbon = "" if not weapon else format_bonuses(weapon.bonuses)

        if not line(f"Arme : {wname}", self.FONT, S.WHITE, indent=0, dy=22): return
        if wbon:
            if not line(f"  {wbon}", self.FONT, S.WHITE, indent=12, dy=20): return
        else:
            if not line("  —", self.FONT, S.WHITE, indent=12, dy=18): return

        # Accessoires
        if not line("Équipements (4 max) :", self.FONT, S.WHITE, indent=0, dy=22): return
        acc = gs.equipment.get("accessories", [])
        if not acc:
            line("  —", self.FONT, S.WHITE, indent=12, dy=18)
        else:
            for it in acc:
                if not line(f"• {it.name} [{it.slot}]", self.FONT, S.WHITE, indent=0, dy=20):
                    line("…", self.FONT, S.WHITE, indent=0, dy=18)
                    break
                bon = format_bonuses(it.bonuses)
                if bon:
                    if not line(f"  {bon}", self.FONT, S.WHITE, indent=12, dy=18):
                        line("…", self.FONT, S.WHITE, indent=0, dy=18)
                        break

    def _draw_right_nodeinfo(self, gs, w, h):
        panel_h = S.PANEL_TOP_H
        bx = w - self.RIGHT_PANEL_W
        if bx < self.RIGHT_PANEL_W:  # window trop étroite -> on laisse le toggle gérer
            return
        pygame.draw.rect(self.screen, S.PANEL, (bx, panel_h, self.RIGHT_PANEL_W, h - panel_h - S.PANEL_BOTTOM_H))
        y = panel_h + 8
        draw_text(self.screen, "Node Info", bx + 12, y, self.BIG, S.WHITE);
        y += 30

        # Compteurs globaux
        draw_text(self.screen, f"Visited nodes: {gs.nodes_visited_count}", bx + 12, y, self.FONT, S.WHITE);
        y += 22
        draw_text(self.screen, f"State: {gs.state}", bx + 12, y, self.FONT, S.WHITE);
        y += 26

        ev = gs.grid.get_event_at(gs.gx, gs.gy)
        if ev is not None:
            draw_text(self.screen, f"Event: {ev.etype}", bx + 12, y, self.FONT, S.WHITE);
            y += 20
            draw_text(self.screen, f"Visited: {ev.visited}", bx + 12, y, self.FONT, S.WHITE);
            y += 20
            if ev.etype == "SHOP":
                left = len([it for it in (ev.shop_inventory or []) if not getattr(it, "_sold", False)])
                draw_text(self.screen, f"Shop stock restant: {left if ev.shop_inventory else '—'}", bx + 12, y,
                          self.FONT, S.WHITE)
            elif ev.etype == "CHEST":  # <-- AJOUT
                status = "ouvert" if ev.event_done else "intact"
                draw_text(self.screen, f"Coffre: {status}", bx + 12, y, self.FONT, S.WHITE);
                y += 20
                # (optionnel) si des choix ont déjà été générés pour ce coffre :
                if getattr(ev, "chest_choices", None) and not ev.event_done:
                    draw_text(self.screen, f"Choix disponibles: {len(ev.chest_choices)}", bx + 12, y, self.FONT,
                              S.WHITE)
        else:
            draw_text(self.screen, "Aucun événement ici", bx + 12, y, self.FONT, S.WHITE)

    def _draw_right_panel_toggle(self, w, h):
        """Dessine le bouton pour masquer/afficher le panneau droit et mémorise son rect cliquable."""
        handle_w = 26
        handle_h = 60
        mid_y = S.PANEL_TOP_H + (h - S.PANEL_TOP_H - S.PANEL_BOTTOM_H) // 2 - handle_h // 2

        if self.right_panel_visible:
            # petit bouton sur la BORDURE GAUCHE du panneau droit
            x = w - self.RIGHT_PANEL_W - handle_w
            y = max(S.PANEL_TOP_H + 8, min(mid_y, h - S.PANEL_BOTTOM_H - handle_h - 8))
            pygame.draw.rect(self.screen, (40, 40, 46), (x, y, handle_w, handle_h), border_radius=8)
            # chevrons >>
            cx = x + handle_w // 2
            cy = y + handle_h // 2
            pygame.draw.polygon(self.screen, S.WHITE, [(cx - 6, cy - 10), (cx - 2, cy - 6), (cx - 6, cy - 2)], width=0)
            pygame.draw.polygon(self.screen, S.WHITE, [(cx - 6, cy + 2), (cx - 2, cy + 6), (cx - 6, cy + 10)], width=0)
            self._btn_right_toggle_rect = pygame.Rect(x, y, handle_w, handle_h)
        else:
            # petit onglet collé au BORD DROIT de l'écran
            x = w - handle_w
            y = max(S.PANEL_TOP_H + 8, min(mid_y, h - S.PANEL_BOTTOM_H - handle_h - 8))
            pygame.draw.rect(self.screen, (40, 40, 46), (x, y, handle_w, handle_h), border_radius=8)
            # chevrons << (pour indiquer "ouvrir")
            cx = x + handle_w // 2
            cy = y + handle_h // 2
            pygame.draw.polygon(self.screen, S.WHITE, [(cx + 6, cy - 10), (cx + 2, cy - 6), (cx + 6, cy - 2)], width=0)
            pygame.draw.polygon(self.screen, S.WHITE, [(cx + 6, cy + 2), (cx + 2, cy + 6), (cx + 6, cy + 10)], width=0)
            self._btn_right_toggle_rect = pygame.Rect(x, y, handle_w, handle_h)

    def _draw_bottom_logs(self, gs, w, h):
        pygame.draw.rect(self.screen, (18, 18, 18), (0, h - S.PANEL_BOTTOM_H, w, S.PANEL_BOTTOM_H))
        header_y = h - S.PANEL_BOTTOM_H + 4
        draw_text(self.screen, "LOGS:", 8, header_y, self.BIG, S.WHITE)

        # espace disponible sous le header
        top = header_y + 28
        bottom = h - 8
        avail_h = max(0, bottom - top)
        line_h = 18
        max_lines = max(1, avail_h // line_h)

        for i, ln in enumerate(gs.logs[-max_lines:]):
            draw_text(self.screen, ln, 12, top + i * line_h, self.FONT, S.WHITE)

    def _draw_ready_overlay(self, w, h):
        box_w, box_h = 560, 140
        bx = w // 2 - box_w // 2
        by = h // 2 - box_h - 40
        pygame.draw.rect(self.screen, S.PANEL, (bx, by, box_w, box_h))
        draw_text(self.screen, "ENCOUNTER ici — SPACE pour démarrer", bx + 18, by + 12, self.BIG, S.WHITE)
        draw_text(self.screen, "Ou déplace-toi ailleurs (flèches) pour ignorer.", bx + 18, by + 56, self.FONT, S.WHITE)
