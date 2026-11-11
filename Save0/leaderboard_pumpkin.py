# Leaderboards.Pumpkins: standalone resource benchmark.
TARGET = 200000000


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


def _column(ws, first):
    x = get_pos_x()
    pending = []
    for y in range(ws):
        if get_entity_type() != Entities.Pumpkin:
            if first and get_ground_type() != Grounds.Soil:
                till()
            if can_harvest():
                harvest()
            if not plant(Entities.Pumpkin):
                return False
            _water()
        pending.append(y)
        move(North)
    while len(pending) > 0:
        for index in range(len(pending) - 1, -1, -1):
            y = pending[index]
            _go_to(x, y, ws)
            if get_entity_type() == Entities.Dead_Pumpkin:
                if not plant(Entities.Pumpkin):
                    return False
                _water()
            if can_harvest():
                pending.pop(index)
    _go_to(x, 0, ws)
    return True


def _batch(ws, first):
    handles = []
    success = True
    for _ in range(ws):
        handle = spawn_drone(_column, ws, first)
        if handle == None:
            if not _column(ws, first):
                success = False
                break
        else:
            handles.append(handle)
        move(East)
    joined = _join(handles)
    if not success or not joined:
        return False
    _go_to(0, 0, ws)
    while not can_harvest():
        _water()
    return harvest()


def run(target=TARGET):
    if num_items(Items.Pumpkin) >= target:
        return True
    ws = get_world_size()
    _go_to(0, 0, ws)
    first = True
    while num_items(Items.Pumpkin) < target:
        if not _batch(ws, first):
            quick_print("Pumpkin benchmark: batch failed")
            return False
        first = False
    return True


if __name__ == "__main__":
    run()
