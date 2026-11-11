import utils_farm
import utils_move


def requirements(target_stock):
    if num_items(Items.Hay) >= target_stock and num_items(Items.Wood) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Plant) == 0:
        return None
    return {}


def _column(ws, target_stock, has_trees):
    x = get_pos_x()
    for y in range(ws):
        entity = Entities.Grass
        if (x + y) % 2 == 0:
            entity = Entities.Bush
            if has_trees:
                entity = Entities.Tree
        if ws == 1 and num_items(Items.Wood) >= target_stock:
            entity = Entities.Grass
        current = get_entity_type()
        if can_harvest():
            if not harvest():
                return False
            current = None
        if current != entity:
            # Discarding an immature mismatched plant can legitimately return False.
            if current != None:
                harvest()
            if not plant(entity):
                return False
        utils_farm.water()
        if not move(North):
            return False
    return True


def _farm(target_stock, parallel):
    if num_items(Items.Hay) >= target_stock and num_items(Items.Wood) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    ws = get_world_size()
    has_trees = num_unlocked(Unlocks.Trees) > 0
    clear()
    timed = num_unlocked(Unlocks.Timing) > 0
    deadlines, idle = {}, {}
    for item in [Items.Hay, Items.Wood]:
        deadlines[item] = 0
        idle[item] = 0
        if timed:
            deadlines[item] = get_time() + 180
    while num_items(Items.Hay) < target_stock or num_items(Items.Wood) < target_stock:
        before = {Items.Hay: num_items(Items.Hay), Items.Wood: num_items(Items.Wood)}
        handles = []
        success = True
        for _ in range(ws):
            handle = None
            if parallel:
                handle = spawn_drone(_column, ws, target_stock, has_trees)
            if handle == None:
                if not _column(ws, target_stock, has_trees):
                    success = False
                    break
            else:
                handles.append(handle)
            if not move(East):
                success = False
                break
        joined = utils_farm.join_workers(handles)
        if not success or not joined:
            return False
        for item in before:
            if num_items(item) >= target_stock or num_items(item) > before[item]:
                idle[item] = 0
                if timed:
                    deadlines[item] = get_time() + 180
            else:
                idle[item] += 1
                if idle[item] > 262144 or (timed and get_time() > deadlines[item]):
                    quick_print("Hay/Wood made no progress", item)
                    return False
    return utils_move.go_to(0, 0, ws)


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
