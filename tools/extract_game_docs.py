"""Export the installed game's documentation, without touching the game or saves.

The normal export and --check use only the Python standard library. Install
requirements-docs.txt and pass --extract-images to refresh the five Unity images.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from build_ai_docs import build_ai_docs
from project_config import load_project_config

REPO = Path(__file__).resolve().parents[1]
DLC_UNLOCKS = set(
    """
    mining rice coal iron pyramid quartz ore_boost jump prospecting drill
    debug_place underground_senses petrified_pumpkins special_soils bamboo
    dynamite treasure_map mushrooms explosive_drill underground_leaderboard
""".split()
)
DLC_CODE = set(
    """
    dig prospect_iron prospect_quartz place push can_push jump hover get_hover
    get_pos_z get_hardness get_stability
""".split()
)
DLC_OBJECTS = set(
    """
    rice bamboo dirt rock clay block_blue block_red block_green coal iron quartz
    limestone sand bedrock petrified_pumpkin loam perlite dynamite dynamite_ground
    soot basalt treasure_map_ground treasure_path_ground treasure_goal_ground
    underground_treasure mushroom dry_rice_terrace rice_terrace
""".split()
)
DLC_ITEMS = set("bamboo block coal dynamite iron mushroom quartz rice".split())
DLC_HATS = set(
    """
    explosive_drill bucket coal_hat rice_hat quartz_hat bamboo_hat dynamite_hat
    mushroom_hat mining_hat
""".split()
)
DLC_ERRORS = set(
    """
    error_explosive_drill_already_used error_non_jumpable_unlock
    error_only_first_drone_can_jump error_can_only_jump_once error_dig_not_allowed
    error_plant_not_allowed error_jump_not_allowed error_place_too_high
    warning_not_enough_coal warning_not_enough_iron warning_cannot_place_ground
    option_tooltip_avalanche_particles
