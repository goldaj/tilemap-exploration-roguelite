# Contre-audit et passation — Tilemap Exploration Roguelite (2026-10-30)

GitHub : 5 branches, 3 PR et arborescence interrogées. Tests de jeu, moteur et GUI non exécutés localement.

## Branches
- `develop` : `e47c858043d136fab2f603cb967329ad9f40a08c` (référence).
- `chatgpt/review-20261024` : **behind**, 0 exclusif(s), 18 derrière. Travaux intégrés à develop, candidate nettoyage après vérification des références.
- `feat/clickable-tactical-actions-20261029` : **behind**, 0 exclusif(s), 1 derrière. Travaux intégrés à develop, candidate nettoyage après vérification des références.
- `feat/tactical-manual-combat-20261029` : **behind**, 0 exclusif(s), 7 derrière. Travaux intégrés à develop, candidate nettoyage après vérification des références.
- `main` : **behind**, 0 exclusif(s), 29 derrière. Ancienne branche de référence : conserver jusqu'à contrôle des usages externes.

## PR
- [#3](https://github.com/goldaj/tilemap-exploration-roguelite/pull/3) — closed, fusionnée : feat: clickable tactical combat actions and headless tests
- [#2](https://github.com/goldaj/tilemap-exploration-roguelite/pull/2) — closed, fusionnée : feat: real manual roguelite combat with guard, power and cooldowns
- [#1](https://github.com/goldaj/tilemap-exploration-roguelite/pull/1) — closed, fusionnée : [ChatGPT] Tilemap : génération déterministe des chemins et robustesse de grille

## Arborescence
`.github`, `.gitignore`, `AGENTS.md`, `README.md`, `docs`, `game`, `main.py`, `requirements.txt`, `settings.py`, `tests`.

## Challenge de fonctionnalité
1. Vérifier génération déterministe des cartes : connectivité des zones, absence d'ennemis coincés, garantie de sortie atteignable.
2. Tester le combat manuel : clics, pouvoirs, garde, cooldowns et transitions de tour, notamment les interactions valides/inactives.
3. Tester décalages d'UI, actions répétées et différence entre mode headless et interface jouable.
4. Mesurer difficulté, progression, équipement et pertes de PV par étage ; détecter les soft-locks et pertes inévitables.
5. Les branches de fonction sont absorbées par develop ; ne pas supprimer `main` juste parce qu'elle est derrière. Exiger un test de campagne et traces CI avant livraison.
