# Documentation

## Projet

- [Architecture](dev/architecture.md) et [contrats de développement](dev/contracts.md).
- [Progression et minage](guides/mining.md), [benchmarks](benchmarks/README.md).
- [Optimisations et sources](analyses/README.md).
- [Scripts de succès conservés](guides/achievements.md) — succès terminés.
- [Installation, synchronisation et vérifications](../CONTRIBUTING.md).

## Références officielles locales

| Jeu | Français | English | Fiche IA |
| --- | --- | --- | --- |
| TFWR | [Lire](tfwr/fr/README.md) | [Read](tfwr/en/README.md) | [Langage et API](ai/tfwr.md) |
| TMWR | [Lire](tmwr/fr/README.md) | [Read](tmwr/en/README.md) | [Minage](ai/tmwr.md) |

Les textes et illustrations sont extraits de l’installation, sans dépendre des
déblocages de la sauvegarde. Ils restent locaux et ignorés par Git, avec le
[manifeste de couverture et d’empreintes](manifest.json). Les fiches IA sont
régénérées depuis les mêmes sources ; elles ne remplacent pas les détails de l’API.

## Source et mise à jour

Build Steam **26462009**, application `2060160`.
Par langue : 65 guides et
146 exemples interactifs ;
620 entrées FR et
634 EN. Source :
`TheFarmerWasReplaced_Data/StreamingAssets/Languages/{FR,EN}/` et `resources.assets`.
Les valeurs dépendant de la partie sont [signalées](tfwr/fr/runtime.md).

```sh
python tools/extract_game_docs.py
python tools/extract_game_docs.py --check
```

Ajouter `--extract-images` pour extraire les illustrations, après installation
de `requirements-docs.txt`. Le dossier du jeu est configuré dans `.env`.
Les droits des textes, exemples et images appartiennent à leurs auteurs ;
les [crédits du jeu](tfwr/fr/credits.md) sont conservés.
