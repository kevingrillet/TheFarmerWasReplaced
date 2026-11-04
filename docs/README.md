# Documentation du jeu

Extraction des textes officiels de l’installation locale, en français et en anglais.

Les textes, illustrations et fiches IA sont des fichiers locaux ignorés par Git.
Seuls les dossiers avec leurs `.gitkeep`, les outils et cet index sont versionnés ;
`manifest.json` reste également local. Les liens ci-dessous deviennent accessibles
après la génération depuis une installation du jeu. Les fiches IA reprenant des
textes du jeu, elles suivent la même règle que les extractions complètes.

| Contenu | Français | English |
| --- | --- | --- |
| The Farmer Was Replaced | [Lire](tfwr/fr/README.md) | [Read](tfwr/en/README.md) |
| The Miner Was Replaced — DLC | [Lire](tmwr/fr/README.md) | [Read](tmwr/en/README.md) |

## Références pour les assistants IA

- [Jeu de base et langage](ai/tfwr.md)
- [DLC et minage](ai/tmwr.md) — à lire en complément du jeu de base.

Ces deux fichiers regroupent les contrats de l’API, les guides de mécaniques et
des catalogues compacts, à partir des textes anglais officiels. Ils ajoutent des
repères de lecture et les pièges de programmation, sans doublons de traduction,
paramètres d’affichage des scènes ni textes d’interface. Les tutoriels détaillés
du langage et les erreurs restent accessibles par liens. Les fichiers sont
régénérés par la même commande que l’extraction complète.

## Source et couverture

- Source : `TheFarmerWasReplaced_Data/StreamingAssets/Languages/{FR,EN}/`.
- Illustrations : `TheFarmerWasReplaced_Data/resources.assets` et `resources.assets.resS`.
- Application Steam : `2060160` ; build installé : `26410308`.
- Dans chaque langue : 65 pages du jeu et
  146 exemples interactifs convertis.
- Textes de référence : 620 entrées dans
  14 tables françaises ;
  634 entrées dans 15 tables anglaises.
  La table des noms de langues existe uniquement en anglais ; deux messages
  supplémentaires existent uniquement en français. Toutes les entrées présentes
  dans chaque langue sont conservées.
- Les guides, l’API, les entités, les sols, les ressources, les améliorations,
  les chapeaux, les classements, les commandes et les erreurs sont inclus.
- Les textes propres au minage sont rangés dans `tmwr/` ; les éléments communs
  sont dans `tfwr/`, avec des liens relatifs entre les deux.
- Les deux versions de la documentation sont celles fournies par le jeu ;
  aucune traduction ni correction des exemples n’est ajoutée.

Les pages sont accessibles quel que soit le niveau de déblocage de la sauvegarde.
Les macros de sortie, de statistiques et de coûts dépendant de la partie sont
[signalées comme données dynamiques](tfwr/fr/runtime.md). Les animations des
exemples sont remplacées par leur code ; leurs configurations et leur préparation
sont conservées. Les cinq illustrations statiques sont incluses.

Le [manifeste](manifest.json) contient les empreintes SHA-256 des fichiers source,
la couverture par langue, les clés exportées et les empreintes des fichiers générés.
Les sauvegardes et leurs anciens `__builtins__.py` ne servent pas de source.

## Actualiser après une mise à jour

Sur un nouveau clone, depuis la racine du dépôt avec Python 3.10 ou plus récent :

```powershell
python -m pip install -r requirements-docs.txt
python tools/extract_game_docs.py --extract-images
```

Une fois les illustrations extraites, les mises à jour textuelles n’ont besoin
que de la bibliothèque standard :

```powershell
python tools/extract_game_docs.py
python tools/extract_game_docs.py --check
```

L’export textuel et la vérification utilisent uniquement la bibliothèque standard.
Les illustrations déjà extraites sont réutilisées. Pour les réextraire également :

```powershell
python -m pip install -r requirements-docs.txt
python tools/extract_game_docs.py --extract-images
```

L’emplacement du jeu est lu depuis `TFWR_GAME_DIR` dans le fichier `.env` à la
racine du dépôt, puis depuis les valeurs par défaut si cette variable est absente.
Les variables d’environnement ont priorité sur le fichier. Un autre emplacement
peut être fourni avec `--game-dir "C:/chemin/du/jeu"`, qui a priorité sur les deux.
`.env.example` fournit une configuration Windows utilisant `%USERPROFILE%` pour
le dossier de sauvegarde. Ce marqueur est résolu par les outils du projet.
`--check` vérifie aussi les liens internes, les ancres et la couverture sans écrire.
Une régénération remplace les fichiers générés ; les anciens fichiers listés dans
le manifeste sont retirés s’ils ne font plus partie de l’export. Les autres fichiers
ne sont pas supprimés. Le jeu et les sauvegardes sont seulement lus.

## Attribution

Les textes, exemples et illustrations proviennent de The Farmer Was Replaced et
de son DLC. Leurs droits appartiennent à leurs auteurs respectifs ; la licence du
code de ce dépôt ne les remplace pas. Les crédits d’origine sont conservés dans
les [pages du jeu](tfwr/fr/credits.md).
