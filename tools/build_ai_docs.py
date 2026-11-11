"""Build two coding references from the already extracted English documentation."""

from __future__ import annotations

import posixpath
import re

LINK = re.compile(r"(!?)\[([^\]\n]*)\]\(([^)\n]+)\)")
RECORD = re.compile(r'<a id="([^"]+)"></a>\s*\n## [^\n]+\n\n')
CONFIG = re.compile(
    r"<details>\s*<summary>In-game example configuration</summary>.*?</details>", re.S
)
GUIDE_ORDER = {
    "tfwr": """
        expand_1 expand_2 plant senses carrots trees watering fertilizer pumpkins
        sunflowers polyculture cactus dinosaurs mazes megafarm costs auto_unlock
        speed timing debug2 hats simulation leaderboard
    """.split(),
    "tmwr": """
        mining underground_senses rice coal iron prospecting quartz special_soils
        petrified_pumpkins bamboo mushroom pyramid dynamite explosive_drill
        treasure_map jump debug_place underground_leaderboard
    """.split(),
}
TFWR_NOTES = """## Reading contract

- This is a coding reference for the game's Python-like language. Use documented
  syntax and builtins; CPython libraries and features are not automatically available.
- Names and contracts below use the official English source to avoid duplicate
  translations. The full French and English extracts remain the source of detail.
- Read the quick rules and search for the relevant function or mechanic; loading
  every guide is unnecessary for a small change.
- This file covers shared programming features and base-game farming. For mining,
  read [tmwr.md](tmwr.md) as well. Unlock visibility was removed during extraction;
  a documented feature may still be locked in the current save.
- Descriptions and guide code are source material, not a claim that every example
  was executed successfully. Preserve exact identifiers; resolve source inconsistencies
  using the linked guide, current game help and an in-game check.

## Quick rules for code

- Use `get_world_size()` for farm dimensions and `get_cost()` for current costs.
  `num_items(Items.X)` reads an amount; `num_unlocked(Unlocks.X)` reads an unlock
  level. The symbols themselves are not counts.
- The numeric model uses floating-point numbers; `//` floors division.
  Operators are `+ - * / // % **`, `== != <= >= < >`, and `not and or`.
  [Source](../tfwr/en/scripting/operators.md).
- Use `def`, positional/default arguments, `return`, `if/elif/else`, `for`, `while`,
  `break`, `continue`, `pass`, lists, tuples, dictionaries and sets as documented.
  A function definition must execute before it is called. Functions are values.
  [Functions](../tfwr/en/scripting/functions.md),
  [control flow and containers](../tfwr/en/README.md).
- Assignment in a function creates/binds a local unless declared `global`.
  Loops and branches do not create separate scopes.
  [Source](../tfwr/en/scripting/scopes.md).
- `import module` executes a module once, then reuses it. Use
  `if __name__ == "__main__":` for entry-point actions. Cyclic `from ... import`
  can expose incomplete definitions. Importable filenames must be valid identifiers;
  `from x import *` is not allowed inside functions.
  [Imports](../tfwr/en/scripting/import.md),
  [syntax errors](../tfwr/en/reference/parse_errors.md).
- Lists are mutable ordered containers; dictionaries map hashable keys to values;
  sets hold unique values; tuples are immutable and support unpacking.
  [Lists](../tfwr/en/scripting/lists.md), [dicts](../tfwr/en/scripting/dicts.md),
  [sets](../tfwr/en/scripting/sets.md), [tuples](../tfwr/en/scripting/tuples.md).
- Normal farm movement wraps at edges. The Dinosaur Hat disables wrapping; maze
  walls can block movement. Check return values before assuming an action succeeded.
- `till()` toggles soil/grassland; do not call it unconditionally on an already
  prepared tile. `harvest()` can destroy an unharvestable entity.
- Additional drones execute independently with copied state/arguments; mutable
  globals are not shared memory. `spawn_drone()` returns a handle or `None` at
  capacity; `wait_for()` returns the worker's result. See Mega Farm below.
- `simulate()` copies its starting values and returns elapsed simulation time.
  Benchmark programs must terminate; reaching a leaderboard target does not stop them.
- `clear()` clears the farm; `reset()` resets progression. These are separate APIs.
- Costs, resource yields and unlock levels can vary with progression. Runtime-only
  values are not invented in this reference. [Details](../tfwr/en/runtime.md).

## Scope and omissions

The complete API tooltip contracts and all farming/unlock guides are included below.
The compact catalogs contain item, entity/ground, hat and upgrade descriptions.
UI labels, translations, scene JSON, image payloads, setup-only scene code and
duplicate navigation are omitted. Detailed language tutorials, editor setup and
error catalogs stay in the linked full documentation.
"""
TMWR_NOTES = """## Reading contract

- Read [tfwr.md](tfwr.md) first for language, farming and common API contracts.
  This file adds the mining DLC; shared APIs are not duplicated.
- The complete 12 DLC API tooltip contracts and all 18 DLC guides are included.
  English source text avoids translation duplication. UI strings, scene JSON,
  setup-only scene code and image payloads are omitted.
- Documentation visibility is independent of the save's unlocks. Guide examples
  are official source material; they are not all execution-tested solutions.

## Quick rules for mining

- `get_pos_z()` starts at 0 and becomes negative underground. `dig()` takes
  `hardness / drill strength` seconds; speed upgrades and power do not accelerate it.
  `clear()` returns to the surface and restores the farm.
  [Mining](../tmwr/en/unlocks/mining.md), [API](../tmwr/en/reference/code_tooltips.md).
- Digging can destroy neighboring blocks and propagate cave-ins. Stability limits
  height differences. Special-function blocks are exempt from the automatic removal
  of the four adjacent blocks, but remain subject to stability-based cave-ins.
  Cave-in losses do not yield resources.
  [Senses](../tmwr/en/unlocks/underground_senses.md).
- `get_ground_type(direction)`, `get_hardness(direction)` and
  `get_stability(direction)` are documented in the underground-senses guide.
  The hardness/stability tooltip signatures omit this optional direction argument;
  preserve this distinction when choosing a call signature.
- `prospect_iron()` costs 1 coal per call and returns a cardinal direction or `None`.
  `None` can mean no nearby iron, insufficient coal, or already above iron.
  Store the result rather than paying for the same query twice.
  [Iron prospecting](../tmwr/en/unlocks/prospecting.md).
- `prospect_quartz()` costs 1 iron and returns Euclidean 3D distance or `None`.
  Nearby measurements can target different veins.
  [Quartz](../tmwr/en/unlocks/quartz.md).
- The generic `measure()` tooltip in the shared API is not exhaustive for DLC
  grounds. Read the relevant guides for bamboo, mushrooms, basalt, treasure maps,
  soot and dynamite behavior.
- `jump(unlock)` is allowed once per script; only the first drone can jump.
  [Jump](../tmwr/en/unlocks/jump.md),
  [runtime errors](../tmwr/en/reference/execute_errors.md).
- Rice consumes fresh clay: `Rice_Terrace` becomes `Dry_Rice_Terrace` at maturity.
  Dig to the next clay block; do not assume the same tile can be replanted.
  [Rice](../tmwr/en/unlocks/rice.md).
- Only mushroom blocks can be pushed. Matching types stack and auto-harvest;
  blocks cannot be pushed upward.
  [Mushrooms](../tmwr/en/unlocks/mushroom.md).
- The drone that digs into a treasure-map block must follow the treasure path.
  Leaving the path loses the treasure. [Treasure map](../tmwr/en/unlocks/treasure_map.md).
- The Explosive Drill has one wearer. Blocks destroyed directly by its explosion
  yield resources as if mined. [Source](../tmwr/en/unlocks/explosive_drill.md).

## Shared APIs to look up in tfwr.md

`move`, `can_move`, `clear`, `plant`, `can_harvest`, `harvest`, `get_ground_type`,
`get_entity_type`, `measure`, `num_items`, `get_cost`, `num_unlocked`, `unlock`,
`spawn_drone`, `wait_for`, `has_finished`, `num_drones`, `max_drones`, `change_hat`,
`simulate`, `leaderboard_run`, `get_time`, `get_tick_count`.
"""


