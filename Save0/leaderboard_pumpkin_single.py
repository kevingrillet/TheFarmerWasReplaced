# Leaderboards.Pumpkins_Single: self-contained column maturation and full-field merge.
TARGET = 10000000


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


def _grow_field(ws):
    for x in range(ws):
        pending = []
        for y in range(ws):
            if get_entity_type() != Entities.Pumpkin:
                pending.append((x, y))
                if get_ground_type() != Grounds.Soil:
                    till()
                harvest()
                plant(Entities.Pumpkin)
                _water()
            move(North)
        while len(pending) > 0:
            for index in range(len(pending) - 1, -1, -1):
                px, py = pending[index]
                _go_to(px, py, ws)
                if get_entity_type() == Entities.Dead_Pumpkin:
                    plant(Entities.Pumpkin)
                    _water()
                if can_harvest():
                    pending.pop(index)
        _go_to(x, 0, ws)
        move(East)
    _go_to(0, 0, ws)
    while not can_harvest():
        pass
    harvest()


def run(target=TARGET):
    if num_items(Items.Pumpkin) >= target:
        return True
    ws = get_world_size()
    while num_items(Items.Pumpkin) < target:
        _grow_field(ws)
    return True


if __name__ == "__main__":
    run()
