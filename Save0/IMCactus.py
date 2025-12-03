import UFarm
import UManager
import UMove

# https://rosettacode.org/wiki/Category:Sorting_Algorithms


def _sort_bubble(dMin, dMax):
    # https://rosettacode.org/wiki/Sorting_algorithms/Bubble_sort

    ws = get_world_size()

    swapped = True
    while swapped:
        swapped = False
        if dMax == East:
            UMove.goTo(0, get_pos_y())
        else:
            UMove.goTo(get_pos_x(), 0)

        for _ in range(ws - 1):
            if measure(dMax) < measure():
                swap(dMax)
                swapped = True
            move(dMax)


def _sort_cocktail(dMin, dMax):
    # https://rosettacode.org/wiki/Sorting_algorithms/Cocktail_sort

    top = 0
    bottom = get_world_size() - 1

    swapped = True
    while top < bottom and swapped:
        swapped = False
        for _ in range(bottom - top):
            if measure(dMax) < measure():
                swapped = True
                swap(dMax)
            move(dMax)
        move(dMin)
        bottom -= 1

        for _ in range(bottom - top):
            if measure(dMin) > measure():
                swapped = True
                swap(dMin)
            move(dMin)
        move(dMax)
        top += 1


def _sort_gnome(dMin, dMax):
    # https://rosettacode.org/wiki/Sorting_algorithms/Gnome_sort

    ws = get_world_size()
    i = 0
    while i < ws - 1:
        if measure(dMax) >= measure():
            move(dMax)
            i += 1
        else:
            swap(dMin)
            if i > 0:
                move(dMin)
                i -= 1
            else:
                move(dMax)
                i += 1


def _sort_selection(dMin, dMax):
    # https://rosettacode.org/wiki/Sorting_algorithms/Selection_sort

    ws = get_world_size()

    for i in range(ws - 1):
        if dMax == East:
            UMove.goTo(i, get_pos_y())
        else:
            UMove.goTo(get_pos_x(), i)

        min_index = i
        min_value = measure()

        for j in range(i + 1, ws):
            move(dMax)
            current_value = measure()
            if current_value < min_value:
                min_value = current_value
                min_index = j

        if min_index != i:
            if dMax == East:
                UMove.goTo(min_index, get_pos_y())
            else:
                UMove.goTo(get_pos_x(), min_index)
            swap(dMin)


def _subSortRow():
    _sort_gnome(West, East)


def _subSortCol():
    _sort_cocktail(South, North)


def _subPlant():
    ws = get_world_size()
    for _ in range(ws):
        plant(Entities.Cactus)
        UFarm.water()
        move(North)
    _subSortCol()


def _subTillAndPlant():
    ws = get_world_size()
    for _ in range(ws):
        UFarm.qHarvest()
        UFarm.qTill()
        plant(Entities.Cactus)
        UFarm.water()
        move(North)
    _subSortCol()


def _resetPoswaitAndDrones(ws):
    UMove.goTo(0, 0, ws)
    while num_drones() > 1:
        pass


def innerFarm(ws, plantAction):
    # Plant & sort col
    for _ in range(ws):
        if spawn_drone(plantAction):
            move(East)
        else:
            plantAction()
            move(East)
    # Sort row
    _resetPoswaitAndDrones(ws)
    for _ in range(ws):
        if spawn_drone(_subSortRow):
            move(North)
        else:
            _subSortRow()
            move(North)
    _resetPoswaitAndDrones(ws)
    harvest()


def farm(qty, checkRequirement=True):
    # Harvest and water carrot fields until reaching qty
    if checkRequirement:
        UManager.checkRequirement(Entities.Cactus, qty)
    ws = get_world_size()
    UMove.init(ws)
    plantAction = _subTillAndPlant
    while num_items(Items.Cactus) < qty:
        innerFarm(ws, plantAction)
        plantAction = _subPlant
