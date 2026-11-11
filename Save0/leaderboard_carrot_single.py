# Leaderboards.Carrots_Single: self-contained carrot column traversal.
TARGET = 100000000


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > 1:
        use_item(Items.Water)


def run(target=TARGET):
    if num_items(Items.Carrot) >= target:
        return True
    ws = get_world_size()
    while num_items(Items.Carrot) < target:
        for _ in range(ws):
            if can_harvest():
                harvest()
            if get_ground_type() != Grounds.Soil:
                till()
            # An unripe carrot can still occupy the tile: a refused replant is normal.
            plant(Entities.Carrot)
            move(North)
            _water()
        move(East)
    return True


if __name__ == "__main__":
    run()
