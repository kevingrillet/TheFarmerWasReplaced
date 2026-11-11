# Succès : scripts conservés

Les succès de cette partie sont terminés, confirmé par l’utilisateur le
11 novembre 2026. Il n’y a plus de liste de travaux ni de catalogue de succès
à maintenir dans la documentation.

[ZZAchievementDLC.py](../../Save0/ZZAchievementDLC.py) reste disponible pour une
autre sauvegarde ou un appel manuel :

```python
import ZZAchievementDLC

ZZAchievementDLC.run("pyramid")
```

`run()` sans argument exécute `SPECIFIC_TASKS + GRIND_TASKS`, selon les lignes
actives du fichier ; ne pas le lancer pour une simple collecte. Aucun filtrage
automatique Steam n’existe. Le script restaure la taille du champ entre tâches,
rejoint ses workers et conserve l’unique autorisation de `jump()` du programme.
Les scénarios renouvellent le terrain et consomment les ressources du défi.

Les collecteurs utilisés par le minage restent documentés dans le
[guide minier](mining.md#contraintes-des-collecteurs). Leur appel ne doit jamais
enchaîner la recherche d’une autre carte ou lancer la file des succès.