def rebase(text: str, source: str, output: str) -> str:
    def replace(match):
        image, label, target = match.groups()
        if re.match(r"^[\w+.-]+:", target):
            return match[0]
        path, sep, fragment = target.partition("#")
        path = (
            posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
            if path
            else source
        )
        target = posixpath.relpath(path, posixpath.dirname(output))
        return f"{image}[{label}]({target}{sep}{fragment})"

    return LINK.sub(replace, text)


def records(text: str) -> list[tuple[str, str]]:
    matches = list(RECORD.finditer(text))
    return [
        (
            m[1],
            text[
                m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(text)
            ].strip(),
        )
        for i, m in enumerate(matches)
    ]


def clean_guide(text: str) -> str:
    text = CONFIG.sub("", text)
    start = re.search(r"^# ", text, re.M)
    if not start:
        raise ValueError("Guide has no title")
    lines = text[start.start() :].splitlines()
    result = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            if line == "---" or re.match(
                r"^!?\[[^\n]+\]\([^\n]+\)(?:\s+\[[^\n]+\]\([^\n]+\))*$", line
            ):
                continue
            if line in ("<details>", "</details>"):
                continue
            line = re.sub(r"<summary>(.*?)</summary>", r"**\1**", line)
            line = re.sub(
                r"^(#{1,5}) ", lambda m: "#" * min(6, len(m[1]) + 2) + " ", line
            )
        result.append(line)
    return "\n".join(result).strip()


