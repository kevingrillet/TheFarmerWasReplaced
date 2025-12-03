import UFarm
import UManager
import UMove


def _firstPlant(ws):
    # Initial planting of pumpkins in a grid pattern

    coord = []
    for x in range(ws):
        for y in range(ws):
            coord.insert(0, (x, y))
            UFarm.qTill()
            harvest()
            plant(Entities.Pumpkin)
            UFarm.water()
            move(East)
        move(North)
    return coord


def _firstPlantCol(ws):
    coord = []
    x = get_pos_x()
    for y in range(ws):
        if get_entity_type() != Entities.Pumpkin:
            coord.append((x, y))
            UFarm.qTill()
            harvest()
            plant(Entities.Pumpkin)
            UFarm.water()
        move(North)
    return coord


def innerFarmGoo(ws):
    # Grow pumpkins in normal grid order with fertilizer/water logic

    coord = _firstPlant(ws)
    while len(coord) > 0:
        for i in range(len(coord) - 1, -1, -1):
            x, y = coord[i]
            UMove.goTo(x, y, ws)
            if get_entity_type() != Entities.Pumpkin:
                harvest()
                plant(Entities.Pumpkin)
                UFarm.fertilizerOrWater()
            if can_harvest():
                coord.remove((x, y))

    harvest()


def innerfarm(ws):
    # Grow pumpkins in normal grid order with fertilizer/water logic

    coord = _firstPlant(ws)
    while len(coord) > 0:
        for i in range(len(coord) - 1, -1, -1):
            x, y = coord[i]
            UMove.goTo(x, y, ws)
            if get_entity_type() != Entities.Pumpkin:
                harvest()
                plant(Entities.Pumpkin)
                UFarm.water()
            if can_harvest():
                coord.remove((x, y))

    harvest()


def innerfarmV2(ws):
    for x in range(ws):
        coord = _firstPlantCol(ws)
        while len(coord) > 0:
            for i in range(len(coord) - 1, -1, -1):
                x, y = coord[i]
                UMove.goTo(x, y, ws)
                if get_entity_type() == Entities.Dead_Pumpkin:
                    plant(Entities.Pumpkin)
                    UFarm.water()
                if can_harvest():
                    coord.remove((x, y))
        UMove.goTo(x, 0, ws)
        move(East)

    UMove.goTo(0, 0, ws)
    harvest()
    return

    anyMissing = True
    while anyMissing:
        anyMissing = False
        for x in range(ws):
            for y in range(ws):
                if get_entity_type() != Entities.Pumpkin:
                    anyMissing = True
                    harvest()
                    plant(Entities.Pumpkin)
                    UFarm.water()
                move(North)
            move(East)


def farm(qtyPumpkin, qtyGoo, checkRequirement=True):
    # Produce pumpkins and/or goo until target quantities are reached

    ws = get_world_size()
    UMove.init(ws)
    if qtyPumpkin != -1:
        # Check requirements and start pumpkin farming loop
        if checkRequirement:
            UManager.checkRequirement(Entities.Pumpkin, qtyPumpkin)
        while num_items(Items.Pumpkin) < qtyPumpkin:
            innerfarmV2(ws)
    if qtyGoo != -1:
        # Check requirements and start goo farming loop
        if checkRequirement:
            UManager.checkRequirement(Items.Weird_Substance, qtyGoo)
        while num_items(Items.Weird_Substance) < qtyGoo:
            innerfarmV2(ws)
