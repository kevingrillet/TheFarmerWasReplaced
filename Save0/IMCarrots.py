import UFarm
import UManager
import UMove


def _subTillAndPlant():
    ws = get_world_size()
    for _ in range(ws):
        UFarm.qHarvest()
        UFarm.qTill()
        plant(Entities.Carrot)
        UFarm.water()
        move(North)


def _subFarm():
    ws = get_world_size()
    for _ in range(ws):
        UFarm.qHarvest()
        plant(Entities.Carrot)
        move(North)
        UFarm.water()


def _infiniteSubFarm():
    while True:
        _subFarm()


def innerFarm(ws, plantAction):
    for _ in range(ws):
        if spawn_drone(plantAction):
            move(East)
        else:
            plantAction()
            move(East)


def farm(qty, checkRequirement=True):
    global qtyWanted
    qtyWanted = qty
    # Harvest and water carrot fields until reaching qty
    if checkRequirement:
        UManager.checkRequirement(Entities.Carrot, qty)
    ws = get_world_size()
    UMove.init(ws)
    plantAction = _subTillAndPlant
    while num_items(Items.Carrot) < qty:
        innerFarm(ws, plantAction)
        plantAction = _subFarm
