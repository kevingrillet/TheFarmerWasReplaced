# Leaderboards.Wood: standalone resource benchmark.
TARGET = 10000000000


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > num_drones():
        use_item(Items.Water)


def _fertilizer_or_water():
    if num_items(Items.Fertilizer) > num_drones():
        if use_item(Items.Fertilizer):
            return
    _water()


def _move_axis(current, target, positive, negative, ws):
    delta = (target - current) % ws
    if delta > ws // 2:
        delta -= ws
    if delta < 0:
        for _ in range(-delta):
            move(negative)
    else:
        for _ in range(delta):
            move(positive)


def _go_to(x, y, ws):
    _move_axis(get_pos_x(), x, East, West, ws)
    _move_axis(get_pos_y(), y, North, South, ws)


def _join(handles):
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def _column(ws, target):
    x = get_pos_x()
    while num_items(Items.Wood) < target:
        for _ in range(ws):
            if can_harvest():
                harvest()
            else:
                _fertilizer_or_water()
                if can_harvest():
                    harvest()
            if (x + get_pos_y()) % 2 == 0:
                plant(Entities.Tree)
                _water()
            else:
                plant(Entities.Bush)
            move(North)
    return True


def run(target=TARGET):
    if num_items(Items.Wood) >= target:
        return True
    ws = get_world_size()
    _go_to(0, 0, ws)
    handles = []
    for _ in range(ws):
        if num_items(Items.Wood) >= target:
            break
        handle = spawn_drone(_column, ws, target)
        if handle == None:
            _column(ws, target)
        else:
            handles.append(handle)
        move(East)
    success = _join(handles)
    return success and num_items(Items.Wood) >= target


if __name__ == "__main__":
    run()