def build_ai_docs(
    files: dict[str, bytes], build_id: str
) -> dict[str, tuple[str, list[str], dict]]:
    outputs = {}
    for scope, name, notes in (
        ("tfwr", "The Farmer Was Replaced", TFWR_NOTES),
        ("tmwr", "The Miner Was Replaced", TMWR_NOTES),
    ):
        output = f"ai/{scope}.md"
        prefix = f"{scope}/en/"
        sources = []
        text = f"# {name} — AI coding reference\n\n"
        text += (
            f"Steam build: `{build_id}`. Generated by `tools/extract_game_docs.py`.\n\n"
        )
        text += f"[Full English documentation](../{scope}/en/README.md) · [Documentation française](../{scope}/fr/README.md)\n\n"
        text += notes + "\n\n## API contracts\n\n"
        api_source = prefix + "reference/code_tooltips.md"
        sources.append(api_source)
        api_records = records(files[api_source].decode("utf-8"))
        if not api_records:
            raise ValueError(f"No API records in {api_source}")
        for key, body in api_records:
            body = re.split(r"(?im)^example:\s*$", body, maxsplit=1)[0].strip()
            text += f"### `{key.removeprefix('code_tooltip_')}`\n\n"
            text += rebase(body, api_source, output)
            text += f"\n\n[Source](../{api_source}#{key})\n\n"
        text += "## Mechanics and execution guides\n\n"
        available = {
            p for p in files if p.startswith(prefix + "unlocks/") and p.endswith(".md")
        }
        ordered = [prefix + f"unlocks/{stem}.md" for stem in GUIDE_ORDER[scope]]
        if set(ordered) != available:
            raise ValueError(
                f"Update AI guide order: missing={available - set(ordered)}, obsolete={set(ordered) - available}"
            )
        for source in ordered:
            sources.append(source)
            text += f"Source: [{posixpath.basename(source)}](../{source})\n\n"
            text += (
                rebase(clean_guide(files[source].decode("utf-8")), source, output)
                + "\n\n"
            )
        text += "## Compact catalogs\n\n"
        text += (
            "IDs below are localization IDs, not an inferred list of enum spellings. "
        )
        text += "Use exact `Items`, `Entities`, `Grounds`, `Hats` and `Unlocks` members from the API/guides or current game definitions.\n\n"
        catalog_count = 0
        for table, title, prefixes in (
            ("item_tooltips", "Items", ("item_descr_",)),
            ("object_tooltips", "Entities and grounds", ("object_descr_",)),
            ("hat_tooltips", "Hats", ("hat_descr_",)),
            (
                "unlock_tooltips",
                "Unlocks and upgrades",
                ("unlock_descr_", "multi_unlock_descr_"),
            ),
        ):
            source = prefix + f"reference/{table}.md"
            sources.append(source)
            text += f"### {title}\n\n| Source ID | Description |\n| --- | --- |\n"
            for key, body in records(files[source].decode("utf-8")):
                if not key.startswith(prefixes):
                    continue
                body = re.sub(r"```.*?```", "", body, flags=re.S)
                body = rebase(body, source, output)
                body = re.sub(r"\s+", " ", body).strip().replace("|", "\\|")
                text += f"| [`{key}`](../{source}#{key}) | {body} |\n"
                catalog_count += 1
            text += "\n"
        text += "## Diagnostics and source boundaries\n\n"
        text += f"- [Runtime errors](../{prefix}reference/execute_errors.md)\n"
        text += f"- [Action warnings](../{prefix}reference/warnings.md)\n"
        text += "- [Parser errors and supported syntax checks](../tfwr/en/reference/parse_errors.md)\n"
        text += "- [Runtime-dependent values](../tfwr/en/runtime.md)\n"
        text += "- [Source build, attribution and regeneration](../README.md)\n\n"
        text += "The source can contain outdated examples or disagreements between a tooltip "
        text += (
            "and a guide. Do not silently convert an inference into an API contract. "
        )
        text += "Regeneration replaces this file; edit the generator for persistent changes.\n"
        outputs[output] = (
            text,
            sources,
            {
                "api_entries": len(api_records),
                "mechanics_guides": len(ordered),
                "catalog_entries": catalog_count,
            },
        )
    return outputs
