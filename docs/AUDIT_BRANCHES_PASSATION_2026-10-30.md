# Passation Tilemap Exploration — audit GitHub du 30/10/2026

## Références (base `develop`)
- `develop` : `a81335b4cbdda9ea5f7f3922672bf84c472895cc`.
- `chatgpt/review-20261024` (`8128d492af9e9e691bfb8cbba7fe5e889b5d77fa`) : behind, ahead 0, behind 20. Historique déjà dans develop, candidate au nettoyage contrôlé.
- `feat/clickable-tactical-actions-20261029` (`a246f4c051b49d01b8b7126e6235d59cd4528e86`) : behind, ahead 0, behind 3. Historique déjà dans develop, candidate au nettoyage contrôlé.
- `feat/tactical-manual-combat-20261029` (`6364908a99f8bf2e6178934c1f9f8dadb7610dbd`) : behind, ahead 0, behind 9. Historique déjà dans develop, candidate au nettoyage contrôlé.
- `main` (`4e8b20cc185a2bf0b16925b0341322bc97e8405b`) : behind, ahead 0, behind 31. Historique déjà dans develop, candidate au nettoyage contrôlé.

## PR
- [#3](https://github.com/goldaj/tilemap-exploration-roguelite/pull/3) : fusionnée. `feat/clickable-tactical-actions-20261029` → `develop`.
- [#2](https://github.com/goldaj/tilemap-exploration-roguelite/pull/2) : fusionnée. `feat/tactical-manual-combat-20261029` → `develop`.
- [#1](https://github.com/goldaj/tilemap-exploration-roguelite/pull/1) : fusionnée. `chatgpt/review-20261024` → `develop`.

## Challenger le gameplay
La grille doit conserver connectivité des chemins et génération déterministe ; les combats manuels (`attack`, `guard`, `power`) doivent appliquer défense/bouclier/HP dans le bon ordre et ne pas consommer plusieurs fois le même tour. Vérifier cooldown, journal et déclenchement des états gagnant/perdant. L'overlay clickable doit fonctionner clavier et souris ; une CI headless ne prouve pas ergonomie ni équilibre des combats/boss de niveaux 3–10. Les sauvegardes doivent survivre aux nouvelles versions.

## Prochain agent
Lire README (« # Roguelite — exploration sur carte à tuiles »), AGENTS, docs/MANUAL_TACTICAL_COMBAT.md et journal ; exécuter `python -m unittest discover -s tests -v`, puis tester le combat manuel sur une partie Pygame et mesurer l'équilibrage. Ne pas toucher à `main` historique sans vérifier son usage. Aucun test ni merge/code modifié ici, document seul.