""".split()
)
IMAGES = {
    "PlayButton": "tfwr",
    "Breakpoints": "tfwr",
    "ImportsInOnePicture": "tfwr",
    "LeaderboardSetup": "tfwr",
    "UndergroundLeaderboardSetup": "tmwr",
}
REFERENCE_NAMES = {
    "button_tooltips": (
        "Commandes, options et raccourcis",
        "Controls, options and shortcuts",
    ),
    "buttons": ("Libellés des boutons", "Button labels"),
    "code_tooltips": (
        "API, méthodes, types et mots-clés",
        "API, methods, types and keywords",
    ),
    "execute_errors": ("Erreurs d’exécution", "Runtime errors"),
    "hat_tooltips": ("Chapeaux", "Hats"),
    "item_tooltips": ("Objets et ressources", "Items and resources"),
    "languages": ("Langues", "Languages"),
    "leaderboard_tooltips": ("Objectifs des classements", "Leaderboard targets"),
    "object_tooltips": ("Entités et sols", "Entities and grounds"),
    "options": ("Libellés des options", "Option labels"),
    "other": ("Autres textes de l’interface", "Other interface text"),
    "parse_errors": ("Erreurs de syntaxe", "Syntax errors"),
    "popup_warnings": ("Messages de confirmation", "Confirmation messages"),
    "unlock_tooltips": ("Améliorations et déblocages", "Upgrades and unlocks"),
    "warnings": ("Avertissements", "Warnings"),
}
ENTRY = re.compile(r"^@([\w]+)\s*=[ \t]?(.*?)(?=^@[\w]+\s*=|\Z)", re.M | re.S)
LINK = re.compile(r"(!?)\[([^\]\n]*)\]\(([^)\n]+)\)")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(source: str, target: str) -> str:
    path, separator, anchor = target.partition("#")
    result = Path(os.path.relpath(path, str(Path(source).parent))).as_posix()
    return result + (separator + anchor if separator else "")


def parse_strings(text: str) -> dict[str, str]:
    matches = list(ENTRY.finditer(text))
    if not matches or text[: matches[0].start()].strip():
        raise ValueError("Unexpected text outside localization entries")
    entries = {m[1]: m[2].strip() for m in matches}
    if len(entries) != len(matches):
        raise ValueError("Duplicate localization keys")
    return entries


def scope_for_key(key: str) -> str:
    for prefix, ids in (
        ("code_tooltip_", DLC_CODE),
        ("item_descr_", DLC_ITEMS),
        ("object_descr_", DLC_OBJECTS),
        ("hat_descr_", DLC_HATS),
        ("unlock_descr_", DLC_UNLOCKS),
        ("multi_unlock_descr_", DLC_UNLOCKS),
    ):
        if key.startswith(prefix):
            return "tmwr" if key[len(prefix) :] in ids else "tfwr"
    if key.startswith("lb_descr_"):
        name = key.removeprefix("lb_descr_").removesuffix("_single")
        if name in {
            "fastest_underground_reset",
            "rice",
            "ores",
            "bamboo",
            "dynamite",
            "mushrooms",
            "pyramids",
            "treasure_map",
        }:
            return "tmwr"
    if key.startswith(("runtime_ground_", "runtime_mushroom_")):
        return "tmwr"
    return "tmwr" if key in DLC_UNLOCKS | DLC_ERRORS else "tfwr"


def scope_for_doc(path: str) -> str:
    stem = Path(path).stem
    if path.startswith("unlocks/") and (stem in DLC_UNLOCKS or stem == "mushroom"):
        return "tmwr"
    return "tfwr"


def fenced(text: str, language: str = "python") -> str:
    runs = re.findall(r"`+", text)
    fence = "`" * max(3, 1 + max((len(run) for run in runs), default=0))
    return f"\n\n{fence}{language}\n{text.strip(chr(10))}\n{fence}\n\n"


def markdown_spacing(text: str) -> str:
    """Normalize prose spacing while keeping fenced example code intact."""
    result = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^(`{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1] == fence:
                fence = None
            result.append(line)
        elif fence is not None:
            result.append(line)
        else:
            line = line.rstrip()
            if line == "---" or re.match(r"^#{1,6} |^\*\*.+\*\*$", line):
                if result and result[-1]:
                    result.append("")
                result.extend((line, ""))
            elif line or not result or result[-1]:
                result.append(line)
    return "\n".join(result).strip()


REPOSITORY_LINKS = {
    "analyses/README.md",
    "dev/architecture.md",
    "dev/contracts.md",
    "guides/mining.md",
    "guides/achievements.md",
    "benchmarks/README.md",
    "../CONTRIBUTING.md",
}


class Exporter:
    def __init__(self, game: Path, output: Path, extract_images: bool):
        self.game = game
        self.data = game / "TheFarmerWasReplaced_Data"
        self.languages = self.data / "StreamingAssets/Languages"
        self.output = output
        self.extract_images = extract_images
        self.files: dict[str, bytes] = {}
        self.sources: dict[str, str] = {}
        self.coverage: dict[str, dict] = {}
        self.provenance: dict[str, list[str]] = {}
        self.registry: dict[str, str] = {}
        self.labels: dict[str, str] = {}
        self.lang = ""
        self.examples = 0
        self.entry_count = 0
        self.build_id = "unknown"

    def tr(self, french: str, english: str) -> str:
        return french if self.lang == "fr" else english

    def read(self, path: Path) -> str:
        data = path.read_bytes()
        self.sources[path.relative_to(self.game).as_posix()] = digest(data)
        return data.decode("utf-8-sig")

    def put(self, path: str, text: str, sources: list[str] | None = None):
        if path.endswith(".md"):
            text = markdown_spacing(text)
        self.files[path] = (text.strip() + "\n").encode("utf-8")
        if sources:
            self.provenance[path] = sources

    def page(self, scope: str, name: str) -> str:
        return f"{scope}/{self.lang}/{name}"

    def register(self, target: str, output: str):
        if target in self.registry:
            raise ValueError(f"Duplicate link target: {target}")
        self.registry[target] = output

    def image_files(self):
        previous_sources = {}
        manifest = self.output / "manifest.json"
        if manifest.is_file():
            previous_sources = json.loads(manifest.read_text(encoding="utf-8"))[
                "source_sha256"
            ]
        for name in ("resources.assets", "resources.assets.resS"):
            path = self.data / name
            key = path.relative_to(self.game).as_posix()
            self.sources[key] = digest(path.read_bytes())
            if (
                not self.extract_images
                and key in previous_sources
                and previous_sources[key] != self.sources[key]
            ):
                raise SystemExit("Unity resources changed; rerun with --extract-images")
        if self.extract_images:
            try:
                import UnityPy
            except ImportError as exc:
                raise SystemExit(
                    "Install requirements-docs.txt to use --extract-images"
                ) from exc
            import io

            asset = self.data / "resources.assets"
            env = UnityPy.load(str(asset))
            for obj in env.objects:
                if obj.type.name != "Texture2D":
                    continue
                texture = obj.read()
                if texture.m_Name in IMAGES:
                    path = f"{IMAGES[texture.m_Name]}/assets/{texture.m_Name}.png"
                    stream = io.BytesIO()
                    texture.image.save(stream, format="PNG")
                    self.files[path] = stream.getvalue()
        for name, scope in IMAGES.items():
            path = f"{scope}/assets/{name}.png"
            if path not in self.files:
                if not (self.output / path).is_file():
                    raise SystemExit(
                        f"Missing {path}; first run requires --extract-images"
                    )
                self.files[path] = (self.output / path).read_bytes()
            self.provenance[path] = [
                f"TheFarmerWasReplaced_Data/resources.assets#Texture2D/{name}"
            ]

    def code_examples(self, text: str) -> str:
        def replace(match):
            self.examples += 1
            raw = match[1].lstrip()
            config, end = json.JSONDecoder().raw_decode(raw)
            rest = raw[end:].strip()
            setup, code = rest.removeprefix("#SETUP").split("#CODE", 1)
            details = self.tr(
                "Configuration de l’exemple dans le jeu",
                "In-game example configuration",
            )
            result = fenced(code.strip("\n"))
            result += f"<details>\n<summary>{details}</summary>\n\n"
            result += fenced(json.dumps(config, ensure_ascii=False, indent=2), "json")
            if setup.strip():
                result += self.tr("Préparation de la scène :", "Scene setup:")
                result += fenced(setup.strip("\n"))
            return result + "</details>\n\n"

        return re.sub(r"\{\{codeexample\s*(.*?)\}\}", replace, text, flags=re.S)

    def convert(self, text: str, output: str) -> str:
        # Convert the game's multiline backtick blocks before introducing fences.
        text = re.sub(
            r"`([^`]*)`", lambda m: fenced(m[1]) if "\n" in m[1] else m[0], text
        )
        text = self.code_examples(text)
        text = re.sub(r"\{\{@([\w]+)\}\}", lambda m: self.labels[m[1]], text)
        text = re.sub(
            r"<spoiler=([^>]+)>",
            lambda m: f"\n\n<details>\n<summary>{html.escape(m[1])}</summary>\n\n",
            text,
        )
        text = text.replace("</spoiler>", "\n\n</details>\n\n")
        text = re.sub(r"</?(?:columns|dlc|unlock(?:=[^>]+)?)>", "\n", text)
        text = text.replace("<right>", "\n\n")

        def dynamic(match):
            token = match[1].strip()
            label = self.tr("Valeur dynamique", "Runtime value")
            target = relative(output, self.page("tfwr", "runtime.md"))
            return f"[{label} : `{token}`]({target})"

        def link(match):
            image, label, target = match.groups()
            if target.startswith(("https://", "http://", "mailto:", "#")):
                return match[0]
            if target.startswith("persistent_data_path/"):
                return f"[{label}]({relative(output, self.page('tfwr', 'runtime.md'))})"
            if target in IMAGES:
                image_path = f"{IMAGES[target]}/assets/{target}.png"
                return f"![{target}]({relative(output, image_path)})"
            if target == "{1}":
                return f"{label} (`{{1}}`)"
            if target not in self.registry:
                raise ValueError(f"Unmapped link {target!r} in {output}")
            return f"{image}[{label}]({relative(output, self.registry[target])})"

        text = LINK.sub(link, text)
        # Four braces occur in templates that are later formatted by the game.
        text = re.sub(r"\{\{\{\{(.*?)\}\}\}\}(?!\})", dynamic, text)
        text = re.sub(r"\{\{([^{}]+)\}\}", dynamic, text)
        if output.endswith("/home.md"):
            text = re.sub(r"^(\[[^\n]+\]\([^\n]+\))\s*$", r"- \1", text, flags=re.M)
        return markdown_spacing(text)

    def localization(self, language: str):
        self.lang = language.lower()
        self.registry = {}
        self.labels = {}
        self.examples = 0
        self.entry_count = 0
        folder = self.languages / language
        documents = {
            p.relative_to(folder / "docs").as_posix(): self.read(p)
            for p in sorted((folder / "docs").rglob("*.md"))
        }
        tables = {
            p.stem: parse_strings(self.read(p))
            for p in sorted((folder / "Strings").glob("*.txt"))
        }
        unknown = tables.keys() - REFERENCE_NAMES.keys()
        if unknown:
            raise ValueError(f"Unknown string tables: {unknown}")
        for table in tables.values():
            for key, value in table.items():
                if key in self.labels:
                    raise ValueError(f"Duplicate global localization key: {key}")
                self.labels[key] = value
        for name in documents:
            self.register("docs/" + name, self.page(scope_for_doc(name), name))
        for table_name, entries in tables.items():
            for key in entries:
                path = self.page(scope_for_key(key), f"reference/{table_name}.md")
                self.register("@" + key, f"{path}#{key}")
                for prefix, category in (
                    ("code_tooltip_", "functions"),
                    ("item_descr_", "items"),
                    ("object_descr_", "objects"),
                    ("unlock_descr_", "unlocks"),
                ):
                    if key.startswith(prefix):
                        self.register(
                            category + "/" + key[len(prefix) :], f"{path}#{key}"
                        )
        objects = tables["object_tooltips"]
        for key in objects:
            if key.startswith("object_descr_"):
                name = key.removeprefix("object_descr_")
                target = self.registry["objects/" + name]
                self.registry["grounds/" + name.removesuffix("_ground")] = target
        # The terrace types have guide text, but no dedicated localized tooltip.
        for name in ("dry_rice_terrace", "rice_terrace"):
            self.register("grounds/" + name, self.page("tmwr", "unlocks/rice.md"))
        self.registry["unlocks/expand"] = self.registry["docs/unlocks/expand_1.md"]
        self.register("tech_tree", self.page("tfwr", "reference/unlock_tooltips.md"))

        for name, text in documents.items():
            path = self.registry["docs/" + name]
            source = f"{language}/docs/{name}"
            self.put(path, self.convert(text, path), [source])
        for table_name, entries in tables.items():
            for scope in ("tfwr", "tmwr"):
                selected = {
                    k: v for k, v in entries.items() if scope_for_key(k) == scope
                }
                if not selected:
                    continue
                self.entry_count += len(selected)
                path = self.page(scope, f"reference/{table_name}.md")
                title = REFERENCE_NAMES[table_name][0 if self.lang == "fr" else 1]
                text = f"# {title}\n\n"
                text += self.tr(
                    "Clés et textes extraits de", "Keys and text extracted from"
                )
                text += f" `Languages/{language}/Strings/{table_name}.txt`.\n\n"
                text += (
                    self.tr(
                        "Les paramètres `{0}`, `{1}`, etc. sont remplacés par le jeu à l’exécution.",
                        "Parameters such as `{0}` and `{1}` are replaced by the game at runtime.",
                    )
                    + "\n\n"
                )
                text += "\n\n" + self.tr("## Index\n\n", "## Index\n\n")
                for key in selected:
                    display = (
                        key.removeprefix("code_tooltip_")
                        if table_name == "code_tooltips"
                        else key
                    )
                    text += f"- [`{display}`](#{key})\n"
                text += "\n"
                for key, value in selected.items():
                    display = (
                        key.removeprefix("code_tooltip_")
                        if table_name == "code_tooltips"
                        else key
                    )
                    text += f'<a id="{key}"></a>\n\n## `{display}`\n\n'
                    text += self.convert(value, path) + "\n\n"
                self.put(
                    path,
                    text,
                    [f"{language}/Strings/{table_name}.txt#{k}" for k in selected],
                )
        self.runtime_page()
        for scope in ("tfwr", "tmwr"):
            self.language_index(scope)
        self.coverage[language] = {
            "guide_pages": len(documents),
            "interactive_examples": self.examples,
            "localization_entries": self.entry_count,
            "string_tables": len(tables),
            "tfwr_guide_pages": sum(scope_for_doc(p) == "tfwr" for p in documents),
            "tmwr_guide_pages": sum(scope_for_doc(p) == "tmwr" for p in documents),
            "dlc_code_tooltips": sorted(DLC_CODE),
        }

    def runtime_page(self):
        self.put(
            self.page("tfwr", "runtime.md"),
            self.tr(
                """# Données calculées pendant la partie

