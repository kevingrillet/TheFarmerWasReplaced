# Leaderboards.Maze: candidate adapted from cheese_maze.py.
# Station one drone on every tile before creating a full-field maze.
TARGET = 9863168


def _join(handles):
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def _create(substance):
    return plant(Entities.Bush) and use_item(Items.Weird_Substance, substance)


def _watch(substance, target):
    best_stock = num_items(Items.Gold)
    last_gain = get_time()
    while num_items(Items.Gold) < target:
        if get_entity_type() == Entities.Treasure and can_harvest():
            if num_items(Items.Weird_Substance) < substance:
                return False
            if not use_item(Items.Weird_Substance, substance):
                # A mature treasure refuses relocation after 300 reuses.
                # No private/global counter can be shared between the drones.
                if not harvest():
                    return False
                if num_items(Items.Gold) >= target:
                    return True
                if not _create(substance):
                    return False
        stock = num_items(Items.Gold)
        if stock > best_stock:
            best_stock = stock
            last_gain = get_time()
        elif get_time() - last_gain > 180:
            return False
    return True


def run(target=TARGET):
    if num_items(Items.Gold) >= target:
        return True
    if num_drones() != 1 or num_unlocked(Unlocks.Timing) == 0:
        return False
    level = num_unlocked(Unlocks.Mazes)
    capacity = max_drones()
    if level < 1 or capacity < 9 or get_world_size() < 3:
        quick_print("Maze reuse: at least 9 drones and a 3x3 field required")
        return False
    ws = 3
    while ws < 5 and ws < get_world_size() and (ws + 1) ** 2 <= capacity:
        ws += 1
    set_world_size(ws)
    if get_world_size() != ws:
        return False
    clear()
    substance = ws * 2 ** (level - 1)
    handles = []
    success = True
    # Snake through the empty field. The parent occupies the final tile.
    for x in range(ws):
        for row in range(ws):
            if x == ws - 1 and row == ws - 1:
                break
            handle = spawn_drone(_watch, substance, target)
            if handle == None:
                success = False
                break
            handles.append(handle)
            if row < ws - 1:
                if x % 2 == 0:
                    success = move(North)
                else:
                    success = move(South)
            else:
                success = move(East)
            if not success:
                break
        if not success:
            break
    if success:
        success = _create(substance)
    if success:
        success = _watch(substance, target)
    # Failed creation/spawn also joins the bounded waiting workers.
    joined = _join(handles)
    return success and joined and num_items(Items.Gold) >= target


if __name__ == "__main__":
    run()
