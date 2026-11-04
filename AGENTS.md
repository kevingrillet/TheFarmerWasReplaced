# Repository instructions

These instructions apply throughout this repository. Assistant-specific entry
files refer here so project conventions have one maintained source.

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, environment variables,
save utilities, the four essential VS Code tasks and development commands.

## Project and documentation

This repository contains automation scripts for The Farmer Was Replaced and
preparation for its mining DLC, The Miner Was Replaced.

- Read [docs/ai/tfwr.md](docs/ai/tfwr.md) for the game's language, shared API,
  farming mechanics and programming pitfalls. Search the relevant sections for
  small changes instead of loading the entire reference.
- For DLC work, also read [docs/ai/tmwr.md](docs/ai/tmwr.md). It extends the shared
  reference and links to it for common functions.
- The complete official extracts are in [docs/tfwr/](docs/tfwr/README.md) and
  [docs/tmwr/](docs/tmwr/README.md), in French and English, after local generation.
  These extracts and `docs/ai/` are ignored by Git, with versioned `.gitkeep`
  placeholders; the extraction manifest is local too. Never force-add the outputs.
  Generate missing references following CONTRIBUTING.md. Follow source links
  for detailed syntax, error messages or an ambiguous contract.
- [docs/README.md](docs/README.md) records the installed source build, coverage,
  limitations, attribution and regeneration procedure.
- Documentation records an installed build, not the current save's unlocks or
  quantities. Check `num_unlocked()`, `num_items()` and `get_cost()` as needed.
- Current generated `__builtins__.py` files can help confirm game enum members
  and editor signatures, but are approximations. They are ignored by Git and can
  be stale. Resolve disagreements against current in-game help and validation;
  do not promote an old save definition or historical script into a current API.
- Import brings both `__builtins__.py` and `save.json` into the development save
  folder. Both are local and ignored by Git; export sends neither back to the game.
  Use `save.json` as a progression snapshot, checking its freshness before relying
  on resource quantities or unlocks.

## Repository layout

- `Save0/`: scripts for the main save. Keep existing module names and utilities.
- `Save0-EA/`: historical Early Access scripts. Change them only when the task
  concerns that version; their APIs and old leaderboard results may differ.
- `tools/`: ordinary host-side Python tooling, not game scripts.
- `docs/tfwr/`, `docs/tmwr/`, `docs/ai/` and `docs/manifest.json`: generated docs.
- `scripts/`: Bash tools to import, export or compare save scripts, with shared
  configuration in `scripts/common.sh`.
- `.env`: ignored local paths for the installation, live save and repository save.
  `.env.example` contains the reference setup. Environment variables override the
  file; explicit command-line paths override both. Relative configured paths are
  rooted at the repository; explicit script CLI paths are relative to the caller.
  `%USERPROFILE%` is the supported profile placeholder; other expressions remain
  literal. Base-game and mining work currently use the same `Save0` save path.
- `.vscode/tasks.json` and `.vscode/extensions.json`: editor actions and extension
  recommendations. Python tasks use the interpreter selected in VS Code; Windows
  shell tasks use Git Bash from `C:/Program Files/Git/bin/bash.exe`.

Script prefixes: `IM`/`IS` = multi/single-drone item management; `LM`/`LS` =
multi/single-drone leaderboard strategies; `U` = utilities; `M` = entry/manager;
`ZZ` = miscellaneous. Reuse `UDebug`, `UManager`, `UMove`, `UMaths` and `UFarm`
where their current behavior fits the task.

## Game code

- The game uses a Python-like language. Use its documented builtins, containers
  and enum symbols; do not assume CPython's standard library or arbitrary Python
  syntax is available. Host-side tools may use normal Python libraries.
- Keep game code simple and readable. Account for action failures, tick costs,
  unlock levels and drone limits when they affect correctness or performance.
- Do not infer exact enum member names from localization IDs in catalog tables.
- Preserve the distinction between `clear()` and progression-resetting `reset()`.
  Imported modules should not perform entry-point actions unintentionally.
- Keep current and historical strategies separate. Do not rewrite gameplay
  scripts, archived results or save contents as a side effect of a docs task.
- Import/export synchronizes real files and can replace scripts. Run it only when
  synchronization is part of the user's request; use `--dryrun` when inspecting.

## Documentation and checks

- Regenerate docs with `python tools/extract_game_docs.py`; do not hand-edit
  generated pages. `tools/build_ai_docs.py` defines the consolidated references.
- Verify against the local installation with
  `python tools/extract_game_docs.py --check`. This requires the installed game.
- The extractor reads `TFWR_GAME_DIR` from the shared `.env` configuration;
  `--game-dir` overrides it. The Bash utilities also read `TFWR_SAVE_DIR` and
  `TFWR_REPO_SAVE_DIR`. Expand only the supported profile placeholder; never
  evaluate configuration as shell code.
- Refresh illustrations with `--extract-images` after installing
  `requirements-docs.txt`; image extraction is optional for ordinary text updates.
- For changes to host tooling, run `ruff check tools` and
  `ruff format --check tools`. The pre-commit hooks use Ruff for lint and format.
- For changes to the save utilities/configuration, run
  `python -m unittest discover -s tools -p 'test_*.py'`. Tests use temporary fixture
  directories and require Bash; they do not synchronize the live save.
- Check `git diff --check` and relevant local links. For gameplay changes, use
  appropriate in-game simulation/benchmark checks when available. CPython parsing
  or lint success does not establish that a game script works or is fast.
- Report what was checked and any validation that could not be performed.

## Assistant entry files

Keep `CLAUDE.md` and `.github/copilot-instructions.md` as small pointers to this
file. Put shared instructions here instead of duplicating them across assistants.
