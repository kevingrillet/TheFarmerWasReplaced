# Leaderboards.Cactus: standalone resource benchmark.
TARGET = 33554432


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


def _sort_column(ws):
    top = 0
    bottom = ws - 1
    swapped = True
    while top < bottom and swapped:
        swapped = False
        for _ in range(bottom - top):
            if measure(North) < measure():
                swap(North)
                swapped = True
            move(North)
        move(South)
        bottom -= 1
        for _ in range(bottom - top):
            if measure(South) > measure():
                swap(South)
                swapped = True
            move(South)
        move(North)
        top += 1


def _sort_row(ws):
    index = 0
    while index < ws - 1:
        if measure(East) >= measure():
            move(East)
            index += 1
        else:
            swap(East)
            if index > 0:
                move(West)
                index -= 1
    return True


def _column(ws, first):
    x = get_pos_x()
    for _ in range(ws):
        if first:
            if can_harvest():
                harvest()
            if get_ground_type() != Grounds.Soil:
                till()
        if not plant(Entities.Cactus):
            return False
        _water()
        move(North)
    _sort_column(ws)
    _go_to(x, 0, ws)
    for _ in range(ws):
        while not can_harvest():
            _water()
        move(North)
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
    handles = []
    for _ in range(ws):
        handle = spawn_drone(_sort_row, ws)
        if handle == None:
            _sort_row(ws)
            # Gnome sort ends at x=ws-1; restore x=0 before the next row.
            move(East)
        else:
            handles.append(handle)
        move(North)
    if not _join(handles):
        return False
    _go_to(0, 0, ws)
    return harvest()


def run(target=TARGET):
    if num_items(Items.Cactus) >= target:
        return True
    ws = get_world_size()
    _go_to(0, 0, ws)
    first = True
    while num_items(Items.Cactus) < target:
        if not _batch(ws, first):
            quick_print("Cactus benchmark: batch failed")
            return False
        first = False
    return True


if __name__ == "__main__":
    run()
