import UFarm
import UMove


def _infiniteStaticSubFarm():
    # Useless
    ws = get_world_size()
    while True:
        UFarm.qHarvest()
        UFarm.water()


def _subFarm():
    ws = get_world_size()
    for _ in range(ws):
        UFarm.qHarvest()
        move(North)


def _infiniteSubFarm():
    while True:
        _subFarm()


def innerFarm(ws):
    for _ in range(ws):
        if spawn_drone(_subFarm):
            move(East)
        else:
            _subFarm()
            move(East)


def farm(qty):
    global qtyWanted
    qtyWanted = qty
    ws = get_world_size()
    UMove.init(ws, True)
    while num_items(Items.Hay) < qty:
        innerFarm(ws)
