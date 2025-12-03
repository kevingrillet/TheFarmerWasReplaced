import UFarm
import UManager
import UMove


def _subFarm(petals, ws):
    x = get_pos_x()
    while len(petals) > 0:
        best = max(petals)
        for y in petals[best]:
            UMove.goTo(x, y, ws)
            if UFarm.qHarvest():
                petals[best].remove(y)
            else:
                UFarm.fertilizerOrWater()

        if len(petals[best]) == 0:
            petals.pop(best)


def _subTillAndPlant():
    while num_drones() < 32:
        pass
    petals = {}
    for i in range(7, 15 + 1):
        petals[i] = []
    ws = get_world_size()
    for y in range(ws):
        UFarm.qHarvest()
        UFarm.qTill()
        plant(Entities.Sunflower)
        UFarm.water()
        petals[measure()].append(y)
        move(North)
    _subFarm(petals, ws)


def _subPlant():
    while num_drones() < 32:
        pass
    petals = {}
    for i in range(7, 15 + 1):
        petals[i] = []
    ws = get_world_size()
    for y in range(ws):
        plant(Entities.Sunflower)
        UFarm.water()
        petals[measure()].append(y)
        move(North)
    _subFarm(petals, ws)


def innerFarm(ws, plantAction):
    for _ in range(ws):
        if spawn_drone(plantAction):
            move(East)
        else:
            plantAction()
    UMove.goTo(0, 0, ws)
    while num_drones() > 1:
        pass


def farm(qty, checkRequirement=True):
    # Harvest and water carrot fields until reaching qty
    if checkRequirement:
        UManager.checkRequirement(Entities.Sunflower, qty)
    ws = get_world_size()
    UMove.init(ws)
    plantAction = _subTillAndPlant
    while num_items(Items.Power) < qty:
        innerFarm(ws, plantAction)
        plantAction = _subPlant
