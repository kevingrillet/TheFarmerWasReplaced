def fertilizer():
    # Action result: False means skipped or refused, not a production failure.

    if num_items(Items.Fertilizer) > num_drones():
        return use_item(Items.Fertilizer)
    return False


def fertilizer_or_water():
    if not fertilizer():
        return water()
    return True


def q_harvest():
    # Harvest if possible

    if can_harvest():
        return harvest()
    return False


def q_till():
    # State result: True means Soil, including an already prepared tile.
    ground = get_ground_type()
    if ground == Grounds.Soil:
        return True
    if ground != Grounds.Grassland:
        return False
    till()
    # Native till() returns None, so verify the resulting ground instead.
    return get_ground_type() == Grounds.Soil


def q_till_grass():
    # State result: True means Grassland; other underground/special soils stay intact.
    ground = get_ground_type()
    if ground == Grounds.Grassland:
        return True
    if ground != Grounds.Soil:
        return False
    till()
    return get_ground_type() == Grounds.Grassland


def till_all(ws):
    # Complete wrapping rows, returning to the starting tile only on success.
    if ws < 1 or ws != get_world_size():
        return False
    if not can_start_phase():
        return False
    for _ in range(ws):
        for _ in range(ws):
            if not move(East) or not q_till():
                return False
        if not move(North):
            return False
    return True


def water():
    # Action result: optional watering can be skipped or refused.

    if get_water() < 0.75 and num_items(Items.Water) > num_drones():
        return use_item(Items.Water)
    return False


def join_workers(handles):
    # Join all owned tasks even if an earlier result reports failure.
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def can_start_phase():
    # Refuse a new world-changing phase while unowned workers are active.
    if num_unlocked(Unlocks.Megafarm) > 0 and num_drones() > 1:
        quick_print("Production blocked: previous workers are still active")
        return False
    return True


def seed_requirements(entity, plants):
    if plants < 0:
        return None
    if plants == 0:
        return {}
    needs = {}
    cost = get_cost(entity)
    for item in cost:
        needs[item] = cost[item] * plants
    return needs


def is_funded(needs):
    if needs == None:
        quick_print("Production locked or unsupported")
        return False
    for item in needs:
        if num_items(item) < needs[item]:
            quick_print("Production requires funding", item, needs[item])
            return False
    return True


def preflight(needs, parallel=False):
    # Only at phase boundaries, never inside the action loop.
    if parallel and num_unlocked(Unlocks.Megafarm) == 0:
        quick_print("Multi production requires Megafarm")
        return False
    return is_funded(needs) and can_start_phase()


def wait_ripe(seconds=180):
    # State result; optional watering does not decide whether the plant is ripe.
    if can_harvest():
        return True
    if seconds <= 0:
        return False
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + seconds
    for _ in range(262144):
        if can_harvest():
            return True
        if timed and get_time() > deadline:
            break
        water()
    quick_print("Plant did not mature")
    return False
