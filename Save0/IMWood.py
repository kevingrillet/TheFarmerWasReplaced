def _subFarmEven():
    global qtyWanted
    ws = get_world_size()
    while num_items(Items.Wood) < qtyWanted:
        for _ in range(ws):
            if can_harvest():
                harvest()
            else:
                water()
                harvest()
            if get_pos_y() % 2 == 0:
                plant(Entities.Tree)
                water()
            else:
                plant(Entities.Bush)
            move(North)


def _subFarmOdd():
    global qtyWanted
    ws = get_world_size()
    while num_items(Items.Wood) < qtyWanted:
        for _ in range(ws):
            if can_harvest():
                harvest()
            else:
                water()
                harvest()
            if get_pos_y() % 2 == 1:
                plant(Entities.Tree)
                water()
            else:
                plant(Entities.Bush)
            move(North)


def run(qty, ws=None):
    global qtyWanted
    qtyWanted = qty
    if ws == None:
        ws = get_world_size()
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
