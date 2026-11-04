# Contributing

For repository conventions and game-language constraints, read [AGENTS.md](AGENTS.md).
The [documentation index](docs/README.md) explains how to generate the local game references.

## Requirements

- Git and Bash 4+; use Git Bash on Windows.
- Python 3.10+ for documentation and host-side tools.
- Optional development tools: `python -m pip install -r requirements-dev.txt`.
- First documentation extraction and image refresh: `python -m pip install -r requirements-docs.txt`.

## Local configuration

For a new clone, copy [.env.example](.env.example) to `.env` at the repository root
and adapt the paths. `.env` is ignored by Git. The example uses the default Steam
installation and the current Windows user profile:

| Variable | Purpose | Default |
| --- | --- | --- |
| `TFWR_GAME_DIR` | Installed game; used by documentation extraction | `C:/Program Files (x86)/Steam/steamapps/common/The Farmer Was Replaced` |
| `TFWR_SAVE_DIR` | Live save scripts | `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0` |
| `TFWR_REPO_SAVE_DIR` | Repository scripts | `Save0`, relative to the repository root |

Use forward slashes. `%USERPROFILE%` is replaced with the Windows user profile
by both the Python tools and Bash scripts, falling back to the current home
directory when `USERPROFILE` is unavailable. `%APPDATA%` is not used: the save is
in `AppData/LocalLow`, rather than `AppData/Roaming`.
Quoted paths may contain spaces; full-line comments are supported. Other variable
syntax, command substitutions and inline comments remain literal and are not
executed. Unset/empty entries use built-in defaults.
Environment variables override `.env`; explicit `-s`/`-d` or `--game-dir` arguments
override the corresponding configured paths. An optional `TFWR_ENV_FILE` environment
variable selects a different configuration file.

Configured relative paths are resolved from the repository root, so script defaults
work from any working directory. Explicit `-s`/`-d` relative paths are resolved from
the calling directory. Use Bash 4+; on Windows, Git Bash is supported.

The base game and mining DLC use the same configured save in this workflow.
The `mining` unlock was confirmed in `Save0/save.json` after enabling it in game;
no separate TMWR save path is needed.

## Import, export and compare

```sh
bash scripts/tfwrImport.sh [-s source_path] [-d dest_path] [--dryrun]
bash scripts/tfwrExport.sh [-s source_path] [-d dest_path] [--dryrun]
bash scripts/tfwrDiff.sh [-s source_path] [-d dest_path]
```

- **Import** copies `.py` files, including `__builtins__.py`, and `save.json` from
  the live save to the repository. It asks before replacing matching files. Other files
  and scripts absent from the source are preserved; the folder is not emptied.
- **Export** copies `.py` files from the repository to the live save, excluding
  `__builtins__.py`. Other live-save files are preserved.
- **Compare** shows changes, additions and deletions among `.py` files only,
  ignoring whitespace and blank lines. Differences are informational and return
  exit code 0; configuration, directory or Git errors return a nonzero code.
- `--dryrun` previews import/export without copying or creating anything.

`__builtins__.py` provides the game's editor API definitions; `save.json` is a
local snapshot useful for inspecting resources and unlocks. Both are ignored by
Git, which does not prevent the import script from copying them. Neither file
is exported back to the game. Refresh them by importing again after game updates
or progression changes; the snapshot can become stale.

## VS Code tasks and extensions

Use **Terminal → Run Task** and select one of the four
[essential tasks](.vscode/tasks.json):

- `TFWR: Comparer les scripts`
- `TFWR: Importer du jeu vers le dépôt`
- `TFWR: Exporter du dépôt vers le jeu`
- `TFWR: Régénérer la documentation`

**Ctrl+Shift+B** runs documentation generation. Previews (`--dryrun`), checks,
image extraction and dependency installation remain available from the terminal
using the commands in this guide.

The Python task uses the interpreter chosen with **Python: Select Interpreter**.
After the first extraction, ordinary documentation generation uses only the
standard library and existing illustrations. Windows shell tasks use Git Bash at
`C:/Program Files/Git/bin/bash.exe`.

The [workspace recommendations](.vscode/extensions.json) cover
[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python),
[Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff),
[Bash IDE](https://marketplace.visualstudio.com/items?itemName=mads-hartmann.bash-ide-vscode),
[ShellCheck](https://marketplace.visualstudio.com/items?itemName=timonwong.shellcheck)
and [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint).
Install them from the Extensions view's workspace recommendations.

## Update the documentation

The official texts, illustrations, AI references and extraction manifest are
local generated artifacts. `docs/tfwr/`, `docs/tmwr/` and `docs/ai/` are ignored
by Git except for their `.gitkeep` placeholders; `docs/manifest.json` is ignored
as well. The AI references also contain extracted game text. Keep these outputs
local rather than adding them with `git add -f`.

On a fresh clone, the folders contain only placeholders. Install the image-extraction
dependency and generate the references from your installed game:

```sh
python -m pip install -r requirements-docs.txt
python tools/extract_game_docs.py --extract-images
```

The extractor reads `TFWR_GAME_DIR` from `.env`. For subsequent text updates:

```sh
python tools/extract_game_docs.py
python tools/extract_game_docs.py --check
```

To refresh the illustrations again:

```sh
python tools/extract_game_docs.py --extract-images
```

Edit `tools/extract_game_docs.py` or `tools/build_ai_docs.py` for persistent
documentation changes; generated files are replaced during extraction.
The GitHub link check skips references to local artifacts; the extractor's
`--check` validates the generated files and their links locally.

## Utility checks

```sh
python -m unittest discover -s tools -p 'test_*.py'
python tools/extract_game_docs.py --check
ruff check tools
ruff format --check tools
```

Utility tests use temporary directories; they do not import or export the live save.