Les pages extraites décrivent la version installée du jeu, indépendamment des
déblocages de la sauvegarde. Les balises qui masquent du contenu verrouillé ont été
retirées ; les textes et les exemples officiels sont conservés, y compris leurs
éventuelles incohérences.

Les macros suivantes sont remplies par le moteur pendant une partie :

- `output` : sortie courante du programme.
- `itemblock stats_sum` et `itemblock stats_best` : production récente et records personnels.
- `itemblock tooltip` et `itemblock tooltip_ground` : rendements de la case survolée.
- `itemblock cost object {0}` et `itemblock cost unlock {0}` : coûts dépendant du niveau.
- Les paramètres `{0}`, `{1}`, etc. des messages : valeurs fournies au moment de l’affichage.

Ces valeurs ne sont pas remplacées par celles d’une sauvegarde particulière.
Utiliser `get_cost()`, `num_items()`, `num_unlocked()` et les infobulles du jeu
pour obtenir les valeurs de la partie en cours. Les constantes du moteur non
présentes dans les fichiers de documentation ne sont pas déduites.

Les liens `persistent_data_path/...` du jeu désignent son dossier de données :
`%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/`.
Il contient notamment `Saves/`, `Backup/` et `output.txt`.

Les animations des exemples sont remplacées par leur code. Leur configuration JSON
et leur préparation `#SETUP` sont conservées dans des sections repliables.
Les cinq illustrations statiques de la documentation sont extraites des ressources Unity.
""",
                """# Values calculated during gameplay

