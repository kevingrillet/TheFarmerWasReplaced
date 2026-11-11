import utils_farm
import utils_mine


def _plan(target_stock):
    ws = get_world_size()
    min_yield = 64 * 2 ** (num_unlocked(Unlocks.Bamboo) - 1)
    plants = max(
        1, (target_stock - num_items(Items.Bamboo) + min_yield - 1) // min_yield
    )
    columns = min(ws // 2, plants)
    if columns < 1:
        return 0, 0
    steps = min(ws, (plants + columns - 1) // columns)
    # Large goals can use the old corridors after the first wave is harvested.
    remaining = plants - columns * steps
    if remaining > 0:
        columns += min(ws // 2, (remaining + steps - 1) // steps)
    return columns, steps


def requirements(target_stock):
    if num_items(Items.Bamboo) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Bamboo) == 0 or num_unlocked(Unlocks.Timing) == 0:
        return None
    columns, steps = _plan(target_stock)
    if columns == 0:
        return None
    return utils_farm.seed_requirements(Entities.Bamboo, columns * steps)


def _wait(seconds):
    end = get_time() + seconds
    while get_time() < end:
        pass


def _column(qty, steps):
    # Retained serial diagnostic; normal production uses corridor-owned batches.
    for _ in range(steps):
        if num_items(Items.Bamboo) >= qty:
            return True
        if get_ground_type() != Grounds.Soil:
            till()
        if not plant(Entities.Bamboo):
            return False
        height = measure()
        if height == None or not move(North):
            return False
        _wait(height + 1)
        for _ in range(2):
            if not hover(height) or not move(South):
                return False
            next_height = measure()
            if next_height == None or not move(North):
                return False
            _wait(next_height - height + 1)
            height = next_height
        if not hover(0) or not move(South) or not move(North):
            return False
    return True


def _batch(qty, x, steps):
    # Plant a whole batch before waiting. The neighboring column is a corridor;
    # all fruit state is created inside its owning worker, never shared globals.
    corridor = x + 1
    enter, leave = West, East
    if x % 2 == 1:
        corridor = x - 1
        enter, leave = East, West
    pending = {}
    for y in range(steps):
        if num_items(Items.Bamboo) >= qty:
            return True
        if not utils_mine.go_to(x, y):
            return False
        if get_ground_type() != Grounds.Soil:
            till()
        if not plant(Entities.Bamboo):
            return False
        height = measure()
        if height == None or not move(leave):
            return False
        pending[y] = (height, get_time() + height + 1, 0, 0)
    while len(pending) > 0:
        if num_items(Items.Bamboo) >= qty:
            return True
        wake = None
        finished = []
        for y in pending:
            height, ready, stage, retries = pending[y]
            if get_time() < ready:
                if wake == None or ready < wake:
                    wake = ready
                continue
            if not utils_mine.go_to(corridor, y):
                return False
            cut = height
            if stage == 2:
                cut = 0
            if not hover(cut) or not move(enter):
                return False
            if stage == 2:
                if not move(leave):
                    return False
                finished.append(y)
                continue
            next_height = measure()
            if not move(leave) or next_height == None:
                return False
            if next_height <= height:
                retries += 1
                if retries >= 6:
                    return False
                pending[y] = (height, get_time() + 1, stage, retries)
            else:
                pending[y] = (
                    next_height,
                    get_time() + next_height - height + 1,
                    stage + 1,
                    0,
                )
        for y in finished:
            pending.pop(y)
        if len(finished) == 0 and wake != None:
            _wait(max(0, wake - get_time()))
    return True


def _wave(target_stock, columns, steps, offset, parallel):
    handles = []
    success = True
    for column in range(columns):
        if num_items(Items.Bamboo) >= target_stock:
            break
        x = 2 * column + offset
        # The waiting coordinator always stays in a corridor, including at join.
        corridor = x + 1
        if offset == 1:
            corridor = x - 1
        if not utils_mine.go_to(corridor, 0):
            success = False
            break
        handle = None
        if parallel and column < columns - 1:
            handle = spawn_drone(_batch, target_stock, x, steps)
        if handle == None:
            if not _batch(target_stock, x, steps):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    return (success and joined) or num_items(Items.Bamboo) >= target_stock


def _produce(target_stock, parallel):
    if num_items(Items.Bamboo) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    columns, steps = _plan(target_stock)
    if columns == 0 or not utils_mine.prepare():
        return False
    first = min(columns, get_world_size() // 2)
    if not _wave(target_stock, first, steps, 0, parallel):
        return False
    if num_items(Items.Bamboo) >= target_stock:
        return True
    # All first-wave stems are cut and every child has joined before swapping.
    return _wave(target_stock, columns - first, steps, 1, parallel)


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Bamboo) < target_stock:
        before = num_items(Items.Bamboo)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Bamboo) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Bamboo)
                return False
        else:
            stalled = 0
    return True


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
