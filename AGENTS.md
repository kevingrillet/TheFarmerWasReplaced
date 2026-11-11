# Repository instructions

## Start here

- [CONTRIBUTING.md](CONTRIBUTING.md): setup, synchronization and checks.
- [docs/README.md](docs/README.md): documentation index.
- Read [architecture](docs/dev/architecture.md) and
  [contracts](docs/dev/contracts.md) before changing shared production code;
  [mining](docs/guides/mining.md) before changing underground algorithms.
- Game API: search [TFWR](docs/ai/tfwr.md), then [TMWR](docs/ai/tmwr.md) for DLC
  work. Resolve ambiguous contracts against the detailed local official help
  and installed build. Old `__builtins__.py` and save snapshots can be stale.

## Scope and files

`Save0/` is active; `Save0-EA/` is historical. `tools/` is ordinary host Python;
`scripts/` contains Bash synchronization utilities configured by `.env`.
Generated `docs/tfwr/`, `docs/tmwr/`, `docs/ai/` and `docs/manifest.json` are local
and ignored, except `.gitkeep` placeholders. Never force-add extracted game text.
Change the generator for persistent edits; do not hand-edit generated pages.

The base game and DLC use the same configured save. Import may copy
`__builtins__.py` and `save.json` into the repo; never export either back.
Compare and back up before replacing live scripts, preserving user edits.
Synchronize only when requested as part of the task. A docs task must not run
game scenarios, reset progression, submit a leaderboard or alter achievements.

## Game code

- This is a restricted Python-like language: no assumed stdlib, classes,
  exceptions, comprehensions, keyword arguments or arbitrary CPython features.
- Use qualified `import module` calls, snake_case and `_` for local helpers.
  Sort imports alphabetically within each block; preserve local import scope
  where circular dependencies require it. Avoid new registries/classes.
- Production lives in `farm_<resource>` / `mine_<resource>`. Public names can
  repeat across modules. Only `resource_manager` funds dependencies, before
  preparation; no producer/helper imports it or another producer.
- `farm_*` succeeds only at its absolute stock goal. `produce_*` completes one
  finite funded lot. Declare requirements, propagate failure, treat `None`
  as failure and preserve the mode-specific signatures in the contracts.
- Each parent joins all owned handles, even after failure. Refused spawns fall
  back to the parent. Never use a fixed drone population as a barrier or assume
  shared mutable worker globals. No clear/funding transition with active workers.
- Preserve `clear()` versus progression-resetting `reset()`. Imports must not
  start gameplay; scenario entries use guarded `run()` calls.
- Mining collectors operate in the caller's world without funding, clear or
  jump. Preserve the height/ownership/stop contracts in the mining guide.
- Keep existing helpers pending a separate cleanup request; unused automatic
  callers do not make a manual diagnostic obsolete.

## Performance and benchmarks

Speed is a primary goal. Direct calls and module access are free according to
Timing; observations, indexing, indirect references, copies and spawns have
costs. Digging has native durations in seconds. Preserve useful parallelism,
cache only valid state and measure the full objective, not code length.

Resource benchmarks `leaderboard_<resource>[_single]` are autonomous: no imports
from producers, managers or utilities. Reset benchmarks may use progression
code. Keep native `Leaderboards.*` categories and the launcher's simulation /
official modes; its dictionaries map categories to filenames, not callbacks.
See [benchmarks](docs/benchmarks/README.md) and
[optimization notes](docs/analyses/optimisations.md) before changing a reference.
Record times against the exact measured code; don't replace scores with guesses.

## Validation and documentation

Run relevant host tests and Ruff for changed tools; use the native parser or
game checks when appropriate. Fixtures and parsing do not establish native
behavior, achievement awards or performance. Report these limits plainly.

```sh
python -m unittest discover -s tools -p 'test_*.py'
ruff check tools Save0
ruff format --check tools
git diff --check
```

For generated docs, run `python tools/extract_game_docs.py --check` against the
configured installation. Keep `docs/README.md` as the only Markdown file at the
root of `docs/`; guides and dev contracts belong in their folders. Analyses are
short syntheses of open decisions and sources, not a history of each change.
All game achievements are complete as confirmed on 2026-11-11; don't recreate
an achievement backlog. Keep the existing scenario scripts available.

`CLAUDE.md` and `.github/copilot-instructions.md` point here; don't duplicate rules.
