import utils_farm
import utils_move


def _item(entity):
    if entity == Entities.Grass:
        return Items.Hay
    if entity == Entities.Bush or entity == Entities.Tree:
        return Items.Wood
    if entity == Entities.Carrot:
        return Items.Carrot
    return None


def requirements(entity, target_stock):
    item = _item(entity)
    if item == None:
        return None
    if num_items(item) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Polyculture) == 0:
        return None
    if entity == Entities.Tree and num_unlocked(Unlocks.Trees) == 0:
        return None
    if entity != Entities.Carrot:
        # Reject paid companions: Hay/Wood production cannot consume its own inputs.
        return {}
    if num_unlocked(Unlocks.Carrots) == 0:
        return None
    # One root per independent zone, with a reserve for rerolling locked Trees.
    ws = get_world_size()
    roots = max(1, ws // 7) ** 2
    attempts = 1
    if num_unlocked(Unlocks.Trees) == 0:
        attempts = 64
    return utils_farm.seed_requirements(Entities.Carrot, roots * attempts)


def _plant(entity):
    current = get_entity_type()
    if current == entity:
        return True
    if current != None:
        # Cleanup is deliberate: harvest(False) may simply discard immature growth.
        harvest()
    if entity == Entities.Carrot:
        if get_ground_type() != Grounds.Soil:
            till()
    elif entity == Entities.Grass and get_ground_type() != Grounds.Grassland:
        till()
    return plant(entity)


def _root(entity, ws, has_trees):
    x, y = get_pos_x(), get_pos_y()
    request = None
    for attempt in range(64):
        if not _plant(entity):
            return False
        if ws == 1:
            break
        request = get_companion()
        if request == None:
            break
        companion, position = request
        if (companion != Entities.Carrot or entity == Entities.Carrot) and (
            companion != Entities.Tree or has_trees
        ):
            break
        harvest()
        request = None
        if attempt == 63:
            quick_print("No affordable companion request")
            return False
    utils_farm.water()
    if request != None:
        companion, (cx, cy) = request
        if not utils_move.go_to(cx, cy, ws) or not _plant(companion):
            return False
        if not utils_move.go_to(x, y, ws):
            return False
    if not utils_farm.wait_ripe():
        return False
    return harvest()


def _produce(entity, target_stock, parallel):
    item = _item(entity)
    if item == None:
        return False
    if num_items(item) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(entity, target_stock), parallel):
        return False
    ws = get_world_size()
    has_trees = num_unlocked(Unlocks.Trees) > 0
    # Companion radius is three. Centers seven apart cannot overwrite each other.
    centers = []
    if ws < 7:
        centers.append(ws // 2)
    else:
        for center in range(3, ws - 3, 7):
            centers.append(center)
    handles = []
    success = True
    for x in centers:
        for y in centers:
            if not utils_move.go_to(x, y, ws):
                success = False
                break
            handle = None
            if parallel:
                handle = spawn_drone(_root, entity, ws, has_trees)
            if handle == None:
                if not _root(entity, ws, has_trees):
                    success = False
                    break
            else:
                handles.append(handle)
        if not success:
            break
    joined = utils_farm.join_workers(handles)
    if not success or not joined:
        return False
    return utils_move.go_to(0, 0, ws)


def produce_single(entity, target_stock):
    return _produce(entity, target_stock, False)


def produce_multi(entity, target_stock):
    return _produce(entity, target_stock, True)


def _farm(entity, target_stock, parallel):
    item = _item(entity)
    if item == None:
        return False
    stalled = 0
    while num_items(item) < target_stock:
        before = num_items(item)
        if not _produce(entity, target_stock, parallel):
            return False
        if num_items(item) <= before:
            stalled += 1
            if stalled >= 8:
                return False
        else:
            stalled = 0
    return True


def farm_single(entity, target_stock):
    return _farm(entity, target_stock, False)


def farm_multi(entity, target_stock):
    return _farm(entity, target_stock, True)
