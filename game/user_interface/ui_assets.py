# ui_assets.py
from pathlib import Path
import pygame

ASSETS_ITEMS_DIR = Path(__file__).resolve().parent / "assets" / "items"
_cache: dict[tuple[str, int], pygame.Surface] = {}


def get_item_icon(item_id: str, size: int) -> pygame.Surface:
    key = (item_id, size)
    if key in _cache:
        return _cache[key]

    path = ASSETS_ITEMS_DIR / f"{item_id}.png"
    if path.exists():
        base = pygame.image.load(str(path)).convert_alpha()
        surf = pygame.transform.scale(base, (size, size))  # nos “cartes” sont 128x128
    else:
        # Fallback visuel
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((220, 220, 220))
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), width=4)
        pygame.draw.line(surf, (0, 0, 0), (6, 6), (size - 6, size - 6), 3)
        pygame.draw.line(surf, (0, 0, 0), (6, size - 6), (size - 6, 6), 3)

    _cache[key] = surf
    return surf


def blit_item_icon(screen: pygame.Surface, item_id: str, rect: pygame.Rect, *, pad: int = 0):
    size = min(rect.w, rect.h) - 2 * pad
    icon = get_item_icon(item_id, size)
    screen.blit(icon, (rect.x + pad, rect.y + pad))
