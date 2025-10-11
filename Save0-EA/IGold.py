import IPumpkin
import UMove

def innerFarmGold(ws, qty):
    # Farm gold until qty is reached
    # https://en.wikipedia.org/wiki/Maze-solving_algorithm

    def _directions(looking):
        if looking == North:
            return [West, North, East, South]
        elif looking == East:
            return [North, East, South, West]
        elif looking == South:
            return [East, South, West, North]
        else:
            return [South, West, North, East]

    looking = North
    goo = ws * num_unlocked(Unlocks.Mazes)
    while num_items(Items.Gold) < qty:
        clear()
        plant(Entities.Bush)
        while can_harvest() != True:
            use_item(Items.Weird_Substance, goo)
        while get_entity_type() != Entities.Treasure:
            x = get_pos_x()
            y = get_pos_y()
            for dir in _directions(looking):
                move(dir)
                if get_pos_x() != x or get_pos_y() != y:
                    looking = dir
                    break
        harvest()

def farmGold(qty):
    # Produce gold until target quantity is reached

    nb = qty / get_world_size() ** 2
    req = get_world_size() * num_unlocked(Unlocks.Mazes)
    qtyChk = req * nb
    if num_items(Items.Weird_Substance) < qtyChk:
        IPumpkin.farmPumpkin(-1, qtyChk)

    ws = get_world_size()
    UMove.init(ws)
    innerFarmGold(ws, qty)
