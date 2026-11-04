<div align="center">
  <a href="https://github.com/kyechan99/capsule-render">
    <img align="center" alt="Header" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=250&section=header&text=The%20Farmer&fontAlign=30&fontAlignY=30&fontSize=85&desc=Was%20Replaced&descAlign=65&descAlignY=55&descSize=80" />
  </a>
</div>

Save location: `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0`

## Game documentation

Official documentation is extracted locally from the installed game, in French
and English. Generated texts and illustrations are ignored by Git; the links
below become available after [local generation](CONTRIBUTING.md).

- [The Farmer Was Replaced](docs/tfwr/README.md)
- [The Miner Was Replaced — DLC](docs/tmwr/README.md)
- [Extraction, source version and coverage](docs/README.md)

For coding assistants, start with the consolidated [TFWR reference](docs/ai/tfwr.md)
and add the [TMWR reference](docs/ai/tmwr.md) for DLC work. Shared repository
instructions are maintained in [AGENTS.md](AGENTS.md); `CLAUDE.md` and the Copilot
instructions point to it.

## Save0

1.0 & Leaderboard

| Category       | Time        | Time solo   |
|----------------|------------:|------------:|
| Hay            |           - |           - |
| Wood           |           - |           - |
| Carrots        |           - |           - |
| Pumpkins       |           - |           - |
| Cactus         |           - |           - |
| Sunflowers     |           - |           - |
| Dinosaur       |           - |             |
| Maze           |           - |           - |
| Polyculture    |           - |             |
| Fastest Reset  |           - |             |

<details>
<summary>ToDo</summary>

- [x] All achievements
- [ ] Leaderboard for everything

</details>

## Save0-EA

Early Access save & Leaderboard

| Category       | Time        | Rank |
|----------------|------------:|-----:|
| Hay            |   00:44.549 |   53 |
| Wood           |   00:52.292 |   99 |
| Carrots        |   05:54.602 |   99 |
| Pumpkins       |   02:47.644 |   77 |
| Cactus         |   00:20.228 |  123 |
| Sunflowers     |   48:00.399 |   93 |
| Dinosaur       |   00:42.263 |  118 |
| Maze           |   06:40.014 |  320 |
| Polyculture    |   07:04.609 |   58 |
| Fastest Reset  | 8:33:56.525 |  110 |

<details>
<summary>ToDo</summary>

- [x] Leaderboard for everything
- [ ] Top 100 for everything
  - [x] Hay
    - [x] Use custom Polyculture
  - [x] Wood
    - [ ] Use custom Polyculture
  - [x] Carrots
  - [x] Pumpkins
  - [ ] Cactus
    - [ ] Alternative sort
  - [x] Sunflowers
    - [ ] Sort distance?
  - [ ] Dinosaur
    - [x] Less check
    - [ ] Better logic: Agressive before Hamilton cycle? Simple GoTo? Pathfinding A*?
  - [ ] Maze
    - [ ] Use same maze
    - [ ] DFS
  - [x] Polyculture
  - [ ] Fastest Reset
    - [ ] Better steps

</details>

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local configuration, save scripts,
essential VS Code tasks, recommended extensions and development checks.

## Licence

```txt
/*
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * kevingrillet wrote this file. As long as you retain this notice you can do
 * whatever you want with this stuff. If we meet some day, and you think this
 * stuff is worth it, you can buy me a beer in return.
 * ----------------------------------------------------------------------------
 */
```

<div align="center">
   <a href="https://github.com/kyechan99/capsule-render">
      <img align="center" alt="Footer" src="https://capsule-render.vercel.app/api?section=footer&type=waving&color=gradient&height=100" />
   </a>
</div>
