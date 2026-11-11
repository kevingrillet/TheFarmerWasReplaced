# Complete funded fields; explicit Pumpkin and Goo goals.
import utils_farm
import utils_move


def requirements(target_stock):
    if num_items(Items.Pumpkin) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Pumpkins) == 0:
        return None
    # One full field plus a replacement reserve. A refused seed aborts the phase.
    return utils_farm.seed_requirements(
        Entities.Pumpkin, 2 * get_world_size() ** 2 + 16
    )


def goo_requirements(target_stock):
    if num_items(Items.Weird_Substance) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Fertilizer) == 0:
        return None
    ws = get_world_size()
    factor = min(ws, 6) * 2 ** (num_unlocked(Unlocks.Pumpkins) - 1)
    if factor < 2:
        return None
    needs = requirements(num_items(Items.Pumpkin) + 1)
    if needs == None:
        return None
    if num_items(Items.Weird_Substance) < 1 or (ws < 3 and factor < 4):
        needs[Items.Fertilizer] = 1
    return needs


def _column(ws):
    x = get_pos_x()
    for _ in range(ws):
        if get_ground_type() != Grounds.Soil:
            till()
        if not plant(Entities.Pumpkin):
            return False
        utils_farm.water()
        if not move(North):
            return False
    pending = []
    replacements = []
    for y in range(ws):
        pending.append(y)
        replacements.append(0)
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + 180
    for _ in range(262144):
        if len(pending) == 0:
            return utils_move.go_to(x, 0, ws)
        if timed and get_time() > deadline:
            break
        for index in range(len(pending) - 1, -1, -1):
            y = pending[index]
            if not utils_move.go_to(x, y, ws):
                return False
            if get_entity_type() == Entities.Dead_Pumpkin:
                replacements[y] += 1
                if replacements[y] > 64 or not plant(Entities.Pumpkin):
                    return False
                utils_farm.water()
            if can_harvest():
                pending.pop(index)
    quick_print("Pumpkin field did not mature")
    return False


def _grow(ws, parallel):
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
    return success and joined


def _infect(ws):
    charges = num_items(Items.Weird_Substance)
    factor = min(ws, 6) * 2 ** (num_unlocked(Unlocks.Pumpkins) - 1)
    if charges < 1 or (ws < 3 and factor < 4):
        if not utils_move.go_to(0, 0, ws):
            return False
        # Fertilizer infects even a mature cell; never lose it on a dead seedling.
        return use_item(Items.Fertilizer)
    if ws < 3:
        return use_item(Items.Weird_Substance)
    # Disjoint interior crosses: every charge infects five healthy cells.
    for x in range(1, ws - 1, 3):
        for y in range(1, ws - 1, 3):
            if charges < 1:
                return True
            if not utils_move.go_to(x, y, ws):
                return False
            if not use_item(Items.Weird_Substance):
                return False
            charges -= 1
    return True


def _produce(target_stock, parallel, goo):
    item = Items.Pumpkin
    if goo:
        item = Items.Weird_Substance
    if num_items(item) >= target_stock:
        return True
    needs = requirements(target_stock)
    if goo:
        needs = goo_requirements(target_stock)
    if not utils_farm.preflight(needs, parallel):
        return False
    ws = get_world_size()
    clear()
    if not _grow(ws, parallel):
        return False
    if goo and not _infect(ws):
        return False
    if not utils_move.go_to(0, 0, ws) or not utils_farm.wait_ripe():
        return False
    return harvest()


def produce_single(target_stock):
    return _produce(target_stock, False, False)


def produce_multi(target_stock):
    return _produce(target_stock, True, False)


def produce_goo_single(target_stock):
    return _produce(target_stock, False, True)


def produce_goo_multi(target_stock):
    return _produce(target_stock, True, True)


def _farm(target_stock, parallel, goo):
    item = Items.Pumpkin
    if goo:
        item = Items.Weird_Substance
    stalled = 0
    while num_items(item) < target_stock:
        before = num_items(item)
        if not _produce(target_stock, parallel, goo):
            return False
        if num_items(item) <= before:
            stalled += 1
            if stalled >= 8:
                return False
        else:
            stalled = 0
    return True


def farm_single(target_stock):
    return _farm(target_stock, False, False)


def farm_multi(target_stock):
    return _farm(target_stock, True, False)


def farm_goo_single(target_stock):
    return _farm(target_stock, False, True)


def farm_goo_multi(target_stock):
    return _farm(target_stock, True, True)
