# Leaderboards.Cactus_Single: self-contained cached-grid gnome sort.
TARGET = 131072


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


def _plant_and_sort(ws):
    cactus = []
    for pos in range(ws * ws):
        x, y = pos % ws, pos // ws
        _go_to(x, y, ws)
        if can_harvest():
            harvest()
        if get_ground_type() != Grounds.Soil:
            till()
        plant(Entities.Cactus)
        cactus.append(measure())

    _go_to(0, 0, ws)
    pos = 0
    while pos < ws * ws:
        x, y = pos % ws, pos // ws
        if y > 0:
            below = pos - ws
            if cactus[below] > cactus[pos]:
                _go_to(x, y, ws)
                swap(South)
                cactus[below], cactus[pos] = cactus[pos], cactus[below]
                pos = below
                continue
        if x == 0 or cactus[pos] >= cactus[pos - 1]:
            pos += 1
        else:
            _go_to(x, y, ws)
            swap(West)
            cactus[pos], cactus[pos - 1] = cactus[pos - 1], cactus[pos]
            pos -= 1
    # Sorting normally covers growth; wait if this particular field sorted quickly.
    while not can_harvest():
        pass
    harvest()


def run(target=TARGET):
    if num_items(Items.Cactus) >= target:
        return True
    ws = get_world_size()
    while num_items(Items.Cactus) < target:
        _plant_and_sort(ws)
    return True


if __name__ == "__main__":
    run()
