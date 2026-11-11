# Absolute stock target; may clear the world only before starting owned workers.
import utils_farm
import utils_move

MAX_IDLE_SECONDS = 180
MAX_IDLE_PASSES = 262144


def requirements(target_stock):
    return {}


def _column(ws):
    for _ in range(ws):
        if can_harvest():
            if not harvest():
                return False
        if not move(North):
            return False
    return True


def _batch(ws, parallel):
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


def _farm(target_stock, parallel):
    if num_items(Items.Hay) >= target_stock:
        return True
    if parallel and num_unlocked(Unlocks.Megafarm) == 0:
        quick_print("Hay multi requires Megafarm")
        return False
    if not utils_farm.can_start_phase():
        return False
    ws = get_world_size()
    if not utils_move.init(ws, True):
        return False
    first = True
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + MAX_IDLE_SECONDS
    idle_passes = 0
    while num_items(Items.Hay) < target_stock:
        before = num_items(Items.Hay)
        if not _batch(ws, parallel):
            quick_print("Hay batch failed")
            return False
        if first or num_items(Items.Hay) > before:
            idle_passes = 0
            if timed:
                deadline = get_time() + MAX_IDLE_SECONDS
        else:
            idle_passes += 1
            stalled = idle_passes > MAX_IDLE_PASSES
            if timed:
                stalled = get_time() > deadline
            if stalled:
                quick_print("Hay production made no progress")
                return False
        first = False
    return utils_move.go_to(0, 0, ws)


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
