import UFarm
import UManager
import UMove


def _subTillAndPlant():
    coord = []
    x = get_pos_x()
    for y in range(get_world_size()):
        if get_entity_type() != Entities.Pumpkin:
            coord.append((x, y))
            UFarm.qTill()
            harvest()
            plant(Entities.Pumpkin)
            UFarm.water()
        move(North)
    return coord


def _subPlant():
    coord = []
    x = get_pos_x()
    for y in range(get_world_size()):
        if get_entity_type() != Entities.Pumpkin:
            coord.append((x, y))
            plant(Entities.Pumpkin)
            UFarm.water()
        move(North)
    return coord


def _subInnerFarm(innerPlantAction):
    ws = get_world_size()
    coord = innerPlantAction()
    while len(coord) > 0:
        for i in range(len(coord) - 1, -1, -1):
            x, y = coord[i]
            UMove.goTo(x, y, ws)
            if get_entity_type() == Entities.Dead_Pumpkin:
                plant(Entities.Pumpkin)
                UFarm.water()
            if can_harvest():
                coord.remove((x, y))


def _subFarmWithTill():
    _subInnerFarm(_subTillAndPlant)


def _subFarm():
    _subInnerFarm(_subPlant)


def innerFarm(ws, plantAction):
    for _ in range(ws):
        if spawn_drone(plantAction):
            move(East)
        else:
            plantAction()
            move(East)
    while num_drones() > 1:
        pass
    harvest()


def farm(qtyPumpkin, qtyGoo, checkRequirement=True):
    ws = get_world_size()
    UMove.init(ws)
    if qtyPumpkin != -1:
        # Check requirements and start pumpkin farming loop
        if checkRequirement:
            UManager.checkRequirement(Entities.Pumpkin, qtyPumpkin)
        plantAction = _subFarmWithTill
        while num_items(Items.Pumpkin) < qtyPumpkin:
            innerFarm(ws, plantAction)
            plantAction = _subFarm
    if qtyGoo != -1:
        # Check requirements and start goo farming loop
        if checkRequirement:
            UManager.checkRequirement(Items.Weird_Substance, qtyGoo)
        plantAction = _subFarmWithTill
        while num_items(Items.Weird_Substance) < qtyGoo:
            innerFarm(ws, plantAction)
            plantAction = _subFarm
