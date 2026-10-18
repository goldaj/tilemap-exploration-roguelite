# Roguelite : exploration sur grille

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
