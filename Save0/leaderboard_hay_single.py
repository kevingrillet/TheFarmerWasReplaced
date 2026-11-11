# Leaderboards.Hay_Single: 3x3 Bush field, six-step setup and selected Grass.
TARGET = 100000000
SIZE = 3
ROOT_COLUMN = 2


def prepare_field():
    # Start at (0, 0); fill x=0 upwards, then x=1 downwards.
    for _ in range(2):
        if not plant(Entities.Bush):
            return False
        move(North)
    if not plant(Entities.Bush):
        return False
    move(East)
    for _ in range(2):
        if not plant(Entities.Bush):
            return False
        move(South)
    if not plant(Entities.Bush):
        return False
    move(East)
    # End at (2, 0), ready to harvest the untouched Grass column.
    return True


def water():
    if get_water() < 0.75 and num_items(Items.Water) > 0:
        use_item(Items.Water)


def select_companion():
    request = get_companion()
    while (
        request == None or request[0] != Entities.Bush or request[1][0] == ROOT_COLUMN
    ):
        if not plant(Entities.Grass):
            quick_print("Hay bush benchmark: grass replacement failed")
            return False
        request = get_companion()
    return True


def run(target=TARGET):
    if num_items(Items.Hay) >= target:
        return True
    if get_world_size() != SIZE:
        set_world_size(SIZE)
    if get_world_size() != SIZE:
        return False
    if not prepare_field():
        quick_print("Hay bush benchmark: field preparation failed")
        return False
    selected = []
    for _ in range(SIZE):
        selected.append(False)
    y = 0
    while num_items(Items.Hay) < target:
        water()
        if not selected[y]:
            if not select_companion():
                return False
            selected[y] = True
        if can_harvest():
            harvest()
            selected[y] = False
            if num_items(Items.Hay) >= target:
                return True
        move(North)
        y = (y + 1) % SIZE
    return True


if __name__ == "__main__":
    run()
