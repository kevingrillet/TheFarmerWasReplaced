# Leaderboards.Maze: standalone resource benchmark.
TARGET = 9863168


def _join(handles):
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def _worker(substance, target):
    # Preserve the existing strategy: repeated one-tile mazes at each drone.
    for _ in range(300):
        if num_items(Items.Gold) >= target:
            return True
        if not plant(Entities.Bush):
            return False
        if not use_item(Items.Weird_Substance, substance):
            return False
        if get_entity_type() != Entities.Treasure or not harvest():
            return False
    return True


def _batch(ws, substance, target):
    handles = []
    success = True
    for _ in range(ws):
        if num_items(Items.Gold) >= target:
            break
        handle = spawn_drone(_worker, substance, target)
        if handle == None:
            if not _worker(substance, target):
                success = False
                break
        else:
            handles.append(handle)
        move(East)
    joined = _join(handles)
    return success and joined


def run(target=TARGET):
    if num_items(Items.Gold) >= target:
        return True
    ws = get_world_size()
    substance = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
    clear()
    while num_items(Items.Gold) < target:
        if not _batch(ws, substance, target):
            quick_print("Maze benchmark: one-tile creation failed")
            return False
    return True


if __name__ == "__main__":
    run()
