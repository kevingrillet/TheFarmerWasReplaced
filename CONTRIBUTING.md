# Contributing

[AGENTS.md](AGENTS.md) defines conventions; [docs](docs/README.md) indexes the
architecture, contracts, mining guide and benchmarks.

## Setup

Use Git, Bash 4+ (Git Bash on Windows) and Python 3.10+ for host tools. Copy
[.env.example](.env.example) to `.env` and adapt the paths:

| Variable | Default |
| --- | --- |
| `TFWR_GAME_DIR` | `C:/Program Files (x86)/Steam/steamapps/common/The Farmer Was Replaced` |
| `TFWR_SAVE_DIR` | `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0` |
| `TFWR_REPO_SAVE_DIR` | `Save0`, relative to the repository |

TFWR and its DLC share this save. `%USERPROFILE%` is the supported placeholder;
`%APPDATA%` points to Roaming rather than LocalLow. Use forward slashes and quote
paths with spaces. Other expressions are literal, never shell code.

Environment variables override `.env`; explicit command paths override both.
`TFWR_ENV_FILE` can select another config. Configured relative paths start at
the repository root; explicit CLI relative paths start at the calling directory.

## Synchronize scripts

```sh
bash scripts/tfwrDiff.sh
bash scripts/tfwrImport.sh --dryrun
bash scripts/tfwrExport.sh --dryrun
```

Remove `--dryrun` to copy. `-s` and `-d` override source and destination.

- Import copies `.py`, `__builtins__.py` and `save.json`, asking before replacing
  matching files. Unrelated files are preserved.
- Export copies `.py` except `__builtins__.py`; it never exports `save.json`
  and does not delete old filenames.
- Diff compares `.py`, ignoring whitespace/blank lines. Differences return 0;
  configuration or Git failures return a nonzero code.

Compare user edits and back up first. Close the game before installing new or
renamed scripts: a later game save can overwrite them. Remove obsolete names
only after checking their replacements. Imported save/type files remain local
snapshots ignored by Git, and may become stale.

## VS Code

**Terminal → Run Task** offers compare, import, export and documentation generation.
**Ctrl+Shift+B** generates docs. Python uses the selected interpreter; Windows
shell tasks use `C:/Program Files/Git/bin/bash.exe`. The workspace recommends
Python, Ruff, Bash IDE, ShellCheck and markdownlint in the Extensions view.

## Generate official references

```sh
python -m pip install -r requirements-docs.txt
python tools/extract_game_docs.py --extract-images
```

Later text refreshes need only the standard library and existing images:

```sh
python tools/extract_game_docs.py
python tools/extract_game_docs.py --check
```

The exporter reads `TFWR_GAME_DIR`; `--game-dir` overrides it. It reads the game
without changing saves. The full references, AI summaries and manifest are
ignored local artifacts. Edit the generators for persistent changes; don't
force-add their outputs. The index and authored guides remain versioned.

## Work on scripts

- Read [architecture](docs/dev/architecture.md) and [contracts](docs/dev/contracts.md)
  for producer changes; [mining](docs/guides/mining.md) for underground work.
- Use [leaderboards.py](Save0/leaderboards.py) for a seeded simulation or official
  campaign; [benchmark settings](docs/benchmarks/README.md) explain the difference.
  Resource benchmarks stay independent of shared producers and helpers.
- `resource_manager.farm_current(item, target_stock)` funds and produces an
  absolute stock goal; direct `farm_*` calls require their inputs already available.

## Checks

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tools -p 'test_*.py'
ruff check tools Save0
ruff format --check tools
git diff --check
```

Run tests relevant to the change; save-tool tests use temporary directories and
do not synchronize the live save. Host tests and lint don't prove native game
behavior or speed. Use the game parser and controlled runs where appropriate.
Historical `Save0-EA` and generated builtins are outside the active refactor.

## Refresh Steam times

```sh
python tools/export_leaderboards.py
```

This read-only public export refreshes `docs/benchmarks/steam-leaderboards.csv`.
Set `TFWR_STEAM_PROFILE` in the ignored `.env` file; `--profile` overrides it.
The CSV keeps scores and ranks without account names or profile URLs.
`--output` overrides the destination. It needs no login or API key and
never submits a run. It doesn't rewrite the README table or attribute an older
best score to the current code. HTTP/parsing failure preserves the previous CSV.
