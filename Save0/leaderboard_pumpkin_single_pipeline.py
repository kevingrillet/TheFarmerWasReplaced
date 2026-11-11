# Independent single candidate: plant the whole field before waiting for repairs.
TARGET = 10000000


def _go_to(x, y, ws):
    dx, dy = (x - get_pos_x()) % ws, (y - get_pos_y()) % ws
    if dx > ws // 2:
        for _ in range(ws - dx):
            if not move(West):
                return False
    else:
        for _ in range(dx):
            if not move(East):
                return False
    if dy > ws // 2:
        for _ in range(ws - dy):
            if not move(South):
                return False
    else:
        for _ in range(dy):
            if not move(North):
                return False
    return True


def _water():
    if get_water() < 0.75 and num_items(Items.Water) > 0:
        use_item(Items.Water)


def _grow_field(ws):
    pending = []
    for x in range(ws):
        y, dy, direction = 0, 1, North
        if x % 2 == 1:
            y, dy, direction = ws - 1, -1, South
        if not _go_to(x, y, ws):
            return False
        for row in range(ws):
            if get_entity_type() != Entities.Pumpkin:
                if get_entity_type() != Entities.Dead_Pumpkin:
                    harvest()
                if get_ground_type() != Grounds.Soil:
                    till()
                if not plant(Entities.Pumpkin):
                    return False
                _water()
            pending.append((x, y))
            if row < ws - 1 and not move(direction):
                return False
            y += dy
    changed = get_time()
    while len(pending) > 0:
        for index in range(len(pending) - 1, -1, -1):
            x, y = pending[index]
            if not _go_to(x, y, ws):
                return False
            if get_entity_type() == Entities.Dead_Pumpkin:
                if not plant(Entities.Pumpkin):
                    return False
                _water()
            if can_harvest():
                pending.pop(index)
                changed = get_time()
        if get_time() - changed > 60:
            return False
    if not _go_to(0, 0, ws):
        return False
    # Every cell was planted and observed mature; a surviving mature Pumpkin
    # cannot later die. This proves the full square rather than a sampled seam.
    return get_entity_type() == Entities.Pumpkin and can_harvest() and harvest()


def run(target=TARGET):
    ws = get_world_size()
    while num_items(Items.Pumpkin) < target:
        if not _grow_field(ws):
            return False
    return True


if __name__ == "__main__":
    run()
