import utils_farm
import utils_mine

PROBE_DIGS = 2
SEARCH_ROUNDS = 32  # Finite surface-world search, never a deep mining campaign.


def requirements(target_stock):
    if num_items(Items.Coal) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Coal) == 0 or num_unlocked(Unlocks.Underground_Senses) == 0:
        return None
    return {}


def _sites(parallel, remaining):
    ws = get_world_size()
    capacity = 1
    if parallel:
        capacity = min(max_drones(), max(1, ws // 3) ** 2, max(1, remaining))
    columns, rows = 1, 1
    while columns * rows * 2 <= capacity:
        if columns <= rows:
            columns *= 2
        else:
            rows *= 2
    sites = []
    for row in range(rows):
        for column in range(columns):
            x0, x1 = column * ws // columns, (column + 1) * ws // columns
            y0, y1 = row * ws // rows, (row + 1) * ws // rows
            sites.append(((x0 + x1 - 1) // 2, (y0 + y1 - 1) // 2))
    return sites


def _visible(x, y, ws):
    hits = []
    if get_ground_type() == Grounds.Coal:
        hits.append((x, y, get_pos_z()))
    for direction, nx, ny in [
        (North, x, y + 1),
        (East, x + 1, y),
        (South, x, y - 1),
        (West, x - 1, y),
    ]:
        if 0 <= nx and nx < ws and 0 <= ny and ny < ws:
            if get_ground_type(direction) == Grounds.Coal:
                hits.append((nx, ny, get_pos_z(direction)))
    return hits


def _probe(x, y, qty, ws):
    if num_items(Items.Coal) >= qty:
        return True, [], True
    if not utils_mine.go_to(x, y):
        return False, [], False
    for step in range(PROBE_DIGS + 1):
        if num_items(Items.Coal) >= qty:
            return True, [], True
        hits = _visible(x, y, ws)
        ground = get_ground_type()
        finished = (
            ground == Grounds.Clay
            or ground == Grounds.Rock
            or ground == Grounds.Bedrock
        )
        if len(hits) > 0 or finished or step == PROBE_DIGS:
            return True, hits, finished
        before = get_pos_z()
        dig()
        if get_pos_z() >= before:
            return False, [], False
    return False, [], False


def _survey(sites, qty, parallel, ws):
    handles, results = [], []
    for index in range(len(sites)):
        x, y = sites[index]
        # The parent is one of the available drones. Workers travel themselves.
        handle = None
        if parallel and index < len(sites) - 1:
            handle = spawn_drone(_probe, x, y, qty, ws)
        if handle == None:
            results.append((index, _probe(x, y, qty, ws)))
        else:
            handles.append((index, handle))
    for index, handle in handles:
        results.append((index, wait_for(handle)))
    success, hits, finished = True, set(), set()
    for index, result in results:
        if result == None:
            success = False
        else:
            ok, found, done = result
            success = success and ok
            for hit in found:
                hits.add(hit)
            if done:
                finished.add(index)
    active = []
    for index in range(len(sites)):
        if index not in finished:
            active.append(sites[index])
    return success, hits, active


def _column(x, starts, level, qty, ws):
    # One column per worker in a wave. Empty fringe cells reveal diagonals;
    # they are inspected without digging or following a lower Coal sheet.
    pending = list(starts)
    checked, hits = set(), set()
    while len(pending) > 0:
        if num_items(Items.Coal) >= qty:
            return True, hits
        # Stack order finishes North before South instead of zigzagging between
        # both ends of the growing segment on every new cell.
        y = pending.pop()
        if y in checked:
            continue
        checked.add(y)
        if not utils_mine.go_to(x, y):
            return False, hits
        coal = get_pos_z() == level and get_ground_type() == Grounds.Coal
        if coal:
            dig()
            if get_pos_z() >= level:
                return False, hits
        for direction, nx in [(East, x + 1), (West, x - 1)]:
            if 0 <= nx and nx < ws and get_ground_type(direction) == Grounds.Coal:
                if get_pos_z(direction) == level:
                    hits.add((nx, y))
        if coal:
            if y > 0:
                pending.append(y - 1)
            if y < ws - 1:
                pending.append(y + 1)
    return True, hits


def _collect(level, seeds, qty, parallel, ws):
    if len(seeds) == 0:
        return True
    px, py = get_pos_x(), get_pos_y()
    nearest, distance = None, 2 * ws
    for x, y in seeds:
        dx, dy = abs(x - px), abs(y - py)
        travel = min(dx, ws - dx) + min(dy, ws - dy)
        if travel < distance:
            nearest, distance = (x, y), travel
    if not utils_mine.go_to(nearest[0], nearest[1]):
        return False
    pending, seen = {}, set()
    for x, y in [nearest] + seeds:
        if (x, y) in seen:
            continue
        if x not in pending:
            pending[x] = []
        pending[x].append(y)
        seen.add((x, y))
    capacity = 1
    if parallel:
        capacity = max_drones()
    # Each new seed is dispatched once; no more than ws*ws seeds exist.
    while len(pending) > 0 and num_items(Items.Coal) < qty:
        columns = []
        for x in pending:
            if len(columns) < capacity:
                columns.append(x)
        handles, results = [], []
        for index in range(len(columns)):
            x = columns[index]
            starts = pending.pop(x)
            handle = None
            if parallel and index < len(columns) - 1:
                handle = spawn_drone(_column, x, starts, level, qty, ws)
            if handle == None:
                results.append(_column(x, starts, level, qty, ws))
            else:
                handles.append(handle)
        for handle in handles:
            results.append(wait_for(handle))
        success = True
        for result in results:
            if result == None:
                success = False
                continue
            ok, hits = result
            success = success and ok
            for x, y in hits:
                if (x, y) in seen:
                    continue
                seen.add((x, y))
                if x not in pending:
                    pending[x] = []
                pending[x].append(y)
        if not success:
            return False
    return True


def _produce(target_stock, parallel):
    if num_items(Items.Coal) >= target_stock:
        return True
    if (
        PROBE_DIGS < 1
        or PROBE_DIGS % 1 != 0
        or SEARCH_ROUNDS < 1
        or SEARCH_ROUNDS % 1 != 0
        or get_world_size() < 1
    ):
        return False
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    ws = get_world_size()
    sites = _sites(parallel, target_stock - num_items(Items.Coal))
    if not utils_mine.prepare():
        return False
    for _ in range(SEARCH_ROUNDS):
        success, hits, sites = _survey(sites, target_stock, parallel, ws)
        if not success:
            return False
        # Repeatedly select the highest discovered sheet without relying on sort.
        while len(hits) > 0 and num_items(Items.Coal) < target_stock:
            level = None
            for x, y, z in hits:
                if level == None or z > level:
                    level = z
            seeds, lower = [], set()
            for x, y, z in hits:
                if z == level:
                    seeds.append((x, y))
                else:
                    lower.add((x, y, z))
            if not _collect(level, seeds, target_stock, parallel, ws):
                return False
            hits = lower
        if num_items(Items.Coal) >= target_stock or len(sites) == 0:
            return True
    return True


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Coal) < target_stock:
        before = num_items(Items.Coal)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Coal) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Coal search made no progress", target_stock)
                return False
        else:
            stalled = 0
    return True


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
