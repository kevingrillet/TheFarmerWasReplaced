# Optimisations

## Mesurer un changement

Comparer un objectif complet valide, préparation et joins compris, avec mêmes
déblocages, taille, stocks, financement et seeds. Pour un grind, mesurer la
ressource nette par minute et distinguer démarrage et régime établi. Tester
plusieurs seeds et les capacités utiles ; l’essai arrêté sur erreur ne compte pas.

`simulate()` fournit un essai reproductible ; le leaderboard fournit la campagne
officielle. Une durée seule ne prouve pas la cible atteinte. Le CSV Steam contient
le meilleur score publié, sans garantir qu’il provient du code courant ; une
régression doit être retravaillée, pas ajoutée à un historique de temps plus lents.

Tests hôte et parseur valident des contrats, pas la croissance, la physique ni un
gain de vitesse. Les résultats externes restent des déclarations de leurs auteurs.

## Coûts à garder en tête

Référence : [Timing](../tfwr/en/unlocks/timing.md) et les tooltips du build local.

| Opération | Coût documenté |
| --- | --- |
| Appel direct, variable, import et accès au module | Gratuits ; le code exécuté reste payant |
| Fonction/module affecté ou passé en argument | Référence indirecte payante ; éviter les registres dans les boucles chaudes |
| Calcul binaire, comparaison, branche, indexation | Généralement un tick, plus l’évaluation des valeurs |
| `move`, `plant`, `harvest`, `spawn_drone` réussis | 200 ticks ; les refus suivent leur propre contrat |
| `till` | 200 ticks : garder la lecture qui évite un labour inutile |
| Lectures de stock, position, mesure, déblocage | Généralement un tick |
| `list(collection)` / `dict(dictionary)` | `1 + n` / `1 + 2n` ticks |
| `wait_for` | Un tick si terminé ; sinon attente effective |
| `get_time`, `get_tick_count`, `quick_print` | Gratuits, hors construction de leurs arguments |
| `print` | Une seconde, non accélérée par la vitesse |
| `dig` | Dureté / force du foret, en secondes ; Speed et Power n’accélèrent pas cette durée |

Réduire les trajets et amortir les créations de drones peut rapporter davantage
que retirer une observation utile. Mettre en cache seulement les données encore
valides ; les stocks et le terrain peuvent changer pendant le travail des enfants.

## État des pistes

| Sujet | État / essai encore utile |
| --- | --- |
| Carrot et Wood polyculture | Variantes single/multi déjà créées ; comparer `strategy="candidate"` aux références |
| Pumpkin single | Pipeline déjà créé ; mesurer préparation complète puis réparations contre la référence |
| Power | Comparer pétales globaux, référence et colonnes continues ; simplifier les trajets ne garantit pas le bonus global ×8 |
| Cactus | Gist Lutfulla01 : tester d’abord cache et bornes au dernier échange, puis prétri par replantation dans un essai distinct |
| Maze | Grand labyrinthe réutilisé avec territoires : arbitrage unique du trésor, fin d’exploration et joins à concevoir avant adaptation |
| Dinosaur | Cycle indexé avec raccourcis, à comparer à notre hybride ; seuil dépendant de la taille, un seul chapeau, vérifier le gain Bone |
| Reset | Un reset global a terminé en partie ; comparer l’ordre d’achat et le coût total avant de changer les producteurs |
| Coal | Stratégie par nappes intégrée ; mesurer Coal net/minute face au minage général, sans confondre récupération par monde et débit |
| Mine profonde `fast` | Chevauchement des forets implémenté ; mesurer le débit natif, les contrôles de sol et le temps des activités |
| Goo par Tree | Piste étudiée mais non intégrée ; vérifier le coût complet, le financement et l’intérêt hors benchmark |

Les modes et candidats disponibles sont dans le [guide des benchmarks](../benchmarks/README.md),
les détails miniers dans le [guide de minage](../guides/mining.md). Les origines
des idées et les révisions consultées sont dans [sources](sources.md).

## Points de vigilance des prochains essais

- Cactus : un plant immature garde sa taille lors d’une replantation ; une
  récolte en chaîne peut invalider plusieurs entrées du cache.
- Maze : deux cartes locales incomplètes peuvent attribuer le même trésor à
  deux drones. Le secours après attente ne remplace pas un arbitrage.
- Dinosaur : un seuil fixe de 400 n’est pas adapté aux petites grilles ; garder
  une marge sûre devant la queue et tester l’absence de pomme.
- Coal : 2 unités par bloc avec Ore Boost dans le build étudié ; les éboulements
  ne rapportent rien. Les nappes minces peuvent avoir des prolongements diagonaux.
  Les coûts de prospection du fer consomment du Coal, même sans gain de fer.