This export documents the installed game version independently of save unlocks.
Visibility gates have been removed. Official text and examples are preserved,
including any inconsistencies in the source.

The game engine fills the following macros during gameplay:

- `output`: the program's current output.
- `itemblock stats_sum` and `itemblock stats_best`: recent production and personal records.
- `itemblock tooltip` and `itemblock tooltip_ground`: yields of the hovered tile.
- `itemblock cost object {0}` and `itemblock cost unlock {0}`: level-dependent costs.
- Message parameters such as `{0}` and `{1}`: values supplied when displayed.

These values are not filled from a particular save. Use `get_cost()`, `num_items()`,
`num_unlocked()` and in-game tooltips to obtain values for the current game.
Engine constants absent from the documentation files are not inferred.

The game's `persistent_data_path/...` links refer to its data directory:
`%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/`.
It contains `Saves/`, `Backup/` and `output.txt`.

Interactive animations are replaced by code. Their JSON configuration and `#SETUP`
code are preserved in collapsible sections. The five static documentation images
are extracted from the Unity resources.
""",
            ),
        )

    def language_index(self, scope: str):
        path = self.page(scope, "README.md")
        name = (
            "The Farmer Was Replaced"
            if scope == "tfwr"
            else "The Miner Was Replaced — DLC"
        )
        text = f"# {name} — {self.lang.upper()}\n\n"
        if scope == "tmwr":
            shared = relative(path, self.page("tfwr", "README.md"))
            text += self.tr(
                f"Documentation du DLC. Le [langage et les fonctions communes]({shared}) sont documentés avec le jeu de base.\n\n",
                f"DLC documentation. The [language and shared functions]({shared}) are documented with the base game.\n\n",
            )
        else:
            text += self.tr(
                "[Sommaire original du jeu](home.md) · [Données dynamiques](runtime.md)\n\n",
                "[Original game contents](home.md) · [Runtime values](runtime.md)\n\n",
            )
        text += self.tr("## Guides\n\n", "## Guides\n\n")
        guides = sorted(
            p
            for p in self.files
            if p.startswith(f"{scope}/{self.lang}/")
            and "/reference/" not in p
            and not p.endswith(("README.md", "runtime.md"))
        )
        for guide in guides:
            body = self.files[guide].decode("utf-8")
            heading = re.search(r"^# (.+)$", body, re.M)
            title = heading[1] if heading else Path(guide).stem
            text += f"- [{title}]({relative(path, guide)})\n"
        text += self.tr("\n## Références\n\n", "\n## Reference\n\n")
        for table_name, titles in REFERENCE_NAMES.items():
            target = self.page(scope, f"reference/{table_name}.md")
            if target in self.files:
                title = titles[0 if self.lang == "fr" else 1]
                text += f"- [{title}]({relative(path, target)})\n"
        if scope == "tmwr":
            text += self.tr(
                "\n## Fonctions propres au DLC\n\n", "\n## DLC functions\n\n"
            )
            for function in sorted(DLC_CODE):
                target = self.registry["functions/" + function]
                text += f"- [`{function}()`]({relative(path, target)})\n"
        self.put(path, text)

    def generate(self):
        repository_index = ""
        if all((self.output / path).is_file() for path in REPOSITORY_LINKS):
            repository_index = """## Projet

