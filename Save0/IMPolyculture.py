def _infiniteSubPoly():
    import UFarm
    import UMove

    ws = get_world_size()
    comp, x, y = None, None, None
    ts = get_time()
    while True:
        UFarm.water()
        UFarm.qTill()
        if comp == None:
            plant(Entities.Grass)
        else:
            plant(comp)
        if get_entity_type() == None:
            move(East)
            continue
        tmpComp = get_companion()
        if tmpComp == None:
            move(North)
            continue
        comp, (x, y) = tmpComp
        UMove.goTo(x, y, ws)
        if not UFarm.qHarvest():
            UFarm.fertilizerOrWater()
            UFarm.qHarvest()
        if ts - ct > 60:
            break


def infiniteInnerFarm(ws):
    for _ in range(ws):
        if spawn_drone(_infiniteSubPoly):
            move(East)
        else:
            _infiniteSubPoly()
            move(East)


def _subPlantCompanion():
    import UFarm
    import UMove

    ws = get_world_size()
    comp = None
    x = None
    y = None

    comp, (x, y) = get_companion()
    UMove.goTo(x, y, ws)
    if not UFarm.qHarvest():
        UFarm.fertilizerOrWater()
        UFarm.qHarvest()
    if comp == Entities.Carrot:
        UFarm.qTill()
    plant(comp)


def innerFarm(item, qty, ws):
    # Farm until qty of item is reached

    while num_items(item) < qty:
        for x in range(ws):
            for y in range(ws):
                if num_items(item) > qty:
                    return
                while not spawn_drone(_subPlantCompanion):
                    pass
                move(North)
            move(East)


def farm(entity, qty):
    global qtyWanted
    qtyWanted = qty
    import IMHayWood
    import UMove

    # Farm a specific entity until qty is reached

    ws = get_world_size()
    UMove.init(ws)

    item = None

    if entity == Entities.Grass:
        item = Items.Hay
    elif entity == Entities.bush or entity == Entities.Tree:
        item = Items.Wood
    else:
        item = Items.Carrot

    if num_items(Items.Hay) < 1000 or num_items(Items.Wood) < 1000:
        IMHayWood.farm(1000)

    innerFarm(item, qty, ws)
