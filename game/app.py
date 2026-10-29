# game/app.py
import pygame, sys
import settings as S
from .state import GameState
from .combat_controls import available_actions, route_combat_click
from .items import format_bonuses

# sélection de l'UI
if S.USE_TILEMAP_UI:
    from .ui_tilemap import UITilemap as UI
    from .ui_tilemap import draw_text

    USING_UI = "tilemap"
else:
    from .ui import UI, draw_text

    USING_UI = "classic"

print(f"[UI] Using {USING_UI}")


class App:
    def __init__(self):
        pygame.init()

        # --- Taille initiale adaptée à l'écran (90% de la résolution) ---
        info = pygame.display.Info()
        scr_w, scr_h = info.current_w, info.current_h
        init_w = min(S.INITIAL_W, int(scr_w * 0.90))
        init_h = min(S.INITIAL_H, int(scr_h * 0.90))

        self.screen = pygame.display.set_mode((init_w, init_h), pygame.RESIZABLE)
        self.is_fullscreen = False
        self.clock = pygame.time.Clock()
        self.ui = UI(self.screen)
        # --- petites fontes (plus compact) ---
        self.FONT = getattr(self.ui, "FONT", pygame.font.SysFont(None, 18))
        self.BIG = getattr(self.ui, "BIG", pygame.font.SysFont(None, 24))
        self.TITLE = getattr(self.ui, "TITLE", self.BIG)

        # variantes réduites
        self.FONT_S = pygame.font.SysFont(None, max(11, self.FONT.get_height() - 3))
        self.BIG_S = pygame.font.SysFont(None, max(13, self.BIG.get_height() - 4))

        w, h = self.screen.get_size()
        self.hot = {}  # dictionnaire de rectangles cliquables, rempli à chaque frame
        self.game = GameState(w, h)

    def run(self):
        running = True
        # game/app.py — dans App.run()
        while running:
            dt = self.clock.tick(S.FPS) / 1000.0

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

                elif ev.type == pygame.VIDEORESIZE:
                    # garder la fenêtre redimensionnable
                    self.screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)

                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # 1) d'abord, si un overlay modal est ouvert, on le traite ici
                    if self.handle_mouse_click(ev.pos):
                        continue
                    # 2) sinon, clics UI génériques (ex: bouton panneau droit)
                    if hasattr(self.ui, "on_mouse_down"):
                        self.ui.on_mouse_down(ev.pos)

                elif ev.type == pygame.KEYDOWN:
                    # --- ÉCRAN DE MORT : R pour recommencer, ESC pour quitter ---
                    if self.game.state == "DEAD":
                        if ev.key == pygame.K_r:
                            w, h = self.screen.get_size()
                            self.game = GameState(w, h)
                        elif ev.key == pygame.K_ESCAPE:
                            running = False
                        continue  # on consomme l'événement en état DEAD

                    # --- CONFIRMATION DE REMPLACEMENT ---
                    if self.game.state == "CONFIRM_REPLACE":
                        if ev.key in (pygame.K_RETURN, pygame.K_y):  # confirmer
                            self.game.confirm_replace(True)
                        elif ev.key in (pygame.K_ESCAPE, pygame.K_n):  # annuler
                            self.game.confirm_replace(False)
                        continue

                    # --- SÉLECTION DE L'ACCESSOIRE À RETIRER ---
                    if self.game.state == "SELECT_DROP":
                        if ev.key in (pygame.K_1, pygame.K_KP1):
                            self.game.select_drop_index(0)
                        elif ev.key in (pygame.K_2, pygame.K_KP2):
                            self.game.select_drop_index(1)
                        elif ev.key in (pygame.K_3, pygame.K_KP3):
                            self.game.select_drop_index(2)
                        elif ev.key in (pygame.K_4, pygame.K_KP4):
                            self.game.select_drop_index(3)
                        elif ev.key in (pygame.K_ESCAPE, pygame.K_n):
                            self.game.cancel_preview()
                        continue

                    # --- SHOP : gestion dédiée et prioritaire ---
                    if self.game.state == "SHOP":
                        if ev.key in (pygame.K_1, pygame.K_KP1):
                            self.game.begin_shop_preview(0)
                        elif ev.key in (pygame.K_2, pygame.K_KP2):
                            self.game.begin_shop_preview(1)
                        elif ev.key in (pygame.K_3, pygame.K_KP3):
                            self.game.begin_shop_preview(2)
                        elif ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                            self.game.exit_shop()
                        continue

                    # --- COFFRE : gestion dédiée et prioritaire ---
                    if self.game.state == "CHEST":
                        if ev.key in (pygame.K_1, pygame.K_KP1):
                            self.game.begin_chest_preview(0)
                        elif ev.key in (pygame.K_2, pygame.K_KP2):
                            self.game.begin_chest_preview(1)
                        elif ev.key in (pygame.K_3, pygame.K_KP3):
                            self.game.begin_chest_preview(2)
                        elif ev.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                            self.game.exit_chest()
                        continue

                    # Combat: SPACE toggles auto/manual. In manual mode each key
                    # advances exactly one full turn; no continuous key repeat.
                    if self.game.state == "IN_COMBAT":
                        if ev.key == pygame.K_SPACE:
                            self.game.toggle_auto()
                        elif ev.key in (pygame.K_1, pygame.K_KP1):
                            self.game.manual_combat_action("attack")
                        elif ev.key in (pygame.K_2, pygame.K_KP2):
                            self.game.manual_combat_action("guard")
                        elif ev.key in (pygame.K_3, pygame.K_KP3):
                            self.game.manual_combat_action("power")
                        elif ev.key == pygame.K_f:
                            self.game.fast = not getattr(self.game, "fast", False)
                            self.game.turn_delay = S.FAST_TURN if self.game.fast else S.SLOW_TURN
                        elif ev.key == pygame.K_ESCAPE:
                            running = False
                        continue

                    # déplacement smooth par demande (avec enchaînement)
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        self.game.request_move("up")
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.game.request_move("down")
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.game.request_move("left")
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.game.request_move("right")

                    # --- Raccourcis existants : garde-les tels quels ---
                    elif ev.key == pygame.K_SPACE:
                        # pause/reprise auto-battle (si en combat)
                        if self.game.state == "IN_COMBAT":
                            self.game.auto_play = not self.game.auto_play
                    elif ev.key == pygame.K_f:
                        # vitesse combat
                        self.game.fast = not getattr(self.game, "fast", False)
                        self.game.turn_delay = S.FAST_TURN if self.game.fast else S.SLOW_TURN
                    elif ev.key == pygame.K_ESCAPE:
                        running = False
                    elif ev.key == pygame.K_F11:
                        # plein écran / fenêtre (en gardant la logique que je t’ai donnée)
                        self.is_fullscreen = not self.is_fullscreen
                        if self.is_fullscreen:
                            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            info = pygame.display.Info()
                            scr_w, scr_h = info.current_w, info.current_h
                            init_w = min(S.INITIAL_W, int(scr_w * 0.90))
                            init_h = min(S.INITIAL_H, int(scr_h * 0.90))
                            self.screen = pygame.display.set_mode((init_w, init_h), pygame.RESIZABLE)

                    # --- Shop: achats ---
                    elif ev.key in (pygame.K_1, pygame.K_KP1):
                        self.game.buy_shop_choice(0)
                    elif ev.key in (pygame.K_2, pygame.K_KP2):
                        self.game.buy_shop_choice(1)
                    elif ev.key in (pygame.K_3, pygame.K_KP3):
                        self.game.buy_shop_choice(2)
                    elif ev.key in (pygame.K_e, pygame.K_RETURN):
                        self.game.exit_shop()

                elif ev.type == pygame.KEYUP:
                    if ev.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s,
                                  pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                        self.game.set_held_dir(None)

            # MAJ de la direction tenue (frame-based, pas dans KEYDOWN)
            keys = pygame.key.get_pressed()
            held = None
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                held = "up"
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                held = "down"
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                held = "left"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                held = "right"
            self.game.set_held_dir(held)

            # update + draw habituels
            self.game.update(dt)
            self.ui.screen = self.screen
            # reset hotspots pour cette frame
            self.hot = {}
            self.ui.draw(self.game)
            # --- Overlays modaux (settent aussi des hotspots) ---
            if self.game.state == "IN_COMBAT" and self.game.current_combat:
                self.draw_combat_overlay(self.game.current_combat)
            elif self.game.state == "SHOP":
                self.draw_shop_overlay(self.game)
            elif self.game.state == "CHEST":
                self.draw_chest_overlay(self.game)
            elif self.game.state == "CONFIRM_REPLACE":
                self.draw_confirm_replace_overlay(self.game)
            elif self.game.state == "SELECT_DROP":
                self.draw_select_drop_overlay(self.game)
            elif self.game.state == "DEAD":
                self.draw_dead_overlay(self.game)

            # READY_COMBAT : créer un hotspot sur la zone de l’overlay (dessiné par l’UI)
            if self.game.state == "READY_COMBAT":
                # reprend la géométrie utilisée dans _draw_ready_overlay de l’UI
                w, h = self.screen.get_size()
                box_w, box_h = 560, 140
                bx = w // 2 - box_w // 2
                by = h // 2 - box_h - 40
                self.hot["ready_start"] = pygame.Rect(bx, by, box_w, box_h)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # --- Helpers layout: zone jouable, popup clamp, texte ellipsé ---
    def _wrap_text(self, text, font, max_w, max_lines=2):
        """Retourne 1..max_lines lignes wrapées qui tiennent dans max_w (dernière ligne ellipsée si besoin)."""
        words = text.split()
        if not words:
            return [""]

        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if not cur:
                cur = w
            elif font.size(test)[0] <= max_w:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        if len(lines) <= max_lines:
            return lines

        # Trop de lignes : compacter la fin et ellipser la dernière
        keep = lines[:max_lines - 1]
        last = " ".join(lines[max_lines - 1:])
        last_fit = self._ellipsis(last, font, max_w)
        return keep + [last_fit]

    def _content_bounds(self):
        """Retourne (x0, y0, x1, y1) de la zone *jouable* (sans panneaux)."""
        w, h = self.screen.get_size()
        top_h = getattr(S, "PANEL_TOP_H", 0)
        bottom_h = getattr(S, "PANEL_BOTTOM_H", 0)

        # largeur panneau gauche (ui_tilemap.py utilise 320)
        left_w = 320

        # panneau droit si visible (sinon 0)
        right_w = 0
        if hasattr(self.ui, "RIGHT_PANEL_W"):
            if getattr(self.ui, "right_panel_visible", False):
                right_w = int(getattr(self.ui, "RIGHT_PANEL_W", 340))

        x0 = left_w
        y0 = top_h
        x1 = w - right_w
        y1 = h - bottom_h
        # sécurité pour éviter valeurs négatives
        if x1 < x0: x0, x1 = 0, w
        if y1 < y0: y0, y1 = 0, h
        return x0, y0, x1, y1

    def _clamp_popup_size(self, desired_w, desired_h, margin=16):
        """Contraint la popup à rester dans la zone jouable, centrée."""
        x0, y0, x1, y1 = self._content_bounds()
        avail_w = max(0, x1 - x0 - 2 * margin)
        avail_h = max(0, y1 - y0 - 2 * margin)
        box_w = min(desired_w, avail_w)
        box_h = min(desired_h, avail_h)
        bx = x0 + (x1 - x0 - box_w) // 2
        by = y0 + (y1 - y0 - box_h) // 2
        return bx, by, box_w, box_h

    def _ellipsis(self, text, font, max_w):
        """Raccourcit `text` avec … pour tenir dans max_w (pixels)."""
        if max_w <= 0:
            return ""
        w, _ = font.size(text)
        if w <= max_w:
            return text
        # on garde au moins 1 char + …
        ell = "…"
        # recherche décroissante simple (suffisant pour nos longueurs)
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            candidate = text[:mid] + ell
            cw, _ = font.size(candidate)
            if cw <= max_w:
                lo = mid + 1
            else:
                hi = mid
        mid = max(1, lo - 1)
        return text[:mid] + ell

    def _draw_text_clamped(self, surf, text, x, y, font, color, max_w):
        s = self._ellipsis(text, font, max_w)
        draw_text(surf, s, x, y, font, color)

    def _draw_button(self, surf, rect, label, hovered=False, font=None):
        if font is None: font = self.FONT_S
        bg = (50, 54, 62) if not hovered else (70, 76, 92)
        border = (96, 102, 116)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, border, rect, width=2, border_radius=10)
        tw, th = font.size(label)
        draw_text(surf, label, rect.x + (rect.w - tw) // 2, rect.y + (rect.h - th) // 2, font, S.WHITE)

    def handle_mouse_click(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        st = self.game.state
        H = self.hot  # raccourci

        # --- DEAD ---
        if st == "DEAD":
            if H.get("dead_restart") and H["dead_restart"].collidepoint(x, y):
                w, h = self.screen.get_size()
                self.game = GameState(w, h)  # même effet que la touche R
                return True
            if H.get("dead_quit") and H["dead_quit"].collidepoint(x, y):
                pygame.event.post(pygame.event.Event(pygame.QUIT))  # même effet que ESC -> quitter
                return True
            return False

        # --- SHOP ---
        if st == "SHOP":
            for i, r in enumerate(H.get("shop_items", [])):
                if r and r.collidepoint(x, y):
                    self.game.begin_shop_preview(i)
                    return True
            if H.get("shop_exit") and H["shop_exit"].collidepoint(x, y):
                self.game.exit_shop()
                return True
            return False

        # --- CHEST ---
        if st == "CHEST":
            for i, r in enumerate(H.get("chest_items", [])):
                if r and r.collidepoint(x, y):
                    self.game.begin_chest_preview(i)
                    return True
            if H.get("chest_exit") and H["chest_exit"].collidepoint(x, y):
                self.game.exit_chest()
                return True
            return False

        # --- CONFIRM_REPLACE ---
        if st == "CONFIRM_REPLACE":
            if H.get("confirm_yes") and H["confirm_yes"].collidepoint(x, y):
                self.game.confirm_replace(True)
                return True
            if H.get("confirm_no") and H["confirm_no"].collidepoint(x, y):
                self.game.confirm_replace(False)
                return True
            return False

        # --- SELECT_DROP ---
        if st == "SELECT_DROP":
            for i, r in enumerate(H.get("drop_slots", [])):
                if r and r.collidepoint(x, y):
                    self.game.select_drop_index(i)
                    return True
            if H.get("drop_cancel") and H["drop_cancel"].collidepoint(x, y):
                self.game.cancel_preview()
                return True
            return False

        # --- IN_COMBAT : toggles cliquables ---
        if st == "IN_COMBAT":
            for key in ("combat_auto", "combat_speed", "combat_attack",
                        "combat_guard", "combat_power"):
                rect = H.get(key)
                if rect is not None and rect.collidepoint(x, y):
                    route_combat_click(self.game, key)
                    # Consume the hit on the overlay regardless of availability.
                    return True
            return False

        # --- READY_COMBAT : cliquer sur l’overlay démarre le combat ---
        if st == "READY_COMBAT":
            if H.get("ready_start") and H["ready_start"].collidepoint(x, y):
                self.game.start_combat()
                return True

        return False

    def draw_confirm_replace_overlay(self, gs):
        surf = self.screen
        pad = 14
        bx, by, box_w, box_h = self._clamp_popup_size(740, 420, margin=14)

        # fond/cadre
        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surf, (70, 70, 78), (bx, by, box_w, box_h), width=2, border_radius=12)

        # titre
        draw_text(surf, "ÉCHANGE — confirmer le remplacement ?", bx + pad, by + pad, self.BIG_S, S.WHITE)

        # Récup actuel/nouveau
        kind = gs.pending.get("replace_kind")
        cur = None
        if kind == "weapon":
            cur = gs.equipment.get("weapon")
        elif kind == "accessory":
            idx = gs.pending.get("replace_index")
            acc = gs.equipment.get("accessories", [])
            if isinstance(idx, int) and 0 <= idx < len(acc):
                cur = acc[idx]
        newp = gs.pending.get("proto")

        # Dessine une ligne type "shop/coffre"
        def _draw_preview_row(rx, ry, rw, proto, right_label: str):
            ROW_H = 60
            rect = pygame.Rect(rx, ry, rw, ROW_H)
            mouse = pygame.mouse.get_pos()
            hovered = rect.collidepoint(mouse)
            bg = (40, 42, 48) if not hovered else (58, 62, 72)
            pygame.draw.rect(surf, bg, rect, border_radius=10)
            pygame.draw.rect(surf, (80, 84, 96), rect, width=1, border_radius=10)

            # Icône placeholder
            ICON = 40
            icon_rect = pygame.Rect(rect.x + 10, rect.y + (ROW_H - ICON) // 2, ICON, ICON)
            pygame.draw.rect(surf, (30, 30, 34), icon_rect, border_radius=6)
            pygame.draw.rect(surf, (90, 90, 98), icon_rect, width=2, border_radius=6)
            pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.top + 5),
                             (icon_rect.right - 5, icon_rect.bottom - 5), width=2)
            pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.bottom - 5),
                             (icon_rect.right - 5, icon_rect.top - 5), width=2)

            # Étiquette à droite
            if right_label:
                lw, lh = self.BIG_S.size(right_label)
                lx = rect.right - 10 - lw
                ly = rect.y + (ROW_H - lh) // 2
                draw_text(surf, right_label, lx, ly, self.BIG_S, S.ACCENT)
                text_r = lx - 8
            else:
                text_r = rect.right - 12

            # Texte (nom + bonus), clampé
            text_l = icon_rect.right + 10
            max_w = max(8, text_r - text_l)
            name_txt = f"[{getattr(proto, 'slot', '—')}] {getattr(proto, 'name', '???')}"
            bon_txt = format_bonuses(getattr(proto, "bonuses", {}) or {}) or "—"
            self._draw_text_clamped(surf, name_txt, text_l, rect.y + 6, self.BIG_S, S.WHITE, max_w)
            self._draw_text_clamped(surf, bon_txt, text_l, rect.y + 6 + self.BIG_S.get_height(),
                                    self.FONT_S, S.WHITE, max_w)
            return ry + ROW_H

        # Corps : lignes comparatives
        y = by + pad + self.BIG_S.get_height() + 10
        list_w = box_w - 2 * pad

        if cur is not None:
            y = _draw_preview_row(bx + pad, y, list_w, cur, "ACTUEL")
            y += 8

        # Étiquette à droite pour le nouveau : GRATUIT (coffre) ou prix (shop)
        if gs.pending.get("from") == "CHEST":
            right = "GRATUIT"
        else:
            entry = gs.pending.get("entry")
            cost = getattr(entry, "cost", 0)
            right = f"{cost} or"
        y = _draw_preview_row(bx + pad, y, list_w, newp, right)

        # Boutons Confirmer/Annuler
        BTN_H = 30
        by_btn = by + box_h - pad - BTN_H
        half = (list_w - 8) // 2
        yes_rect = pygame.Rect(bx + pad, by_btn, half, BTN_H)
        no_rect = pygame.Rect(bx + pad + half + 8, by_btn, half, BTN_H)
        mouse = pygame.mouse.get_pos()
        self._draw_button(surf, yes_rect, "Confirmer  (Entrée • Y)", yes_rect.collidepoint(mouse), font=self.FONT_S)
        self._draw_button(surf, no_rect, "Annuler    (Échap  • N)", no_rect.collidepoint(mouse), font=self.FONT_S)
        self.hot["confirm_yes"] = yes_rect
        self.hot["confirm_no"] = no_rect

    def draw_select_drop_overlay(self, gs):
        surf = self.screen
        pad = 14
        bx, by, box_w, box_h = self._clamp_popup_size(700, 420, margin=14)

        # panneau
        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surf, (70, 70, 78), (bx, by, box_w, box_h), width=2, border_radius=12)

        # reset hotspots
        self.hot["drop_slots"] = []
        self.hot["drop_cancel"] = None

        # Titre wrapé (jusqu’à 3 lignes, petite fonte)
        title = "Inventaire plein — choisissez l'objet à retirer"
        max_title_w = box_w - 2 * pad
        lines = self._wrap_text(title, self.BIG_S, max_title_w, max_lines=3)
        y = by + pad
        for ln in lines:
            draw_text(surf, ln, bx + pad, y, self.BIG_S, S.WHITE)
            y += self.BIG_S.get_height() + 2
        y += 4  # petit gap

        # Zone liste
        ROW_H = 60  # plus bas
        GAP = 8
        BTN_H = 30

        list_top = y
        list_bottom = by + box_h - pad - BTN_H - 8
        mouse = pygame.mouse.get_pos()

        acc = gs.equipment.get("accessories", [])
        cur_y = list_top
        if acc:
            for i, it in enumerate(acc[:4]):
                # dessiner seulement si la ligne tient entière
                if cur_y + ROW_H > list_bottom:
                    break
                cur_y = self._draw_drop_item_row(
                    surf, bx + pad, cur_y, box_w - 2 * pad, it, mouse, i, row_h=ROW_H
                )
                cur_y += GAP
        else:
            draw_text(surf, "Aucun accessoire à retirer.", bx + pad, list_top + 6, self.FONT_S, S.WHITE)

        # Bouton Annuler
        btn_rect = pygame.Rect(bx + pad, by + box_h - pad - BTN_H, box_w - 2 * pad, BTN_H)
        self._draw_button(surf, btn_rect, "Annuler (Échap • N)", btn_rect.collidepoint(mouse), font=self.FONT_S)
        self.hot["drop_cancel"] = btn_rect

    def draw_dead_overlay(self, gs):
        surf = self.screen
        pad = 16
        bx, by, box_w, box_h = self._clamp_popup_size(680, 420, margin=14)

        # fond + cadre
        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surf, (70, 70, 78), (bx, by, box_w, box_h), width=2, border_radius=12)

        # titre
        title = "TU ES MORT"
        draw_text(surf, title, bx + pad, by + pad, self.TITLE, S.ACCENT)

        # stats de run (optionnelles mais utiles)
        y = by + pad + self.TITLE.get_height() + 8
        line = self.BIG
        small = self.FONT

        draw_text(surf, f"Nœuds visités : {getattr(gs, 'nodes_visited_count', 0)}", bx + pad, y, line, S.WHITE)
        y += line.get_height() + 6
        draw_text(surf, f"Combats gagnés : {getattr(gs, 'encounters_done', 0)}", bx + pad, y, line, S.WHITE)
        y += line.get_height() + 6
        draw_text(surf, f"Boss vaincus : {getattr(gs, 'boss_count', 0)}", bx + pad, y, line, S.WHITE)
        y += line.get_height() + 6
        draw_text(surf, f"Or collecté : {getattr(gs, 'gold', 0)}", bx + pad, y, line, S.WHITE)

        # rappel des raccourcis clavier
        hint = "R : recommencer    •    Esc : quitter"
        hw, hh = small.size(hint)
        draw_text(surf, hint, bx + pad, by + box_h - pad - hh - 40, small, S.WHITE)

        # boutons
        BTN_H = 36
        list_w = box_w - 2 * pad
        by_btn = by + box_h - pad - BTN_H

        half = (list_w - 10) // 2
        restart_rect = pygame.Rect(bx + pad, by_btn, half, BTN_H)
        quit_rect = pygame.Rect(bx + pad + half + 10, by_btn, half, BTN_H)

        mouse = pygame.mouse.get_pos()
        self._draw_button(surf, restart_rect, "Recommencer (R)", restart_rect.collidepoint(mouse), font=self.BIG_S)
        self._draw_button(surf, quit_rect, "Quitter (Esc)", quit_rect.collidepoint(mouse), font=self.BIG_S)

        # hotspots cliquables
        self.hot["dead_restart"] = restart_rect
        self.hot["dead_quit"] = quit_rect

    def draw_combat_overlay(self, cm):
        surf = self.screen
        w, h = surf.get_size()
        pad = 16

        # Fonts / hauteurs réelles
        title_h = self.ui.TITLE.get_height()
        line_h = self.ui.FONT.get_height()

        # Cadre & dimensions
        box_w = min(900, w - 80)
        base_panels_h = 96
        instr_h = 2 * line_h + 28  # two distinct clickable control rows
        min_log_lines = 3
        content_min_h = pad + title_h + pad + base_panels_h + pad + min_log_lines * line_h + pad + instr_h + pad
        box_h = min(max(240, content_min_h), h - 80)

        bx = w // 2 - box_w // 2
        by = h // 2 - box_h // 2

        # Fond
        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h))

        # Titre
        y = by + pad
        draw_text(surf, f"COMBAT (Tour {cm.turn_count})", bx + pad, y, self.ui.TITLE, S.WHITE)
        y += title_h + pad

        # Layout des panneaux
        two_cols_ok = box_w >= (2 * 260 + 3 * pad)
        if two_cols_ok:
            panel_w = (box_w - 3 * pad) // 2
            panel_h = base_panels_h
            px1, py1 = bx + pad, y
            px2, py2 = bx + pad * 2 + panel_w, y
            y_after_panels = y + panel_h
        else:
            panel_w = (box_w - 2 * pad)
            panel_h = base_panels_h
            px1, py1 = bx + pad, y
            px2, py2 = bx + pad, y + panel_h + pad
            y_after_panels = py2 + panel_h

        # --- Panneau JOUEUR ---
        pygame.draw.rect(surf, (0, 0, 0), (px1 - 2, py1 - 2, panel_w + 4, panel_h + 4))
        pygame.draw.rect(surf, S.PLAYER_COL, (px1, py1, panel_w, panel_h))
        draw_text(surf, "PLAYER", px1 + 8, py1 + 8, self.ui.FONT, S.WHITE)
        draw_text(surf, f"HP: {int(cm.player.hp)}/{int(cm.player.max_hp)}",
                  px1 + 8, py1 + 8 + line_h + 4, self.ui.FONT, S.WHITE)
        draw_text(surf,
                  f"ATK: {cm.player.atk:.1f}  BLD: {int(getattr(cm.player, 'max_shield', 0))}  SPD: {cm.player.speed:.2f}",
                  px1 + 8, py1 + 8 + 2 * (line_h + 4), self.ui.FONT, S.WHITE)

        # --- Panneau ENNEMI ---
        ecol = S.BOSS_COL if cm.enemy.is_boss else S.EN_COL
        pygame.draw.rect(surf, (0, 0, 0), (px2 - 2, py2 - 2, panel_w + 4, panel_h + 4))
        pygame.draw.rect(surf, ecol, (px2, py2, panel_w, panel_h))
        draw_text(surf, f"{'BOSS' if cm.enemy.is_boss else 'ENNEMI'}", px2 + 8, py2 + 8, self.ui.FONT, S.WHITE)
        draw_text(surf, f"HP: {int(cm.enemy.hp)}/{int(cm.enemy.max_hp)}",
                  px2 + 8, py2 + 8 + line_h + 4, self.ui.FONT, S.WHITE)
        draw_text(surf,
                  f"ATK: {cm.enemy.atk:.1f}  BLD: {int(getattr(cm.enemy, 'max_shield', 0))}  SPD: {cm.enemy.speed:.2f}",
                  px2 + 8, py2 + 8 + 2 * (line_h + 4), self.ui.FONT, S.WHITE)

        # Y sous les panneaux
        y = y_after_panels + pad

        # Log area
        log_top = y
        log_bottom = by + box_h - pad - instr_h
        log_h = max(0, log_bottom - log_top)
        max_lines = max(1, log_h // line_h)
        pygame.draw.rect(surf, (12, 12, 12), (bx + pad - 2, log_top - 2, box_w - 2 * pad + 4, log_h + 4), width=1)

        lines = cm.log[-max_lines:] if hasattr(cm, "log") else []
        for i, ln in enumerate(lines):
            draw_text(surf, ln, bx + pad, log_top + i * line_h, self.ui.FONT, S.WHITE)

        # --- Controls: mode button + distinct actual mouse actions ---
        instr_y = by + box_h - pad - instr_h
        auto_txt = f"Auto: {'ON' if self.game.auto_play else 'OFF'}  |  Espace: basculer"
        draw_text(surf, auto_txt, bx + pad, instr_y, self.ui.FONT, S.WHITE)
        aw, ah = self.ui.FONT.size(auto_txt)
        self.hot["combat_auto"] = pygame.Rect(bx + pad, instr_y, aw, ah)
        self.hot["combat_speed"] = None
        self.hot["combat_attack"] = None
        self.hot["combat_guard"] = None
        self.hot["combat_power"] = None
        mouse = pygame.mouse.get_pos()
        if self.game.auto_play:
            speed = f"F: vitesse ({self.game.turn_delay:.2f}s)"
            sw, sh = self.ui.FONT.size(speed)
            sx = bx + box_w - pad - sw
            draw_text(surf, speed, sx, instr_y, self.ui.FONT, S.WHITE)
            self.hot["combat_speed"] = pygame.Rect(sx, instr_y, sw, sh)
        else:
            states = available_actions(self.game)
            actions = (
                ("attack", "combat_attack", "1 Attaquer"),
                ("guard", "combat_guard", "2 Garder (-2)"),
                ("power", "combat_power",
                 "3 Puissance" if cm.power_cooldown == 0 else f"3 Puissance ({cm.power_cooldown}t)"),
            )
            width = max(62, (box_w - 2 * pad - 16) // 3)
            button_y = instr_y + line_h + 9
            for index, (action, key, label) in enumerate(actions):
                rect = pygame.Rect(bx + pad + index * (width + 8), button_y, width, line_h + 12)
                if states[action]:
                    self._draw_button(surf, rect, label, rect.collidepoint(mouse), font=self.ui.FONT)
                    self.hot[key] = rect
                else:
                    # Explicitly disabled power action during its cooldown.
                    pygame.draw.rect(surf, (38, 39, 44), rect, border_radius=6)
                    draw_text(surf, label, rect.x + 6, rect.y + 4, self.ui.FONT, (120, 120, 125))

        # Message si fini
        if cm.finished:
            msg = f"Combat terminé : {cm.result}"
            msg_y = by + pad + title_h + 4
            draw_text(surf, msg, bx + box_w - pad - 280, msg_y, self.ui.BIG, S.WHITE)

    def _draw_chest_item_row(self, surf, bx, by, bw, item, mouse_pos, row_h=60):
        PAD = 10
        ICON = 40
        import pygame
        rect = pygame.Rect(bx, by, bw, row_h)
        hovered = rect.collidepoint(mouse_pos)

        bg = (40, 42, 48) if not hovered else (58, 62, 72)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, (80, 84, 96), rect, width=1, border_radius=10)

        # Icône
        icon_rect = pygame.Rect(rect.x + PAD, rect.y + (row_h - ICON) // 2, ICON, ICON)
        pygame.draw.rect(surf, (30, 30, 34), icon_rect, border_radius=6)
        pygame.draw.rect(surf, (90, 90, 98), icon_rect, width=2, border_radius=6)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.top + 5),
                         (icon_rect.right - 5, icon_rect.bottom - 5), width=2)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.bottom - 5),
                         (icon_rect.right - 5, icon_rect.top - 5), width=2)

        # Label "GRATUIT"
        label = "GRATUIT"
        lw, lh = self.BIG_S.size(label)
        lx = rect.right - PAD - lw
        ly = rect.y + (row_h - lh) // 2
        draw_text(surf, label, lx, ly, self.BIG_S, S.ACCENT)

        # Zone texte
        text_l = icon_rect.right + 10
        text_r = lx - 8
        max_w = max(8, text_r - text_l)

        # Nom (toujours)
        name_txt = f"[{item.proto.slot}] {item.name}"
        self._draw_text_clamped(surf, name_txt, text_l, rect.y + 6, self.BIG_S, S.WHITE, max_w)

        # BONUS (toujours)
        bon_txt = format_bonuses(item.proto.bonuses) or "—"
        self._draw_text_clamped(surf, bon_txt, text_l, rect.y + 6 + self.BIG_S.get_height(), self.FONT_S, S.WHITE,
                                max_w)

        self.hot["chest_items"].append(rect)
        return by + row_h

    def draw_chest_overlay(self, gs):
        surf = self.screen
        pad = 14
        bx, by, box_w, box_h = self._clamp_popup_size(740, 420, margin=14)

        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surf, (70, 70, 78), (bx, by, box_w, box_h), width=2, border_radius=12)

        self.hot["chest_items"] = []
        self.hot["chest_exit"] = None

        title_y = by + pad
        draw_text(surf, "COFFRE", bx + pad, title_y, self.BIG_S, S.WHITE)

        ROW_H = 60
        GAP = 8
        BTN_H = 30

        list_top = title_y + self.BIG_S.get_height() + 10
        list_bottom = by + box_h - pad - BTN_H - 8
        mouse = pygame.mouse.get_pos()

        y = list_top
        choices = getattr(gs, 'chest_choices', []) or []
        if choices:
            for it in choices:
                if y + ROW_H > list_bottom:
                    break
                y = self._draw_chest_item_row(
                    surf, bx + pad, y, box_w - 2 * pad, it, mouse, row_h=ROW_H
                )
                y += GAP
        else:
            draw_text(surf, "Le coffre est vide.", bx + pad, list_top + 6, self.FONT_S, S.WHITE)

        btn_rect = pygame.Rect(bx + pad, by + box_h - pad - BTN_H, box_w - 2 * pad, BTN_H)
        self._draw_button(surf, btn_rect, "Fermer le coffre  (E • Entrée • Espace)", btn_rect.collidepoint(mouse),
                          font=self.FONT_S)
        self.hot["chest_exit"] = btn_rect

    # ---- Helpers génériques de boutons / lignes cliquables ----
    def _draw_shop_item_row(self, surf, bx, by, bw, item, mouse_pos, row_h=60):
        PAD = 10
        ICON = 40
        import pygame
        rect = pygame.Rect(bx, by, bw, row_h)
        hovered = rect.collidepoint(mouse_pos)

        # fond
        bg = (40, 42, 48) if not hovered else (58, 62, 72)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, (80, 84, 96), rect, width=1, border_radius=10)

        # Icône
        icon_rect = pygame.Rect(rect.x + PAD, rect.y + (row_h - ICON) // 2, ICON, ICON)
        pygame.draw.rect(surf, (30, 30, 34), icon_rect, border_radius=6)
        pygame.draw.rect(surf, (90, 90, 98), icon_rect, width=2, border_radius=6)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.top + 5),
                         (icon_rect.right - 5, icon_rect.bottom - 5), width=2)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.bottom - 5),
                         (icon_rect.right - 5, icon_rect.top - 5), width=2)

        # Prix (droite)
        price = f"{item.cost} or"
        pw, ph = self.BIG_S.size(price)
        px = rect.right - PAD - pw
        py = rect.y + (row_h - ph) // 2
        draw_text(surf, price, px, py, self.BIG_S, S.ACCENT)

        # Zone texte
        text_l = icon_rect.right + 10
        text_r = px - 8
        max_w = max(8, text_r - text_l)

        # Nom (toujours)
        name_txt = f"[{item.proto.slot}] {item.name}"
        self._draw_text_clamped(surf, name_txt, text_l, rect.y + 6, self.BIG_S, S.WHITE, max_w)

        # BONUS (toujours)
        bon_txt = format_bonuses(item.proto.bonuses) or "—"
        self._draw_text_clamped(surf, bon_txt, text_l, rect.y + 6 + self.BIG_S.get_height(), self.FONT_S, S.WHITE,
                                max_w)

        # hotspot
        self.hot["shop_items"].append(rect)
        return by + row_h

    def _draw_drop_item_row(self, surf, bx, by, bw, item, mouse_pos, index, row_h=60):
        PAD = 10
        ICON = 40
        import pygame
        rect = pygame.Rect(bx, by, bw, row_h)
        hovered = rect.collidepoint(mouse_pos)

        bg = (40, 42, 48) if not hovered else (58, 62, 72)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, (80, 84, 96), rect, width=1, border_radius=10)

        # Badge index
        badge_w, badge_h = 22, 22
        badge_rect = pygame.Rect(rect.right - badge_w - 8, rect.y + 8, badge_w, badge_h)
        pygame.draw.rect(surf, (32, 34, 40), badge_rect, border_radius=6)
        pygame.draw.rect(surf, (95, 98, 110), badge_rect, width=2, border_radius=6)
        draw_text(surf, str(index + 1), badge_rect.x + 6, badge_rect.y + 2, self.FONT_S, S.WHITE)

        # Icône
        icon_rect = pygame.Rect(rect.x + PAD, rect.y + (row_h - ICON) // 2, ICON, ICON)
        pygame.draw.rect(surf, (30, 30, 34), icon_rect, border_radius=6)
        pygame.draw.rect(surf, (90, 90, 98), icon_rect, width=2, border_radius=6)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.top + 5),
                         (icon_rect.right - 5, icon_rect.bottom - 5), width=2)
        pygame.draw.line(surf, (90, 90, 98), (icon_rect.left + 5, icon_rect.bottom - 5),
                         (icon_rect.right - 5, icon_rect.top - 5), width=2)

        # Zone texte
        text_l = icon_rect.right + 10
        text_r = badge_rect.left - 8
        max_w = max(8, text_r - text_l)

        # Nom (toujours)
        name_txt = f"{item.name}  [{getattr(item, 'slot', 'accessory')}]"
        self._draw_text_clamped(surf, name_txt, text_l, rect.y + 6, self.BIG_S, S.WHITE, max_w)

        # BONUS (toujours)
        bon_txt = format_bonuses(getattr(item, "bonuses", {}) or {}) or "—"
        self._draw_text_clamped(surf, bon_txt, text_l, rect.y + 6 + self.BIG_S.get_height(), self.FONT_S, S.WHITE,
                                max_w)

        self.hot["drop_slots"].append(rect)
        return by + row_h

    def draw_shop_overlay(self, gs):
        surf = self.screen
        pad = 14
        bx, by, box_w, box_h = self._clamp_popup_size(740, 420, margin=14)

        # fond/cadre
        pygame.draw.rect(surf, S.PANEL, (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(surf, (70, 70, 78), (bx, by, box_w, box_h), width=2, border_radius=12)

        # hotspots
        self.hot["shop_items"] = []
        self.hot["shop_exit"] = None

        # titre (petit)
        title_y = by + pad
        draw_text(surf, "BOUTIQUE", bx + pad, title_y, self.BIG_S, S.WHITE)

        # liste
        ROW_H = 60
        GAP = 8
        BTN_H = 30

        list_top = title_y + self.BIG_S.get_height() + 10
        list_bottom = by + box_h - pad - BTN_H - 8
        mouse = pygame.mouse.get_pos()

        y = list_top
        choices = getattr(gs, 'shop_choices', [])
        if choices:
            for it in choices:
                if y + ROW_H > list_bottom:
                    break
                y = self._draw_shop_item_row(
                    surf, bx + pad, y, box_w - 2 * pad, it, mouse, row_h=ROW_H
                )
                y += GAP
        else:
            draw_text(surf, "Rupture de stock.", bx + pad, list_top + 6, self.FONT_S, S.WHITE)

        # bouton quitter
        btn_rect = pygame.Rect(bx + pad, by + box_h - pad - BTN_H, box_w - 2 * pad, BTN_H)
        self._draw_button(surf, btn_rect, "Fermer la boutique  (E • Entrée • Espace)", btn_rect.collidepoint(mouse),
                          font=self.FONT_S)
        self.hot["shop_exit"] = btn_rect