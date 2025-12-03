import UFarm
import UManager
import UMove


def innerfarm(ws):
    # Grow carrot in all grid positions until reaching target quantity
    for _ in range(ws):
        UFarm.qHarvest()
        UFarm.qTill()
        plant(Entities.Carrot)
        move(North)
        UFarm.water()
    move(East)


def farm(qty, checkRequirement=True):
    # Harvest and water carrot fields until reaching qty
    if checkRequirement:
        UManager.checkRequirement(Entities.Carrot, qty)
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Carrot) < qty:
        innerfarm(ws)
