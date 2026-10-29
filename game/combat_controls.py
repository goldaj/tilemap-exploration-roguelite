"""UI-to-game routing for mouse combat controls; no Pygame imports.

The keyboard and mouse paths must use the same GameState commands so rules,
cooldowns and terminal outcomes are never reimplemented by the UI.
"""
from __future__ import annotations


def available_actions(state) -> dict[str, bool]:
    """Button enabled/disabled states, read-only."""
    combat = getattr(state, "current_combat", None)
    manual = (getattr(state, "state", None) == "IN_COMBAT"
              and not getattr(state, "auto_play", True)
              and combat is not None and not combat.finished)
    return {
        "attack": bool(manual),
        "guard": bool(manual),
        "power": bool(manual and combat.power_cooldown == 0),
    }


def route_combat_click(state, hit_name: str) -> bool:
    """Dispatch a UI hotspot by name. True iff accepted.

    A click on an unavailable action is ignored and does not consume a turn.
    """
    if getattr(state, "state", None) != "IN_COMBAT" or not getattr(state, "current_combat", None):
        return False
    if hit_name == "combat_auto":
        state.toggle_auto()
        return True
    if hit_name == "combat_speed":
        if getattr(state, "auto_play", False):
            state.toggle_speed()
            return True
        return False
    actions = {
        "combat_attack": "attack",
        "combat_guard": "guard",
        "combat_power": "power",
    }
    action = actions.get(hit_name)
    if action is None or not available_actions(state).get(action, False):
        return False
    return bool(state.manual_combat_action(action))
