# AGENTS.md — Tilemap Exploration

Lire README.md puis **docs/CHATGPT_PROJECT_HISTORY.md** avant toute modification.

Projet : Roguelite Python/Pygame, exploration de grille, rencontres, objets, combat et boutique.

Validation et invariants : `python main.py` après installation requirements.txt ; respecter séparation des modules world/combat/UI.

Préserver les fichiers existants ; ne pas inventer de résultats de test. Après chaque intervention, compléter le journal avec les nouveaux messages effectivement disponibles, en distinguant Utilisateur et Assistant, verbatim et résumé, dates vérifiées ou inconnues. Ne jamais inventer de conversation ou d'horodatage. Veiller au caractère public/privé du dépôt.

## Fonctionnalité du 29 octobre 2026 : combat tactique manuel

Lire `docs/MANUAL_TACTICAL_COMBAT.md` avant toute reprise. Branche `feat/tactical-manual-combat-20261029`, base `develop` ; PR #1 sur `chatgpt/review-20261024` (génération des chemins) demeure séparée.

- `game/combat.py` : `step_turn("attack"|"guard"|"power")`, cooldown 3 tours, défense puis garde puis bouclier puis PV ; attaque automatique inchangée par défaut.
- `game/state.py` : `manual_combat_action` et `_advance_combat` avec journal non dupliqué et transition gagnant/perdant.
- `game/app.py` : touches Espace puis 1/2/3 ; instructions de l'overlay actualisées.
- `tests/test_manual_combat.py` : neuf scénarios en Python pur, dont 20 graines d'ennemis de début de jeu. Workflow `manual-combat.yml` pour Python 3.10/3.12.
- Contrôler réellement la CI, puis tester une run complète Pygame au clavier et revoir l'équilibrage HP/soins, 3–10 paliers, boss et recharge avant fusion. Ne pas déclarer le jeu « équilibré » sur un seul niveau.
