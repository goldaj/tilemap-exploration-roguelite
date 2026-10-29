# Combat tactique manuel — tranche fonctionnelle du 29 octobre 2026

## Problème corrigé

Le raccourci `Espace` pouvait désactiver le combat automatique, mais **aucun tour manuel n'était accessible** au joueur. Le « mode manuel » servait donc surtout de pause. Ce changement le transforme en mécanique jouable.

## Contrôles (pendant un combat)

- `Espace` : alterner combat automatique / manuel.
- En mode manuel, `1` : **Attaquer**. Même attaque ordinaire qu'auparavant.
- `2` : **Garder**. N'attaque pas, mais réduit de 2 les dégâts ennemis de ce tour (après la défense, avant le bouclier) ; la réduction ne se cumule pas entre les tours.
- `3` : **Puissance**. Inflige un bonus de dégâts `max(1, round(ATK/2))` en plus de l'attaque, puis nécessite **3 autres tours** avant de redevenir disponible. Une demande pendant le cooldown est refusée **sans consommer de tour**.
- `F` : vitesse de combat automatique, comme auparavant.

Les options et l'état de recharge s'affichent en bas de l'overlay. Le mode auto utilise toujours l'attaque ordinaire. Aucune potion, magie ou ressource tierce n'a été inventée.

## Correctifs d'intégrité

- `CombatManager._apply_damage` applique désormais `defense`, puis la garde, puis le bouclier, enfin les PV. La logique de défense `Unit.take_damage` et celle des combats étaient incohérentes.
- Une cible réduite à 0 PV passe à `alive = False`.
- Le journal global reçoit **uniquement les nouveaux messages** d'un tour. L'ancien appel répétait les deux dernières lignes, puis encore les trois dernières en cas de victoire.
- Les décisions manuelles et automatiques passent par `GameState._advance_combat`, qui fait remonter victoire / défaite sans attente artificielle.

## Équilibrage initial

Un modèle simple, volontairement limité :
- Attaque = 1 point de dégâts de base.
- Garde = 0 dégâts infligés, mais `-2` dégâts subis pour ce tour, sans stockage.
- Puissance = attaque + au moins 1 point, mais 3 tours normaux de recharge.

Cela donne un arbitrage clair entre protection et burst. La défense préexistante peut réduire les dégâts à zéro, tandis que l'attaque puisssante peut surmonter des défenses légères.

**Tests ajoutés dans `tests/test_manual_combat.py` :** neuf scénarios incluant attaque auto, garde, recharge, défense+shield+PV, vol de vie, rejet de commandes, états terminaux, ordre de vitesse et survie face à 20 graines d'ennemis de niveau 0. Ils s'exécutent sans Pygame :

```bash
python -m unittest discover -s tests -p 'test_manual_combat.py' -v
python -m py_compile game/combat.py game/state.py game/app.py
```

La CI essaie Python 3.10 et 3.12. **Ces contrôles isolés ne garantissent pas le rendu Pygame ni l'équilibre d'une run entière**. Tester au clavier puis calibrer les paliers 3–10, les récompenses, les builds d'équipement et les mécanismes de soin en multi-seed.

## Périmètre et reprise Codex

- Base `develop` ; branche `feat/tactical-manual-combat-20261029` ; la PR #1 de correction des chemins reste séparée, sur `chatgpt/review-20261024`. Ne pas écraser ni merger automatiquement ce travail.
- Lire `AGENTS.md`, `README.md`, `docs/CHATGPT_PROJECT_HISTORY.md` et ce guide.
- Démarrage : `python -m pip install -r requirements.txt` puis `python main.py`. Dans un combat, `Espace`, puis `1`/`2`/`3`. Attention à l'absence de support graphique dans les runners CI.
- Vérifier CI, exécuter une partie manuelle sur vrai poste, tester un combat où l'ennemi est plus rapide, la garde avec défense et le retour à l'auto.
- Programme suivant : modéliser le TTK, le taux de victoire et le retour HP sur des centaines de graines; ajuster seulement sur données observées, pas au hasard.
- Aucun fichier graphique, aucun artefact utilisateur ou configuration locale n'ont été modifiés.
