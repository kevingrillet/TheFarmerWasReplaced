# Contrats de développement

## Langage et imports

Le langage du jeu ressemble à Python, sans être CPython. Employer les fonctions
et constructions des références [TFWR](../ai/tfwr.md) et [TMWR](../ai/tmwr.md) :
pas de bibliothèque standard, classes, exceptions ou syntaxe moderne présumées.
Utiliser `import module` puis `module.fonction()`, avec des imports triés dans
chaque bloc. Les appels directs et accès aux modules sont gratuits selon Timing ;
un callback, une indexation ou une copie de conteneur ne le sont pas forcément.

Les fonctions, paramètres et variables utilisent `snake_case`. Les helpers privés
portent `_`. Conserver les imports locaux qui évitent les dépendances circulaires.
Les noms répétés `farm_single`/`farm_multi` sont des espaces de noms utiles.

## Producteurs et financement

| Entrée | Résultat |
| --- | --- |
| `requirements(target_stock)` | Stocks nécessaires au prochain lot ; `{}` sans besoin, `None` si indisponible |
| `farm_single/multi(target_stock)` | Booléen ; `True` seulement si le stock absolu est atteint |
| `produce_single/multi(target_stock)` | Booléen ; `True` si un lot fini se termine correctement, même sans atteindre la cible |

Si le stock suffit, réussir sans préparation. Seul `resource_manager` finance les
dépendances, avant la production ; aucun producteur/worker/helper minier n’importe
le gestionnaire ou un autre producteur. Le gestionnaire recontrôle les intrants
entre lots et détecte les cycles ; un retour `None` n’est jamais une réussite.

Particularités d’API à conserver :

| Module | Particularité |
| --- | --- |
| `farm_polyculture` | `entity` précède le stock cible dans les besoins et la production |
| `farm_haywood` | Les deux stocks Hay et Wood doivent atteindre la cible |
| `farm_pumpkin` | Goo possède `goo_requirements` et `farm_goo_*`/`produce_goo_*` ; aucun objectif sentinelle `-1` |
| `farm_gold`, `farm_power` | `requirements(target_stock, parallel=False)` déclare le budget du mode |
| `farm_wood` | Paramètres optionnels `has_trees` et taille de champ à préserver |
| `farm_bone` | Single uniquement : un seul Dinosaur Hat |
| `mine_block` | Fonctionne avant Underground Senses ; les autres modes miniers requièrent leurs capteurs |

## Workers et terrain

- Chaque parent possède et rejoint tous ses handles, y compris après son propre
  échec. Un spawn refusé se traite en série ; aucun compteur fixe de drones ne
  sert de barrière. Les arguments et globals des enfants sont copiés.
- Refuser une phase si des workers précédents restent actifs. Financer avant
  `prepare`/`clear`, et ne jamais changer le monde pendant leur travail.
- `clear()` renouvelle le terrain ; `reset()` natif efface la progression. Les
  producteurs peuvent remplacer le terrain. Les collecteurs de la mine partagée
  ne financent, ne nettoient et ne sautent jamais vers un autre monde.
- Les lots sont finis, avec contrôle de progression. Valider un plan avant ses
  effets de bord ; un lot vide est sans action, un compte négatif est refusé.

## Invariants des algorithmes

| Producteur | À préserver |
| --- | --- |
| Carrot classique | Financer les graines du lot complet ; garder le profilage séparé des variantes polyculture |
| Polyculture | Bandes possédées, compagnons compatibles et Carrots gratuits ; aucun écrasement entre zones |
| Pumpkin / Goo | Réparer les plants morts ; attendre le champ avant la récolte. Amorçage Goo financé et zones d’infection disjointes |
| Cactus | Tri terminé et workers rejoints avant la récolte en chaîne |
| Power multi | Colonnes persistantes, plants immatures conservés. Réserver une seule capacité de graines puis des quotas distincts ; `CHECK_EVERY_ROUNDS` est une cadence de contrôle, pas un plafond de vie des drones |
| Power, financement | Les quotas se renouvellent localement tant que leurs graines restent disponibles ; joindre et vider les plants payés avant un financement. Garder les arrêts sans progrès, même si Power est consommé pendant la récolte |
| Bamboo | Planter avant les visites de fruits ; surveiller la croissance avec Timing. Deux vagues : colonnes paires puis anciens couloirs, uniquement après coupe à hover 0 et joins ; financer tous les plants prévus avant préparation |
| Coal / Iron / Quartz / puzzles | Voir les [contrats miniers](../guides/mining.md#contraintes-des-collecteurs) |

## Helpers

| Helper | Contrat |
| --- | --- |
| `q_till`, `q_till_grass` | État souhaité présent, y compris déjà correct ; convertir seulement Soil/Grassland et vérifier l’effet de `till()` |
| `water`, `fertilizer` | Actions facultatives : `False` peut signifier aucune utilisation nécessaire |
| `utils_mine.go_to(x, y)` | Trajet XY via `utils_move`, sans creusement ni reset ; `go_to_yx` et variantes `warpless` gardent leur ordre |
| `utils_debug.reset` | Nettoyage manuel, distinct du `reset()` natif ; garde des workers et refus de trajet propagé |
| `utils_debug.sim` | Preset Hay par défaut ; seul `None` choisit les valeurs par défaut, les conteneurs vides restent vides ; Simulation requise |
| `profile_carrot` | Timing requis avant horloges/production |

Les helpers existants restent disponibles. Une absence d’appel automatique ne
rend pas un diagnostic manuel inutile ; leur suppression est un autre changement.

## Vérification

Ruff et les tests hôte vérifient syntaxe Python, contrats et géométrie simplifiée.
Le parseur du jeu vérifie son langage. Seuls une simulation ou un essai en partie
établissent le comportement natif et le débit. Le protocole de comparaison est
dans [les optimisations](../analyses/optimisations.md#mesurer-un-changement).
