# Leaderboards.Wood_Single: self-contained checkerboard trees/bushes strategy.
TARGET = 500000000


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > 1:
        use_item(Items.Water)


def run(target=TARGET):
    if num_items(Items.Wood) >= target:
        return True
    ws = get_world_size()
    # leaderboards simulations start at (0, 0) on a fresh farm.
    while num_items(Items.Wood) < target:
        x = get_pos_x()
        for y in range(ws):
            if can_harvest():
                harvest()
                if (x + y) % 2 == 0:
                    plant(Entities.Tree)
                else:
                    plant(Entities.Bush)
            move(North)
            _water()
        move(East)
    return True


if __name__ == "__main__":
    run()
