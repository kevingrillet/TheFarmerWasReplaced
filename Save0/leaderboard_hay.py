# Leaderboards.Hay: standalone resource benchmark.
TARGET = 2000000000


def _join(handles):
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def _column(ws):
    for _ in range(ws):
        if can_harvest():
            harvest()
        move(North)
    return True


def _batch(ws):
    handles = []
    for _ in range(ws):
        handle = spawn_drone(_column, ws)
        if handle == None:
            _column(ws)
        else:
            handles.append(handle)
        move(East)
    return _join(handles)


def run(target=TARGET):
    if num_items(Items.Hay) >= target:
        return True
    ws = get_world_size()
    clear()
    while num_items(Items.Hay) < target:
        if not _batch(ws):
            return False
    return True


if __name__ == "__main__":
    run()