- [Architecture](dev/architecture.md) et [contrats de développement](dev/contracts.md).
- [Progression et minage](guides/mining.md), [benchmarks](benchmarks/README.md).
- [Optimisations et sources](analyses/README.md).
- [Scripts de succès conservés](guides/achievements.md) — succès terminés.
- [Installation, synchronisation et vérifications](../CONTRIBUTING.md).
"""
        manifest = self.game.parent.parent / "appmanifest_2060160.acf"
        if manifest.is_file():
            match = re.search(
                r'"buildid"\s+"(\d+)"', manifest.read_text(encoding="utf-8")
            )
            if match:
                self.build_id = match[1]
        self.image_files()
        for scope in ("tfwr", "tmwr", "ai"):
            self.files[f"{scope}/.gitkeep"] = b""
        for language in ("FR", "EN"):
            self.localization(language)
        for path, (text, sources, coverage) in build_ai_docs(
            self.files, self.build_id
        ).items():
            self.put(path, text, sources)
            self.coverage[path] = coverage
        for scope, name in (
            ("tfwr", "The Farmer Was Replaced"),
            ("tmwr", "The Miner Was Replaced — DLC"),
        ):
            self.put(
                f"{scope}/README.md",
                f"""# {name}

- [Documentation en français](fr/README.md)
- [Documentation in English](en/README.md)
- [AI coding reference](../ai/{scope}.md)
- [Source, extraction et couverture](../README.md)

