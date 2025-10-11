import UFarm
import UManager
import UMove

def innerFarmCarrot(ws):
    # Grow carrot in all grid positions until reaching target quantity
    for _ in range(ws):
        UFarm.qHarvest()
        UFarm.qTill()
        plant(Entities.Carrot)
        move(North)
        UFarm.water()
    move(East)

def farmCarrot(qty):
    # Harvest and water carrot fields until reaching qty
    UManager.checkRequirement(Entities.Carrot, qty)
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Carrot) < qty:
        innerFarmCarrot(ws)
