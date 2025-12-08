# GitHub Copilot Instructions

## Project Context

This project is for **The Farmer Was Replaced**, a programming game where players automate a farm through code.

## Specific Syntax

This project uses a Python-derived syntax specific to "The Farmer Was Replaced" game. When generating or modifying code:

- **Respect game functions and API**: Use native functions like `num_unlocked()`, `harvest()`, `plant()`, `trade()`, etc.
- **Respect game enumerations**: `Items`, `Unlocks`, `Grounds`, `Entities`, `Hats`, `Leaderboards`, etc.
- **Don't import unavailable standard Python libraries**: The game has its own limited environment.
- **Reference `__builtins__.py`**: This file contains most accessible functions in the game along with some documentation on available types and enumerations.
- **Project modules**: Files often start with prefixes:
  - `IM`: Item Multi (item management in multi mode)
  - `IS`: Item Single (item management in single mode)
  - `LM`: Leaderboard Multi (leaderboard strategies in multi mode)
  - `LS`: Leaderboard Single (leaderboard strategies in single mode)
  - `U`: Utilities
  - `M`: Main/Manager
  - `ZZ`: Miscellaneous
- **Code structure**: Prefer simple and clear functions, as code is executed within the game context.

## Best Practices

- Keep code simple and readable
- Comment complex strategies and algorithms
- Use existing utilities (`UDebug`, `UManager`, `UMove`, `UMaths`, `UFarm`)
- Respect existing file structure
