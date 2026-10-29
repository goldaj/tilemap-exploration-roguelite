# Historique ChatGPT de Tilemap Exploration

**Archive partielle datée du 2026-10-24, à lire depuis AGENTS.md.** Les conversations complètes ne sont pas disponibles sous forme exportable dans cette session. Ne pas prétendre que ce fichier les remplace.

## Contexte confirmé dans README
Roguelite Python/Pygame, exploration de grille, rencontres, objets, combat et boutique.

## Reprise technique
`python main.py` après installation requirements.txt ; respecter séparation des modules world/combat/UI.

## Échanges retrouvés
- **2026-10-18** — Assistant (résumé reconstruit, non verbatim) : archivage et classement de ce projet dans un dépôt autonome, en préservant le travail précédent.
- **2026-10-18 13:24:13 UTC** — Utilisateur (extrait exact) : « N'écrase aucun repo existant. »
- **2026-10-24** — Utilisateur (résumé fidèle, non verbatim ; heure inconnue) : souhaite AGENTS.md, un journal consultable par Codex avec échanges exacts, rôles, horodatages disponibles, et mise à jour de cette discipline à chaque modification Git.

## Limites
Aucun AGENTS.md initial. Il manque encore les questions et réponses intégrales des anciennes séances ; aucun message de l'assistant n'est inventé. Compléter depuis les exports authentiques si disponibles, avec examen préalable des données sensibles avant toute publication. Ajouter ensuite des entrées horodatées `Utilisateur (verbatim)` / `Assistant (verbatim)` lorsque les textes exacts sont accessibles.

## Intervention 2026-10-29 — combat manuel utilisable (résumé non verbatim)

- L'utilisateur demande des développements fonctionnels continus dans différents dépôts, reprise des travaux inachevés, inspection des branches/PR et passation Codex. Aucun historique intégral nouveau n'a été récupéré.
- Audit de `develop`, `chatgpt/review-20261024` et de la PR #1 ; branche séparée `feat/tactical-manual-combat-20261029`, sans réécriture de la PR #1.
- Bug constaté : le mode auto OFF stoppait les tours sans proposer de décisions manuelles. Correction : actions 1 attaque, 2 garde, 3 puissance avec recharge 3 tours, Espace auto/manuel ; règles de dégâts cohérentes et logs dédupliqués.
- Tests hors écran couvrant la simulation de tours et l'équilibrage de 20 graines en tout début de jeu ; intégration Pygame et campagne complète non validées. Workflow ajouté, statut CI à vérifier.
- Voir `docs/MANUAL_TACTICAL_COMBAT.md` ; étape suivante : métriques de TTK et taux de victoire en multi-seed avant réglages des ennemis. Aucune donnée privée ni assets modifiés.
