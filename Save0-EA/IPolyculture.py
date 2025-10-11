import IHayWood
import UFarm
import UMove

def innerFarm(item, qty, ws):
    # Farm until qty of item is reached

    comp = None
    x = None
    y = None
    while num_items(item) < qty:
        UFarm.water()
        UFarm.qTill()
        if comp == None:
            plant(Entities.Grass)
        else:
            plant(comp)
        comp, (x, y) = get_companion()
        UMove.goTo(x, y, ws)
        if not UFarm.qHarvest():
            UFarm.fertilizerOrWater()
            UFarm.qHarvest()

def farm(entity, qty):
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
        IHayWood.farmHayWood(1000)

    innerFarm(item, qty, ws)
