# Leaderboards.Sunflowers: standalone resource benchmark.
TARGET = 100000


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


def _column(ws, first):
    x = get_pos_x()
    petals = {}
    for count in range(7, 16):
        petals[count] = []
    for y in range(ws):
        if first:
            if can_harvest():
                harvest()
            if get_ground_type() != Grounds.Soil:
                till()
        if not plant(Entities.Sunflower):
            return False
        _water()
        count = measure()
        if count == None:
            return False
        petals[count].append(y)
        move(North)
    while len(petals) > 0:
        best = max(petals)
        bucket = petals[best]
        index = 0
        while index < len(bucket):
            _go_to(x, bucket[index], ws)
            if can_harvest():
                harvest()
                bucket.pop(index)
            else:
                _fertilizer_or_water()
                index += 1
        if len(bucket) == 0:
            petals.pop(best)
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
    return success and joined


def run(target=TARGET):
    # Power is spent by execution too: retain a margin until the program ends.
    finish_target = target + 1
    if num_items(Items.Power) >= finish_target:
        return True
    ws = get_world_size()
    _go_to(0, 0, ws)
    first = True
    while num_items(Items.Power) < finish_target:
        if not _batch(ws, first):
            quick_print("Power benchmark: batch failed")
            return False
        first = False
    return True


if __name__ == "__main__":
    run()
