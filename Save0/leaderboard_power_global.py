# Independent multi candidate: all columns joined before global petal groups.
TARGET = 100000


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


def _plant_column(x, ws):
    flowers = []
    if not _go_to(x, 0, ws):
        return None
    for y in range(ws):
        if get_entity_type() != Entities.Sunflower:
            harvest()
            if get_ground_type() != Grounds.Soil:
                till()
            if not plant(Entities.Sunflower):
                return None
            _water()
        petals = measure()
        if petals == None or petals < 7 or petals > 15:
            return None
        flowers.append((petals, x, y))
        if not move(North):
            return None
    return flowers


def _plant_all(ws):
    handles, flowers = [], []
    success = True
    for x in range(ws):
        handle = None
        if x < ws - 1:
            handle = spawn_drone(_plant_column, x, ws)
        if handle == None:
            result = _plant_column(x, ws)
            if result == None:
                success = False
                break
            flowers += result
        else:
            handles.append(handle)
    for handle in handles:
        result = wait_for(handle)
        if result == None:
            success = False
        else:
            flowers += result
    if not success:
        return None
    buckets = {}
    for count in range(7, 16):
        buckets[count] = []
    for petals, x, y in flowers:
        buckets[petals].append((x, y))
    return buckets


def _harvest_group(cells, target, ws):
    pending = []
    for pos in cells:
        pending.append(pos)
    changed = get_time()
    while len(pending) > 0:
        if num_items(Items.Power) >= target:
            return True
        for index in range(len(pending) - 1, -1, -1):
            x, y = pending[index]
            if not _go_to(x, y, ws):
                return False
            if can_harvest():
                if not harvest():
                    return False
                pending.pop(index)
                changed = get_time()
            else:
                _water()
        if get_time() - changed > 60:
            return False
    return True


def _harvest_all(cells, target, ws):
    count = min(max_drones(), len(cells))
    if count == 0:
        return True
    groups = []
    for _ in range(count):
        groups.append([])
    for index in range(len(cells)):
        groups[index % count].append(cells[index])
    handles = []
    success = True
    for index in range(count):
        handle = None
        if index < count - 1:
            handle = spawn_drone(_harvest_group, groups[index], target, ws)
        if handle == None:
            if not _harvest_group(groups[index], target, ws):
                success = False
                break
        else:
            handles.append(handle)
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def run(target=TARGET):
    finish = target + 1
    ws = get_world_size()
    keep = 0
    if ws * ws >= 10:
        keep = 9
    while num_items(Items.Power) < finish:
        buckets = _plant_all(ws)
        if buckets == None:
            return False
        remaining = ws * ws
        for petals in range(15, 6, -1):
            cells = []
            for pos in buckets[petals]:
                if remaining > keep:
                    cells.append(pos)
                    remaining -= 1
            # No replanting during harvest; the next group starts after this join.
            if not _harvest_all(cells, finish, ws):
                return False
            if num_items(Items.Power) >= finish:
                return True
    return True


if __name__ == "__main__":
    run()
