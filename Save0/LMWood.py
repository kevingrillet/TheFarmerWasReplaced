import UFarm


def _subFarmEven():
    ws = get_world_size()
    for _ in range(ws):
        if not UFarm.qHarvest():
            UFarm.fertilizerOrWater()
            UFarm.qHarvest()
        if get_pos_y() % 2 == 0:
            plant(Entities.Tree)
            UFarm.water()
        else:
            plant(Entities.Bush)
        move(North)


def _subFarmOdd():
    ws = get_world_size()
    for _ in range(ws):
        if not UFarm.qHarvest():
            UFarm.fertilizerOrWater()
            UFarm.qHarvest()
        if get_pos_y() % 2 == 1:
            plant(Entities.Tree)
            UFarm.water()
        else:
            plant(Entities.Bush)
        move(North)


def _infiniteSubFarmEven():
    while num_items(Items.Wood) < 10000000000:
        _subFarmEven()


def _infiniteSubFarmOdd():
    while num_items(Items.Wood) < 10000000000:
        _subFarmOdd()


def innerFarm(ws):
    for _ in range(ws):
        if get_pos_x() % 2 == 0:
            action = _infiniteSubFarmEven
        else:
            action = _infiniteSubFarmOdd
        if spawn_drone(action):
            move(East)
        else:
            action()
            move(East)


def runWood():
    ws = get_world_size()
    while num_items(Items.Wood) < 10000000000:
        innerFarm(ws)


runWood()
