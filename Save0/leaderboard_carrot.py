# Leaderboards.Carrots: standalone resource benchmark.
TARGET = 2000000000


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > num_drones():
        use_item(Items.Water)


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


def _plant_column(ws):
    for _ in range(ws):
        if can_harvest():
            harvest()
        if get_ground_type() != Grounds.Soil:
            till()
        plant(Entities.Carrot)
        _water()
        move(North)
    return True


def _harvest_column(ws):
    for _ in range(ws):
        if can_harvest():
            harvest()
        plant(Entities.Carrot)
        move(North)
        _water()
    return True


def _batch(ws, first):
    action = _harvest_column
    if first:
        action = _plant_column
    handles = []
    for _ in range(ws):
        handle = spawn_drone(action, ws)
        if handle == None:
            action(ws)
        else:
            handles.append(handle)
        move(East)
    return _join(handles)


def run(target=TARGET):
    if num_items(Items.Carrot) >= target:
        return True
    ws = get_world_size()
    _go_to(0, 0, ws)
    first = True
    while num_items(Items.Carrot) < target:
        if not _batch(ws, first):
            return False
        first = False
    return True


if __name__ == "__main__":
    run()
