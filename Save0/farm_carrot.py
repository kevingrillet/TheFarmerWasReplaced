# Funded Carrot producer: absolute stock target, explicit result, owned workers.
import utils_farm
import utils_move

MAX_IDLE_SECONDS = 180
MAX_IDLE_PASSES = 262144


def requirements(target_stock):
    missing = target_stock - num_items(Items.Carrot)
    if missing <= 0:
        return {}
    level = num_unlocked(Unlocks.Carrots)
    if level == 0:
        return None
    yield_per_plant = 2 ** (level - 1)
    plants = missing // yield_per_plant
    if plants * yield_per_plant < missing:
        plants += 1
    # Initial seeding and the last whole-field pass can both consume seeds.
    # Finance the complete phase before another farm can clear its growing crops.
    plants += 2 * get_world_size() ** 2
    needs = {}
    cost = get_cost(Entities.Carrot)
    for item in cost:
        needs[item] = cost[item] * plants
    return needs


def _column(ws, first):
    for _ in range(ws):
        if can_harvest():
            if not harvest():
                return False
            needs_seed = True
        else:
            needs_seed = get_entity_type() != Entities.Carrot
        if first and get_ground_type() != Grounds.Soil:
            till()
        if needs_seed and not plant(Entities.Carrot):
            return False
        utils_farm.water()
        if not move(North):
            return False
    return True


def _batch(ws, first, parallel):
    handles = []
    success = True
    for _ in range(ws):
        handle = None
        if parallel:
            handle = spawn_drone(_column, ws, first)
        if handle == None:
            if not _column(ws, first):
                success = False
                break
        else:
            handles.append(handle)
        if not move(East):
            success = False
            break
    joined = utils_farm.join_workers(handles)
    return success and joined


def _farm(target_stock, parallel):
    if num_items(Items.Carrot) >= target_stock:
        return True
    if parallel and num_unlocked(Unlocks.Megafarm) == 0:
        quick_print("Carrot multi requires Megafarm")
        return False
    needs = requirements(target_stock)
    if needs == None:
        quick_print("Carrot production locked")
        return False
    for item in needs:
        if num_items(item) < needs[item]:
            quick_print("Carrot phase requires funding", item, needs[item])
            return False
    if not utils_farm.can_start_phase():
        return False
    ws = get_world_size()
    if not utils_move.go_to(0, 0, ws):
        return False
    first = True
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + MAX_IDLE_SECONDS
    idle_passes = 0
    while num_items(Items.Carrot) < target_stock:
        before = num_items(Items.Carrot)
        if not _batch(ws, first, parallel):
            quick_print("Carrot batch failed")
            return False
        if first or num_items(Items.Carrot) > before:
            idle_passes = 0
            if timed:
                deadline = get_time() + MAX_IDLE_SECONDS
        else:
            idle_passes += 1
            stalled = idle_passes > MAX_IDLE_PASSES
            if timed:
                stalled = get_time() > deadline
            if stalled:
                quick_print("Carrot production made no progress")
                return False
        first = False
    return utils_move.go_to(0, 0, ws)


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
