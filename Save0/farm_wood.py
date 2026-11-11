# Absolute stock target; private workers receive copied targets, not globals.
import utils_farm
import utils_move

MAX_IDLE_SECONDS = 180
MAX_IDLE_PASSES = 262144


def requirements(target_stock):
    if num_items(Items.Wood) < target_stock and num_unlocked(Unlocks.Plant) == 0:
        return None
    return {}


def _column(ws, has_trees):
    x = get_pos_x()
    for _ in range(ws):
        if has_trees and (x + get_pos_y()) % 2 == 0:
            entity = Entities.Tree
        else:
            entity = Entities.Bush
        current = get_entity_type()
        if can_harvest():
            if not harvest():
                return False
            current = None
        if current != entity:
            if current != None:
                harvest()
            if not plant(entity):
                return False
        utils_farm.water()
        if not move(North):
            return False
    return True


def _worker(ws, target_stock, has_trees):
    first = True
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + MAX_IDLE_SECONDS
    idle_passes = 0
    while num_items(Items.Wood) < target_stock:
        before = num_items(Items.Wood)
        if not _column(ws, has_trees):
            return False
        if first or num_items(Items.Wood) > before:
            idle_passes = 0
            if timed:
                deadline = get_time() + MAX_IDLE_SECONDS
        else:
            idle_passes += 1
            stalled = idle_passes > MAX_IDLE_PASSES
            if timed:
                stalled = get_time() > deadline
            if stalled:
                quick_print("Wood worker made no progress")
                return False
        first = False
    return True


def farm_multi(target_stock, ws=None):
    if num_items(Items.Wood) >= target_stock:
        return True
    if not utils_farm.is_funded(requirements(target_stock)):
        return False
    if num_unlocked(Unlocks.Megafarm) == 0:
        quick_print("Wood multi requires Megafarm")
        return False
    if not utils_farm.can_start_phase():
        return False
    actual_size = get_world_size()
    if ws != None and ws != actual_size:
        quick_print("Wood production requires the current world size")
        return False
    ws = actual_size
    has_trees = num_unlocked(Unlocks.Trees) > 0
    if not utils_move.go_to(0, 0, ws):
        return False
    handles = []
    success = True
    for _ in range(ws):
        if num_items(Items.Wood) >= target_stock:
            break
        handle = spawn_drone(_worker, ws, target_stock, has_trees)
        if handle == None:
            if not _worker(ws, target_stock, has_trees):
                success = False
                break
        else:
            handles.append(handle)
        if not move(East):
            success = False
            break
    joined = utils_farm.join_workers(handles)
    if not success or not joined or num_items(Items.Wood) < target_stock:
        return False
    return utils_move.go_to(0, 0, ws)


def farm_single(target_stock, has_trees=None):
    if num_items(Items.Wood) >= target_stock:
        return True
    if not utils_farm.is_funded(requirements(target_stock)):
        return False
    if not utils_farm.can_start_phase():
        return False
    if has_trees == None:
        has_trees = num_unlocked(Unlocks.Trees) > 0
    ws = get_world_size()
    if not utils_move.go_to(0, 0, ws):
        return False
    first = True
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + MAX_IDLE_SECONDS
    idle_passes = 0
    while num_items(Items.Wood) < target_stock:
        before = num_items(Items.Wood)
        for _ in range(ws):
            if not _column(ws, has_trees) or not move(East):
                return False
        if first or num_items(Items.Wood) > before:
            idle_passes = 0
            if timed:
                deadline = get_time() + MAX_IDLE_SECONDS
        else:
            idle_passes += 1
            stalled = idle_passes > MAX_IDLE_PASSES
            if timed:
                stalled = get_time() > deadline
            if stalled:
                quick_print("Wood production made no progress")
                return False
        first = False
    return utils_move.go_to(0, 0, ws)
