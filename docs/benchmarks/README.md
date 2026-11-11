# Benchmarks

## Lancer un essai

Modifier les réglages de [leaderboards.py](../../Save0/leaderboards.py), puis
l’exécuter, ou appeler :

```python
import leaderboards

leaderboards.run(Leaderboards.Hay_Single, "simulation", "default", 0)
```

| Réglage | Choix |
| --- | --- |
| `LEADERBOARD` | Catégorie native `Leaderboards.*` ; elle détermine single/multi |
| `MODE` | `simulation` : un essai isolé ; `leaderboard` : campagne officielle avec publication Steam |
| `STRATEGY` | `default` : référence ; `candidate` ou `cheese` : variante du tableau ci-dessous |
| `SEED` | Simulation seulement ; négatif pour une graine aléatoire |
| `SPEEDUP` | Accélération de l’attente réelle, sans modifier le temps mesuré |

Le lanceur choisit un fichier, sans l’importer. Chaque benchmark par ressource
possède son algorithme, sa cible et ses helpers, sans dépendance aux producteurs.
Les resets utilisent au contraire les scénarios de progression.

## Références

Le nom `leaderboard_<ressource>_single.py` désigne le single et
`leaderboard_<ressource>.py` le multi. Dinosaur reste single, son chapeau étant unique.

| Catégorie native | Ressource dans le nom du fichier | Cible single | Cible multi |
| --- | --- | ---: | ---: |
| `Hay` / `Hay_Single` | `hay` | 100 000 000 | 2 000 000 000 |
| `Wood` / `Wood_Single` | `wood` | 500 000 000 | 10 000 000 000 |
| `Carrots` / `Carrots_Single` | `carrot` | 100 000 000 | 2 000 000 000 |
| `Pumpkins` / `Pumpkins_Single` | `pumpkin` | 10 000 000 | 200 000 000 |
| `Cactus` / `Cactus_Single` | `cactus` | 131 072 | 33 554 432 |
| `Sunflowers` / `Sunflowers_Single` | `power` | 10 000 | 100 000 |
| `Maze` / `Maze_Single` | `gold` | 616 448 | 9 863 168 |
| `Dinosaur` | `bone` | 33 488 928 | — |

Les catégories `Fastest_Reset` et `Fastest_Underground_Reset` choisissent
`leaderboard_fastest_reset` et `leaderboard_fastest_underground_reset`.
Les cibles ci-dessus viennent des scénarios natifs étudiés ; vérifier le jeu
après une mise à jour.

## Variantes disponibles

| Stratégie | Catégorie | Fichier `leaderboard_*` |
| --- | --- | --- |
| `candidate` | Carrots / Carrots_Single | `carrot_polyculture` / `carrot_single_polyculture` |
| `candidate` | Wood / Wood_Single | `wood_polyculture` / `wood_single_polyculture` |
| `candidate` | Pumpkins_Single | `pumpkin_single_pipeline` |
| `candidate` | Sunflowers | `power_global` |
| `cheese` | Sunflowers | `power_columns` |
| `cheese` | Maze | `gold_reuse` |
| `cheese` | Dinosaur | `bone_hybrid` |

Les variantes restent séparées des références jusqu’à mesure comparable. Leurs
[sources](../analyses/sources.md) et les [prochains essais](../analyses/optimisations.md)
décrivent leur intérêt et leurs limites.

## Hay Single conservé

[leaderboard_hay_single.py](../../Save0/leaderboard_hay_single.py), ancienne version
09 : grille 3×3, six Bush en x=0/1, Grass en x=2, préparation en S à six mouvements.
Les demandes de compagnons sont sélectionnées jusqu’à obtenir un Bush compatible ;
les buissons autour ne forcent pas cette demande. Conserver les racines immatures
valides, leur cache et le contrôle d’eau. La surplantation Grass utilisée ici
n’est pas une règle générale pour les autres cultures.

Temps rapporté par l’utilisateur le 5 novembre 2026 : **03:52.095**, build étudié
26410308. Les variantes numérotées ont été remplacées par ce fichier.

## Conditions et résultats

Le lanceur prépare une ressource cible à zéro et les consommables de la catégorie.
Les singles utilisent Expand 5 (8×8) et aucun Megafarm ; les resets commencent
sans stocks/déblocages. `simulate()` conserve les DLC installés et ne reproduit
pas tous les verrous de la campagne officielle. Lire le résultat du script :
une durée peut aussi correspondre à un arrêt sur erreur.

Un lancement direct du fichier utilise le terrain et les stocks courants.
`leaderboard_run(...)` impose le scénario officiel, répète les essais et publie
le score. Un `True` du lanceur confirme la demande, pas la réussite de la campagne.

Le [tableau principal](../../README.md#save0) contient les références relevées.
Le [CSV Steam](steam-leaderboards.csv) se rafraîchit avec :

```sh
python tools/export_leaderboards.py
```

Ce relevé est public et en lecture seule. Il ne récupère pas les essais plus
lents ; le commit du CSV identifie la collecte, pas le code ayant produit le score.
Un ancien meilleur score peut masquer une régression : noter aussi l’essai courant.
Le profil Steam est configuré dans `.env` avec `TFWR_STEAM_PROFILE` ; le CSV
ne conserve ni nom de compte ni lien vers le profil.
