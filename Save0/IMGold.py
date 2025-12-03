import ISPumpkin
import UFarm
import UMove


def _subFarm():
    UFarm.qTillGrass()
    ws = get_world_size()
    reuse = 0

    while reuse < 300:
        plant(Entities.Bush)
        use_item(Items.Weird_Substance, ws)
        harvest()
        reuse += 1


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
    # Produce gold until target quantity is reached

    nb = qty / get_world_size() ** 2
    req = get_world_size() * num_unlocked(Unlocks.Mazes)
    qtyChk = req * nb
    if num_items(Items.Weird_Substance) < qtyChk:
        ISPumpkin.farm(-1, qtyChk)

    ws = get_world_size()
    UMove.init(ws, True)
    while num_items(Items.Gold) < qty:
        innerFarm(ws)