Build Steam de la source : `{self.build_id}`.
""",
            )
        self.put(
            "README.md",
            f"""# Documentation

{repository_index}
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

Build Steam **{self.build_id}**, application `2060160`.
Par langue : {self.coverage['EN']['guide_pages']} guides et
{self.coverage['EN']['interactive_examples']} exemples interactifs ;
{self.coverage['FR']['localization_entries']} entrées FR et
{self.coverage['EN']['localization_entries']} EN. Source :
`TheFarmerWasReplaced_Data/StreamingAssets/Languages/{{FR,EN}}/` et `resources.assets`.
Les valeurs dépendant de la partie sont [signalées](tfwr/fr/runtime.md).

```sh
python tools/extract_game_docs.py
python tools/extract_game_docs.py --check
```

Ajouter `--extract-images` pour extraire les illustrations, après installation
de `requirements-docs.txt`. Le dossier du jeu est configuré dans `.env`.
Les droits des textes, exemples et images appartiennent à leurs auteurs ;
les [crédits du jeu](tfwr/fr/credits.md) sont conservés.
""",
        )
        self.validate()
        metadata = {
            "format_version": 1,
            "steam_app_id": "2060160",
            "steam_build_id": self.build_id,
            "coverage": self.coverage,
            "source_sha256": dict(sorted(self.sources.items())),
            "provenance": dict(sorted(self.provenance.items())),
            "output_sha256": {
                p: digest(data) for p, data in sorted(self.files.items())
            },
        }
        self.put("manifest.json", json.dumps(metadata, ensure_ascii=False, indent=2))

    def validate(self):
        errors = []
        for path, data in self.files.items():
            if not path.endswith(".md"):
                continue
            text = data.decode("utf-8")
            if "{{" in text or re.search(
                r"</?(?:unlock|columns|dlc|spoiler)[=>]", text
            ):
                errors.append(f"Unconverted game markup: {path}")
            for match in LINK.finditer(text):
                target = unquote(match[3])
                if re.match(r"^[\w+.-]+:", target):
                    continue
                target_path, _, anchor = target.partition("#")
                normalized = (
                    os.path.normpath(str(Path(path).parent / target_path))
                    if target_path
                    else path
                )
                normalized = Path(normalized).as_posix()
                if (
                    path == "README.md"
                    and normalized in REPOSITORY_LINKS
                    and (self.output / normalized).is_file()
                ):
                    continue
                if normalized not in self.files and normalized != "manifest.json":
                    errors.append(f"Missing target: {path} -> {target}")
                elif anchor and normalized in self.files:
                    contents = self.files[normalized].decode("utf-8")
                    if f'id="{anchor}"' not in contents:
                        errors.append(f"Missing anchor: {path} -> {target}")
        if errors:
            raise ValueError("\n".join(errors))

    def finish(self, check: bool) -> int:
        previous = {}
        manifest_path = self.output / "manifest.json"
        if manifest_path.is_file():
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get(
                "output_sha256", {}
            )
        changed = [
            p
            for p, data in self.files.items()
            if not (self.output / p).is_file() or (self.output / p).read_bytes() != data
        ]
        stale = [p for p in previous if p not in self.files]
        if check:
            if changed or stale:
                print(
                    f"Out of date: {len(changed)} changed/missing, {len(stale)} obsolete files"
                )
                for path in changed[:10] + stale[:10]:
                    print(path)
                return 1
        else:
            for path in changed:
                target = self.output / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.files[path])
            for path in stale:
                target = (self.output / path).resolve()
                # Only remove individual generated files contained in this docs tree.
                if not target.is_relative_to(self.output.resolve()):
                    raise ValueError(f"Unsafe obsolete manifest path: {path}")
                if target.is_file():
                    target.unlink()
        print(
            f"{'Verified' if check else 'Exported'} {len(self.files)} files; Steam build {self.build_id}"
        )
        print(json.dumps(self.coverage, ensure_ascii=True))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--output", type=Path, default=REPO / "docs")
    parser.add_argument("--extract-images", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = load_project_config()
    exporter = Exporter(
        (args.game_dir or config["TFWR_GAME_DIR"]).resolve(),
        args.output.resolve(),
        args.extract_images,
    )
    exporter.generate()
    return exporter.finish(args.check)


if __name__ == "__main__":
    sys.exit(main())
