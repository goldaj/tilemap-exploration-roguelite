# Roguelite — exploration sur carte à tuiles

Prototype de jeu en Python/Pygame : exploration d'une grille, rencontres, combats, boutique et rendu de carte avec tuiles et sprites. Ce dépôt conserve son historique de développement et la dernière version locale du prototype.

## Lancer

Python 3.10 ou plus récent conseillé. Dans un environnement virtuel :

```bash
python -m pip install -r requirements.txt
python main.py
```

## Structure

- `game/app.py` : application et boucle du jeu.
- `game/world.py`, `game/infinite_grid.py`, `game/node.py` : monde et exploration.
- `game/combat.py`, `game/units.py`, `game/items.py`, `game/shop.py` : systèmes de jeu.
- `game/user_interface/` : rendu des tuiles, marqueurs et ressources graphiques.
- `settings.py` : paramètres du prototype.

Le projet est expérimental ; la qualité et les fonctionnalités peuvent évoluer. Les environnements, caches et paramètres de l'éditeur sont ignorés par Git.

## Situer ce prototype parmi les autres jeux

| Projet | Expérience explorée | Organisation du code |
| --- | --- | --- |
| [Moonrail](https://github.com/goldaj/moonrail-narrative-deckbuilder) | Deckbuilding narratif, collection et progression persistante | Projet distinct, avec sa direction de produit et ses personnages |
| [Bestiaire](https://github.com/goldaj/roguelite-bestiary-deckbuilder) | Créatures, cartes et attrition persistante au fil des combats | Prototype autonome, moteur `core/` et tests ; progression encore à corriger |
| [DeckLite](https://github.com/goldaj/decklite-roguelite-deckbuilder) | Construire son deck pendant une run, choisir des récompenses, événements et boutique méta | Prototype Pygame concentré dans `main.py` |
| [Exploration sur tuiles](https://github.com/goldaj/tilemap-exploration-roguelite) | Se déplacer sur une grille, rencontrer des ennemis, gérer objets et boutique | Modules monde/combat/interface, tuiles et sprites |
| [Chess Roguelite](https://github.com/goldaj/chess-roguelite) | Déplacer des pièces d'échecs et acquérir des améliorations entre les affrontements | Plateau, IA, progression et interface souris |
| [Idle Clicker](https://github.com/goldaj/idle-clicker-tkinter) | Clics, revenus et achats avec coût dynamique | Interface de bureau Tkinter/ttkbootstrap |

Ces dépôts conservent des expériences distinctes, à différents niveaux d'avancement.
