<div align="center">
  <a href="https://github.com/kyechan99/capsule-render">
    <img align="center" alt="Header" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=250&section=header&text=The%20Farmer&fontAlign=30&fontAlignY=30&fontSize=85&desc=Was%20Replaced&descAlign=65&descAlignY=55&descSize=80" />
  </a>
</div>

Save location: `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0`

## Early Access Leaderboards

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

## Scripts

### tfwrImport.sh

This script copies all .py files from your game save folder (by default: `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0`) to a local folder (default: `./Save0`).
If the destination folder is not empty, it will ask for confirmation before deleting its contents.
You can use the `--dryrun` option to preview which files would be copied.

Usage:

```sh
./tfwrImport.sh [-s source_path] [-d dest_path] [--dryrun]
```

### tfwrExport.sh

This script copies all `.py` files (except `__builtins__.py`) from a local folder (default: `./Save0`) back to your game save folder (by default: `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0`).
It does not delete or overwrite any non-`.py` files in the destination.
You can use the `--dryrun` option to preview which files would be copied.

Usage:

```sh
./tfwrExport.sh [-s source_path] [-d dest_path] [--dryrun]
```

### tfwrDiff.sh

This script compares `.py` files between your game save folder (by default: `%USERPROFILE%/AppData/LocalLow/TheFarmerWasReplaced/TheFarmerWasReplaced/Saves/Save0`) and a local folder (default: `./Save0`).
It shows the differences for each file present in both folders, as well as a list of files only present in one or the other.

Usage:

```sh
./tfwrDiff.sh [-s source_path] [-d dest_path]
```

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
