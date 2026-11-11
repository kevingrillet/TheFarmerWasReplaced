import utils_farm
import utils_move


def requirements(target_stock):
    if num_items(Items.Cactus) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Cactus) == 0:
        return None
    return utils_farm.seed_requirements(Entities.Cactus, get_world_size() ** 2)


def _sort_column(ws):
    # Bounded adjacent swaps, ascending South -> North, without comparing the wrap.
    x = get_pos_x()
    for end in range(ws - 1, 0, -1):
        if not utils_move.go_to(x, 0, ws):
            return False
        changed = False
        for _ in range(end):
            current, neighbor = measure(), measure(North)
            if current == None or neighbor == None:
                return False
            if neighbor < current:
                if not swap(North):
                    return False
                changed = True
            if not move(North):
                return False
        if not changed:
            break
    return utils_move.go_to(x, 0, ws)


def _sort_row(ws):
    y = get_pos_y()
    index = 0
    for _ in range(2 * ws * ws + 1):
        if index >= ws - 1:
            return utils_move.go_to(0, y, ws)
        current, neighbor = measure(), measure(East)
        if current == None or neighbor == None:
            return False
        if neighbor >= current:
            if not move(East):
                return False
            index += 1
        else:
            if not swap(East):
                return False
            if index > 0:
                if not move(West):
                    return False
                index -= 1
    return False


def _column(ws):
    x = get_pos_x()
    for _ in range(ws):
        if get_ground_type() != Grounds.Soil:
            till()
        if not plant(Entities.Cactus):
            return False
        utils_farm.water()
        if not move(North):
            return False
    if not _sort_column(ws):
        return False
    for _ in range(ws):
        if not utils_farm.wait_ripe() or not move(North):
            return False
    return utils_move.go_to(x, 0, ws)


def _produce(target_stock, parallel):
    if num_items(Items.Cactus) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    ws = get_world_size()
    clear()
    handles = []
    success = True
    for _ in range(ws):
        handle = None
        if parallel:
            handle = spawn_drone(_column, ws)
        if handle == None:
            if not _column(ws):
                success = False
                break
        else:
            handles.append(handle)
        if not move(East):
            success = False
            break
    joined = utils_farm.join_workers(handles)
    if not success or not joined or not utils_move.go_to(0, 0, ws):
        return False
    handles = []
    for _ in range(ws):
        handle = None
        if parallel:
            handle = spawn_drone(_sort_row, ws)
        if handle == None:
            if not _sort_row(ws):
                success = False
                break
        else:
            handles.append(handle)
        if not move(North):
            success = False
            break
    joined = utils_farm.join_workers(handles)
    if not success or not joined or not utils_move.go_to(0, 0, ws):
        return False
    return harvest()


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Cactus) < target_stock:
        before = num_items(Items.Cactus)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Cactus) <= before:
            stalled += 1
            if stalled >= 8:
                return False
        else:
            stalled = 0
    return True


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
