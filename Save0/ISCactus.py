import UFarm
import UManager
import UMaths
import UMove


def innerfarmV0(ws):
    for x in range(ws):
        UMove.goTo(x, 0, ws)
        cols = []
        for y in range(ws):
            UFarm.qHarvest()
            UFarm.qTill()
            plant(Entities.Cactus)
            cols.append(measure())
            move(North)
        for i in range(ws):
            if len(cols) == 0:
                break
            minY = find(cols, min(cols))
            cols.pop(minY)
            UMove.goTo(x, minY + 1, ws)
            for _ in range(minY + 1 - i):
                swap(South)

    for y in range(ws):
        UMove.goTo(0, y, ws)
        rows = []
        for x in range(ws):
            rows.append(measure())
            move(East)
        for i in range(ws):
            if len(rows) == 0:
                break
            minX = find(rows, min(rows))
            rows.pop(minX)
            UMove.goTo(minX + 1, y, ws)
            for _ in range(minX + 1 - i):
                swap(West)


def innerfarmV1(ws):
    # Grow and sort cactus until reaching target quantity

    def _plant(grid_size, ws):
        # Plant cactus in all grid positions and record growth values
        grid = []
        for i in range(grid_size):
            x, y = UMaths.reshape(i, ws)
            UMove.goTo(x, y, ws)
            UFarm.qHarvest()
            UFarm.qTill()
            plant(Entities.Cactus)
            grid.append(measure())
        return grid

    def _gnomeSort(cactus, ws):
        # https://en.wikipedia.org/wiki/Gnome_sort
        # Sort cactus grid by growth using swap operations
        UMove.goTo(0, 0, ws)

        pos = 0
        while pos < ws**2:
            x, y = UMaths.reshape(pos, ws)

            # Compare with cactus above
            if y > 0 and y != ws:
                pos_2 = UMaths.flatten(x, y - 1, ws)
                if cactus[pos_2] > cactus[pos]:
                    UMove.goTo(x, y, ws)
                    swap(South)
                    cactus[pos_2], cactus[pos] = cactus[pos], cactus[pos_2]
                    pos = pos_2
                    continue

            # Compare with left cactus
            if x == 0 or cactus[pos] >= cactus[pos - 1]:
                pos += 1
            else:
                UMove.goTo(x, y, ws)
                cactus[pos], cactus[pos - 1] = cactus[pos - 1], cactus[pos]
                swap(West)
                pos -= 1
        UFarm.qHarvest()

    _gnomeSort(_plant(ws**2, ws), ws)


def farm(qty, checkRequirement=True):
    # Check requirements and start cactus farming loop
    if checkRequirement:
        UManager.checkRequirement(Entities.Cactus, qty)
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Cactus) < qty:
        innerfarmV1(ws)
