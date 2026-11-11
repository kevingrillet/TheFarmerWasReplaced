# Sources et provenance

Synthèse des lectures effectuées du 8 au 10 novembre 2026, pour le build local
**26462009**. Les références figent ce qui a été étudié ; elles ne sont pas une
veille automatique. Le code externe n’est pas une validation native de nos variantes.

## Références principales

| Source | Apport / attribution |
| --- | --- |
| [msmith93 — jeu de base](https://github.com/msmith93/thefarmerwasreplaced/tree/7fef7c327e8d0b6ef34af2fafc3e5aeaf0b89823) | Polyculture Carrot/Wood, stratégies Power et Dinosaur |
| [msmith93 — DLC](https://github.com/msmith93/thefarmerwasreplaced/tree/cfe6e07d6f877b20349d5ecd75e2b92df5026f19) | Puzzles miniers, Coal/Rice, Mushroom, Goo par Tree ; conserver notre financement central |
| [msmith93 — Pumpkin](https://github.com/msmith93/thefarmerwasreplaced/tree/a26f758b235ee2016b9dff29b6e5235a00589f9c) | Pipeline single, notamment `claude/iteration_3_seam_polish.py` |
| [msmith93 — reset](https://github.com/msmith93/thefarmerwasreplaced/tree/28544222a2b1531c915b0646f8eb74971f4cc615) | Ordre d’achats TFWR ; ne décrit pas à lui seul un reset DLC |
| [Luzahe — TFWR](https://steamcommunity.com/sharedfiles/filedetails/?id=3586817011) | Compilation de cultures, polyculture et variantes |
| [Luzahe — DLC](https://steamcommunity.com/sharedfiles/filedetails/?id=3834856161) | Bamboo, Mushroom, pyramides et démineur ; Bamboo attribué à **NemoStein** |
| [Karada Giden Balik — Miner Master](https://steamcommunity.com/sharedfiles/filedetails/?id=3835682919) | Forage explosif soutenu ; scénario de succès conservé |
| [Lutfulla01 — gist](https://gist.github.com/Lutfulla01/2051aed1b8215308014f4ffe68e1a4a9/e59393d25393ade6d94dae8d5799a1984fef31b1) | Cactus prétrié, territoires Maze, raccourcis Dinosaur ; pistes non intégrées |
| [Reddit — Coal](https://www.reddit.com/r/TheFarmerWasReplaced/comments/1xpjhui/comment/19sdpoarjrfnk/) | Description collée par l’utilisateur : sondages courts, colonnes, arrêt à l’argile ; accès direct au commentaire bloqué lors de l’analyse |
| [Nagise — Hay Single](https://note.com/nagise/n/n4a2bca28cd81) | Colonnes de Grass et compagnons ; notre variante finale Bush 3×3 a été mesurée par l’utilisateur |
| [Vidéo Bush / petit champ](https://www.youtube.com/shorts/QmPLERJVToE) | Piste transmise par l’utilisateur pour la réduction de grille du Hay Single |

Les trois anciens scripts locaux `cheese_*`, d’origine externe non identifiée
dans le dépôt, ont été adaptés en `leaderboard_power_columns`,
`leaderboard_gold_reuse` et `leaderboard_bone_hybrid`. Les originaux ont été retirés
après migration ; garder ces noms autonomes. La production Power normale reprend
l’ordre de travail des colonnes, avec son propre financement et ses quotas.

Les guides Steam sont des compilations : conserver les attributions particulières
lors d’une reprise. La licence du dépôt ne remplace pas celle des sources externes.

## Éléments déjà adaptés

| Origine étudiée | Résultat local |
| --- | --- |
| Entretien Bamboo par lots | Deux vagues de cultures/couloirs et croissance contrôlée |
| Mushroom et Matchmaker | Préparation complète, appariement et compaction bornés |
| Pyramides | Conservation du sable, dégagement et reconstruction multi |
| Foret explosif | Scénarios manuels et descente profonde configurables |
| Carrot/Wood polyculture, Pumpkin pipeline, Power global | Six benchmarks `candidate`, séparés des références |
| Coal Reddit | `mine_coal` : colonnes attribuées explicitement, extrémités inspectées, tous les enfants rejoints |

Le gist Lutfulla01 annonce des durées de simulation hors Steam. Elles ne sont
pas ajoutées au tableau des scores : conditions et moteur ne sont pas établis
équivalents. Les pistes encore utiles sont dans [optimisations](optimisations.md).

## Références natives

Les contrats sont vérifiés contre les [textes officiels locaux](../README.md)
et, si nécessaire, les données/contrôleurs installés. Les extractions techniques
et les sauvegardes de travail restent locales et ignorées par Git. La complétion
de la sauvegarde ne modifie pas la couverture des références officielles.
