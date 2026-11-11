# Independent polyculture candidate: Bush background, privately owned crop strips.
TARGET = 2000000000
SINGLE = False


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


def _crop(x, y, root):
    return x == root


def _select(x0, x1, root, y):
    for _ in range(256):
        if get_entity_type() != Entities.Carrot:
            harvest()
            if get_ground_type() != Grounds.Soil:
                till()
            if not plant(Entities.Carrot):
                return False
        request = get_companion()
        if request != None and request[0] == Entities.Bush:
            x, cy = request[1]
            if x0 <= x and x < x1 and not _crop(x, cy, root):
                return True
        # Occupied Carrot/Tree cannot be overplanted like Grass.
        harvest()
    return False


def _strip(target, x0, x1, ws):
    root = x0 + (x1 - x0) // 2
    for x in range(x0, x1):
        if not _go_to(x, 0, ws):
            return False
        for y in range(ws):
            if not _crop(x, y, root) and get_entity_type() != Entities.Bush:
                harvest()
                if not plant(Entities.Bush):
                    return False
            if not move(North):
                return False
    selected = set()
    while num_items(Items.Carrot) < target:
        if not _go_to(root, 0, ws):
            return False
        for y in range(ws):
            if _crop(root, y, root):
                if y not in selected:
                    if not _select(x0, x1, root, y):
                        return False
                    selected.add(y)
                _water()
                if can_harvest():
                    if not harvest():
                        return False
                    selected.remove(y)
                    if num_items(Items.Carrot) >= target:
                        return True
            if not move(North):
                return False
    return True


def run(target=TARGET):
    if num_items(Items.Carrot) >= target:
        return True
    if num_unlocked(Unlocks.Polyculture) == 0:
        return False
    ws = get_world_size()
    if ws < 3:
        return False
    strips = 1
    if not SINGLE:
        strips = max(1, ws // 4)
    handles = []
    success = True
    for index in range(strips):
        x0, x1 = index * ws // strips, (index + 1) * ws // strips
        handle = None
        if not SINGLE and index < strips - 1:
            handle = spawn_drone(_strip, target, x0, x1, ws)
        if handle == None:
            if not _strip(target, x0, x1, ws):
                success = False
                break
        else:
            handles.append(handle)
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success and num_items(Items.Carrot) >= target


if __name__ == "__main__":
    run()
