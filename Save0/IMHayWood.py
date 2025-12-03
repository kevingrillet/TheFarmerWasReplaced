import UFarm
import UMove


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
            plant(Entities.Grass)
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
            plant(Entities.Grass)
        move(North)


def _infiniteSubFarmEven():
    while True:
        _subFarmEven()


def _infiniteSubFarmOdd():
    while True:
        _subFarmOdd()


def innerFarm(ws):
    for _ in range(ws):
        if get_pos_x() % 2 == 0:
            action = _subFarmEven
        else:
            action = _subFarmOdd
        if spawn_drone(action):
            move(East)
        else:
            action()
            move(East)


def farm(qty):
    global qtyWanted
    qtyWanted = qty
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Hay) < qty or num_items(Items.Wood) < qty:
        innerFarm(ws)
