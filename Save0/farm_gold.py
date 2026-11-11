import utils_farm
import utils_move


def requirements(target_stock, parallel=False):
    missing = target_stock - num_items(Items.Gold)
    if missing <= 0:
        return {}
    if num_unlocked(Unlocks.Mazes) == 0:
        return None
    factor = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
    ws = get_world_size()
    if parallel:
        return {Items.Weird_Substance: ws * _steps(target_stock, ws, factor) * factor}
    return {Items.Weird_Substance: ws * factor}


def _steps(target_stock, ws, factor):
    missing = target_stock - num_items(Items.Gold)
    steps = missing // (ws * factor)
    if steps * ws * factor < missing:
        steps += 1
    return max(1, min(300, steps))


def _directions(looking):
    if looking == North:
        return [West, North, East, South]
    if looking == East:
        return [North, East, South, West]
    if looking == South:
        return [East, South, West, North]
    return [South, West, North, East]


def _tile(substance, target_stock, steps):
    for _ in range(steps):
        if num_items(Items.Gold) >= target_stock:
            return True
        if not plant(Entities.Bush) or not use_item(Items.Weird_Substance, substance):
            return False
        if get_entity_type() != Entities.Treasure or not harvest():
            return False
    return True


def _produce(target_stock, parallel):
    if num_items(Items.Gold) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock, parallel), parallel):
        return False
    clear()
    ws = get_world_size()
    factor = 2 ** (num_unlocked(Unlocks.Mazes) - 1)
    if parallel:
        steps = _steps(target_stock, ws, factor)
        handles = []
        success = True
        for _ in range(ws):
            handle = spawn_drone(_tile, factor, target_stock, steps)
            if handle == None:
                if not _tile(factor, target_stock, steps):
                    success = False
                    break
            else:
                handles.append(handle)
            if not move(East):
                success = False
                break
        joined = utils_farm.join_workers(handles)
        return success and joined
    if not plant(Entities.Bush) or not use_item(Items.Weird_Substance, ws * factor):
        return False
    looking = North
    for _ in range(4 * ws * ws + 1):
        if get_entity_type() == Entities.Treasure:
            if not harvest():
                return False
            return utils_move.go_to(0, 0, ws)
        moved = False
        for direction in _directions(looking):
            if move(direction):
                looking = direction
                moved = True
                break
        if not moved:
            return False
    quick_print("Treasure not reached")
    return False


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Gold) < target_stock:
        before = num_items(Items.Gold)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Gold) <= before:
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
