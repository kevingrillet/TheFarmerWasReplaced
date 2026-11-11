import utils_farm
import utils_move

CHECK_EVERY_ROUNDS = 16
MAX_IDLE_SWEEPS = 262144


def _multi_plan(target_stock):
    ws = get_world_size()
    columns = min(ws, max_drones())
    minimum = columns * ws * CHECK_EVERY_ROUNDS
    cost = get_cost(Entities.Sunflower)
    available = None
    for item in cost:
        if cost[item] > 0:
            count = num_items(item) // cost[item]
            if available == None or count < available:
                available = count
    if available == None:
        # Even free-seed simulations keep a finite fallback budget.
        available = 2 * max(1, target_stock - num_items(Items.Power)) // 1 + 1
    return columns, max(minimum, available), cost


def requirements(target_stock, parallel=False):
    if num_items(Items.Power) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Sunflowers) == 0:
        return None
    if parallel:
        if num_unlocked(Unlocks.Megafarm) == 0:
            return None
        if CHECK_EVERY_ROUNDS < 1 or CHECK_EVERY_ROUNDS % 1 != 0:
            quick_print("Power checkpoint must be a positive whole number")
            return None
        columns, plants, cost = _multi_plan(target_stock)
        needs = {}
        for item in cost:
            needs[item] = cost[item] * plants
        return needs
    return utils_farm.seed_requirements(Entities.Sunflower, get_world_size() ** 2)


def _column(ws):
    x = get_pos_x()
    petals = {}
    for count in range(7, 16):
        petals[count] = []
    for y in range(ws):
        if get_ground_type() != Grounds.Soil:
            till()
        if not plant(Entities.Sunflower):
            return False
        utils_farm.water()
        count = measure()
        if count == None or count not in petals:
            return False
        petals[count].append(y)
        if not move(North):
            return False
    # Finite owned columns: no population barrier or mutation during for.
    for count in range(15, 6, -1):
        bucket = petals[count]
        while len(bucket) > 0:
            y = bucket.pop()
            if not utils_move.go_to(x, y, ws):
                return False
            if not utils_farm.wait_ripe() or not harvest():
                return False
    return utils_move.go_to(x, 0, ws)


def _column_continuous(ws, target_stock, seeds_left, seed_cost=None):
    # Each worker owns a disjoint part of the funded stock, not just 16 rounds.
    # Renew local planting chunks without respawning or borrowing another quota.
    # Visit other plants while immature Sunflowers grow; never replant them.
    if seed_cost == None:
        seed_cost = get_cost(Entities.Sunflower)
    authorized = 0
    best_stock = num_items(Items.Power)
    timed = num_unlocked(Unlocks.Timing) > 0
    last_gain = 0
    if timed:
        last_gain = get_time()
    idle = 0
    while idle < MAX_IDLE_SWEEPS:
        empty = 0
        for _ in range(ws):
            if num_items(Items.Power) >= target_stock:
                return True
            if get_ground_type() != Grounds.Soil:
                till()
                if get_ground_type() != Grounds.Soil:
                    return False
            utils_farm.water()
            entity = get_entity_type()
            if entity != None and can_harvest():
                if not harvest():
                    return False
                entity = None
                if num_items(Items.Power) >= target_stock:
                    return True
            if entity == None:
                if seeds_left > 0 and authorized == 0:
                    authorized = min(ws * CHECK_EVERY_ROUNDS, seeds_left)
                    needs = {}
                    for item in seed_cost:
                        needs[item] = seed_cost[item] * authorized
                    if not utils_farm.is_funded(needs):
                        # Drain paid plants, then let the joined parent refinance.
                        seeds_left, authorized = 0, 0
                if seeds_left > 0:
                    if not plant(Entities.Sunflower):
                        return False
                    seeds_left -= 1
                    authorized -= 1
                else:
                    empty += 1
            elif entity != Entities.Sunflower:
                return False
            if not move(North):
                return False
        if seeds_left == 0 and empty == ws:
            return True
        stock = num_items(Items.Power)
        if stock > best_stock:
            best_stock = stock
            idle = 0
            if timed:
                last_gain = get_time()
        else:
            idle += 1
            if timed and get_time() - last_gain > 180:
                break
    quick_print("Power column made no progress")
    return False


def _continuous_columns(ws, target_stock):
    # Snapshot once before any spawn: concurrent workers cannot all claim the
    # same available carrots. Copied quotas add up to this one funded reserve.
    columns, budget, cost = _multi_plan(target_stock)
    handles = []
    success = True
    finish = target_stock + 1
    for column in range(columns):
        if num_items(Items.Power) >= finish:
            break
        handle = None
        allowance = budget // columns
        if column < budget % columns:
            allowance += 1
        if column < columns - 1:
            handle = spawn_drone(_column_continuous, ws, finish, allowance, cost)
        if handle == None:
            if not _column_continuous(ws, finish, allowance, cost):
                success = False
                break
        else:
            handles.append(handle)
        if column < columns - 1 and not move(East):
            success = False
            break
    joined = utils_farm.join_workers(handles)
    return success and joined


def _produce(target_stock, parallel):
    if num_items(Items.Power) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock, parallel), parallel):
        return False
    ws = get_world_size()
    clear()
    if parallel:
        return _continuous_columns(ws, target_stock)
    for _ in range(ws):
        if not _column(ws) or not move(East):
            return False
    return True


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    if num_items(Items.Power) >= target_stock:
        return True
    stalled = 0
    while num_items(Items.Power) < target_stock:
        before = num_items(Items.Power)
        if not _produce(target_stock + 1, parallel):
            return False
        if num_items(Items.Power) <= before:
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
