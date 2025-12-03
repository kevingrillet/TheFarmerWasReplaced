import UFarm
import UMove


def innerFarmHay(ws):
    # Grow hay in all grid positions until reaching target quantity
    for _ in range(ws):
        UFarm.qHarvest()
        move(North)
    move(East)


def farmHay(qty):
    # Harvest and water hay fields until reaching qty
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Hay) < qty:
        innerFarmHay(ws)


def innerFarmHayWood(ws):
    # Grow both hay and wood in all grid positions until reaching target quantity
    for _ in range(ws):
        UFarm.qHarvest()
        if get_pos_x() % 2 == 0 and get_pos_y() % 2 == 0:
            plant(Entities.Tree)
        elif get_pos_x() % 2 == 1 and get_pos_y() % 2 == 1:
            plant(Entities.Tree)
        else:
            plant(Entities.Grass)
        move(North)
        UFarm.water()
    move(East)


def farmHayWood(qty):
    # Harvest and plant both hay and wood until reaching qty
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Hay) < qty or num_items(Items.Wood) < qty:
        innerFarmHayWood(ws)


def innerfarm(ws):
    # Quickly harvest and replant bushes
    for _ in range(ws):
        if UFarm.qHarvest():
            plant(Entities.Bush)
        move(North)
        UFarm.water()
    move(East)


def innerfarmWithT(ws):
    # Harvest and plant trees or bushes for wood
    for _ in range(ws):
        if UFarm.qHarvest():
            if get_pos_x() % 2 == 0 and get_pos_y() % 2 == 0:
                plant(Entities.Tree)
            elif get_pos_x() % 2 == 1 and get_pos_y() % 2 == 1:
                plant(Entities.Tree)
            else:
                plant(Entities.Bush)
        move(North)
        UFarm.water()
    move(East)


def farm(qty, hasTrees):
    # Harvest and plant trees or bushes for wood until reaching qty
    ws = get_world_size()
    UMove.init(ws)
    if hasTrees:
        while num_items(Items.Wood) < qty:
            innerfarmWithT(ws)
    else:
        while num_items(Items.Wood) < qty:
            innerfarm(ws)
