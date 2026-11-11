# Leaderboards.Sunflowers_Single: self-contained descending-petal harvest.
TARGET = 10000


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


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > 1:
        use_item(Items.Water)


def _fertilizer_or_water():
    if num_items(Items.Fertilizer) > 1:
        if use_item(Items.Fertilizer):
            return
    _water()


def _grow_and_harvest(ws, target):
    petals = {}
    for count in range(7, 16):
        petals[count] = []
    for x in range(ws):
        for y in range(ws):
            _go_to(x, y, ws)
            if can_harvest():
                harvest()
            if get_ground_type() != Grounds.Soil:
                till()
            _water()
            plant(Entities.Sunflower)
            petals[measure()].append((x, y))
    while len(petals) > 0:
        best = max(petals)
        bucket = petals[best]
        index = 0
        while index < len(bucket):
            x, y = bucket[index]
            _go_to(x, y, ws)
            if can_harvest():
                harvest()
                bucket.pop(index)
                if num_items(Items.Power) >= target:
                    return True
            else:
                _fertilizer_or_water()
                index += 1
        if len(bucket) == 0:
            petals.pop(best)
    return False


def run(target=TARGET):
    # Power is also spent executing code: keep a margin through program termination.
    finish_target = target + 1
    if num_items(Items.Power) >= finish_target:
        return True
    ws = get_world_size()
    while num_items(Items.Power) < finish_target:
        if _grow_and_harvest(ws, finish_target):
            return True
    return True


if __name__ == "__main__":
    run()
