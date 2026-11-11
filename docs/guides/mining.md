# Progression et minage

## Choisir un scénario

`main.py` termine `story_farm.run()`, puis `story_mining.run()`, prépare le stock
absolu `POWER_TARGET` et lance un seul scénario. Zéro désactive cette réserve.
Une erreur de mode, de cible ou de financement arrête l’enchaînement.

| `INFINITE_MODE` | Module | Usage |
| --- | --- | --- |
| `"resources"` | `story_infinite` | Objectifs croissants pour les ressources sélectionnées |
| `"mining"` | `story_mining_infinite` | Récolte par couches, activités comprises, mondes renouvelés |
| `"explosive"` | `story_mining_infinite_explosive` | Puits profond au foret explosif unique, puis normal sans carburant |
| `"fast"` | `story_mining_infinite_fast` | Forets ordinaires coopérant dans le même puits |

Les réglages de départ sont dans [main.py](../../Save0/main.py). Pour reprendre
directement une mine existante sans financement initial, lancer le fichier de
descente concerné. `main` peut financer Power et donc remplacer le terrain.
`story_mining.run()` reprend les upgrades DLC ; `run(True)` s’arrête au classement
souterrain. Les coûts restent dynamiques, la foreuse s’améliore avec `Unlocks.Mining`.

## Une ressource seulement

```python
import resource_manager

resource_manager.farm_current(Items.Coal, 500000)
```

La cible est le stock total. Le gestionnaire choisit le mode et finance ses
dépendances. Pour appeler le producteur directement : `mine_coal.farm_multi(cible)`
ou `farm_single(cible)`, sans financement implicite. Ces producteurs renouvellent
le terrain entre leurs lots. Coal seul ne lance ni Rice ni un puzzle.

`story_infinite.run([Items.Coal], "individual")` répète ces objectifs individuels.
Son mode `layers`, disponible après les déblocages nécessaires, utilise le monde
minier général même avec une seule ressource sélectionnée. Ses ressources par
défaut incluent les huit ressources DLC et il recharge Power entre les tours.

## Monde par couches

Le parent conserve une hauteur numérique. Les workers traitent leurs bandes puis
sont rejoints avant un puzzle ou une descente. Un relevé complet, plat et de
stabilité au moins 2 permet un pas de deux couches ; sinon le pas reste d’une.
Ne jamais dépasser deux en se fondant sur la stabilité du sol visible.

Un monde est borné à 256 couches, quatre champs de Rice et huit volumes maximaux
de pyramide financés avant préparation. Les réserves épuisées terminent le monde.
Le scénario renouvelle Power et cultive Bamboo entre les mondes. Huit mondes sans
gain pour une même ressource manquante arrêtent le grind.

## Descentes profondes

Les variantes `explosive` et `fast` partagent les collecteurs et une liste
`ACTIVITIES` : `treasure`, `pyramid`, `minesweeper`, `mushroom`. Commenter une entrée
la désactive ; liste vide pour descendre seulement. Mushroom est activé dans
les deux descentes ; il peut demander une longue préparation.

`TARGET_DEPTH = None` ne fixe aucun plafond ; `10000` vise z ≤ −10000.
`START_NEW_WORLD = False` reprend le terrain sans `clear()` ni financement.
`True` finance un nouveau monde au démarrage seulement : Power, Block des pyramides,
et Dynamite pour l’explosif. Aucune ferme n’est lancée pendant la descente.
Une activité en échec, Bedrock ou un creusement bloqué rend la main.

Le puits observe sa case et les quatre voisins exposés. Il peut manquer une ruine
éloignée ; les éboulements restent possibles et le souffle peut détruire une
structure cachée. Ces parcours ne récoltent pas tout le champ.

Le mode `fast` attribue chaque hauteur à un seul drone selon son rang modulo la
capacité. `dig()` modifie le terrain avant l’attente native, permettant de
chevaucher les creusements sans course entre contrôle du sol et excavation.
Conserver cette propriété exclusive, la reprise des rangs refusés par le parent
et les joins avant les activités. `BATCH_DEPTH` est un intervalle de jonction,
pas de renouvellement. `WORKER_TIMEOUT` borne les attentes ; Timing est requis.
La lecture native `get_pos_z(direction)` évite de se déplacer pour mesurer un voisin.

## Contraintes des collecteurs

| Ressource / activité | Contrat important |
| --- | --- |
| Block | Lots courts et forages espacés ; disponible sans Underground Senses |
| Coal | Sondes espacées d’au plus deux creusements, arrêt sur Coal visible sous/à côté. Joindre, traiter les nappes de haut en bas, puis colonnes disjointes avec inspection des extrémités pour les diagonales. Finir une direction avant l’autre ; jamais sous la nappe choisie |
| Coal, fin de monde | Retirer les sondes à Clay/Rock/Bedrock, terminer les autres puis renouveler ; 32 vagues maximum. Parent inclus dans la capacité : 32 secteurs 4×8 sur 32×32 pour une grande cible. Les poches cachées ne sont pas garanties |
| Iron / Quartz | Secteurs, suivi du filon puis retour au centre XY. Répartir un budget total de sondes, au plus 64 Coal ou 128 Iron ; jamais cette réserve entière par drone. `prospect_iron()` coûte 1 Coal, `prospect_quartz()` 1 Iron ; `None` ne signifie pas toujours absence de minerai |
| Mushroom | Préparer toute la strate et joindre avant les poussées. Comparer les quatre voisins, alterner lignes/colonnes, borner les réarrangements ; ne pas creuser sous un bloc transporté. Aucun temps de croissance |
| Dynamite | Un parent fusionne les indices ; seuls les blocs prouvés sûrs sont ouverts en parallèle. Paris isolés. Cache incrémental des contraintes et voisins calculés à la demande ; conserver la détection native résolu/explosé |
| Pyramide | Délimiter la fondation par quatre sondes cardinales puis bandes de dégagement ; arrêter sur Sand à conserver ou Limestone. Joindre avant construction ; financer avant de préparer un monde |
| Construction | Étages disjoints, joins avant l’étage supérieur. Le parent réserve le sommet pour éviter la disparition native de la ruine pendant les poses des enfants. Récolter le tournesol final |
| Carte | Une seule carte par appel, jamais la file des succès. Le `D` initial est l’activation déjà effectuée ; éliminer les boucles en coordonnées 3D. Une indication Basalt périmée ne permet de chercher qu’une couche dessous, sans descendre vers une nouvelle carte |
| Collecteurs partagés | Aucun financement, `clear()` ou `jump()`. Accès à une hauteur connue borné par l’écart, avec contrôle sans progrès. Mémoriser les strates/cartes/fondations déjà traitées avant de reprendre la descente |

`story_mining_infinite_explosive.protected_grounds`, `discover` et
`collect_activity` sont communs aux deux descentes. Les helpers d’excavation
restent dans `utils_mine` ; `excavate_layer` garde quatre résultats,
`excavate_band` ajoute la stabilité plafonnée à deux. `survey_surface` reste un
diagnostic en lecture seule. Voir les [contrats généraux](../dev/contracts.md).

Les tests ciblés sont `test_coal`, `test_mining_multi`, `test_mushroom`,
`test_dynamite_solver`, `test_layer_mining`, `test_explosive_deep`, `test_fast_mining`
et `test_achievement_dlc`, dans [tools](../../tools/).
