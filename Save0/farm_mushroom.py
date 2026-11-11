# Progression producer: absolute stock targets; single/multi entry points.
import utils_farm
import utils_mine

# Bound the search and collection separately: mushrooms do not grow.
_DIG_BUDGET = 1024
_PASS_LIMIT = 24


def _seek_mushroom(budget):
    used = 0
    while used < budget:
        ground = get_ground_type()
        if ground == Grounds.Mushroom:
            return True, used
        if ground == Grounds.Bedrock:
            return False, used
        z = get_pos_z()
        dig()
        used += 1
        if get_pos_z() >= z:
            return None, used
    return get_ground_type() == Grounds.Mushroom, used


def _stratum_single(qty):
    ws = get_world_size()
    if ws < 2:
        return False
    return _collect_layer(qty, [(0, 0, ws, ws)])


def requirements(target_stock):
    if num_items(Items.Mushroom) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Mushrooms) == 0:
        return None
    return {}


def produce_single(target_stock):
    if num_items(Items.Mushroom) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock)) or not utils_mine.prepare():
        return False
    result = _stratum_single(target_stock)
    return result or num_items(Items.Mushroom) >= target_stock


def farm_single(target_stock):
    stalled = 0
    while num_items(Items.Mushroom) < target_stock:
        before = num_items(Items.Mushroom)
        if not produce_single(target_stock):
            return False
        if num_items(Items.Mushroom) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Mushroom)
                return False
        else:
            stalled = 0
    return True


def _prepare_sector(qty, sector, level, budget, deep=False):
    # Only expose the reference height. Never drill through the colony just
    # because one tile has already lost its top mushroom in a cave-in.
    x0, y0, x1, y1 = sector
    width, height = x1 - x0, y1 - y0
    seeded = False
    for row in range(height):
        x, direction = x0, East
        if row % 2 == 1:
            x, direction = x1 - 1, West
        if not utils_mine.go_to(x, y0 + row):
            return False
        for column in range(width):
            if num_items(Items.Mushroom) >= qty:
                return True
            limit = _DIG_BUDGET
            if deep:
                limit = max(limit, get_pos_z() - level + 1)
            for _ in range(limit):
                if get_pos_z() <= level or get_ground_type() == Grounds.Bedrock:
                    break
                z = get_pos_z()
                dig()
                if get_pos_z() >= z:
                    return False
            if get_pos_z() > level and get_ground_type() != Grounds.Bedrock:
                return False
            # A flat colony needs one opening per sector, completed before the
            # preparation join. No digging is allowed in the collection passes.
            if not seeded and get_ground_type() == Grounds.Mushroom:
                z = get_pos_z()
                dig()
                if get_pos_z() >= z:
                    return False
                seeded = True
            if column < width - 1 and not move(direction):
                return False
    return True


def _visit(qty, x, y, sector, turn):
    x0, y0, x1, y1 = sector
    directions = [(East, 1, 0), (North, 0, 1), (West, -1, 0), (South, 0, -1)]
    # Matching pushes can expose another usable mushroom below the source.
    for _ in range(16):
        if num_items(Items.Mushroom) >= qty or get_ground_type() != Grounds.Mushroom:
            return True
        kind = measure()
        matched = False
        for direction, dx, dy in directions:
            if x0 <= x + dx and x + dx < x1 and y0 <= y + dy and y + dy < y1:
                if (
                    can_push(direction)
                    and get_ground_type(direction) == Grounds.Mushroom
                    and measure(direction) == kind
                ):
                    if push(direction):
                        matched = True
                        break
        if matched:
            continue
        # Move at most one unmatched block, without following or digging below
        # it. Rotating the preference avoids a permanent east/west-only lane.
        for index in range(4):
            direction, dx, dy = directions[(x + y + turn + index) % 4]
            if x0 <= x + dx and x + dx < x1 and y0 <= y + dy and y + dy < y1:
                if can_push(direction) and push(direction):
                    break
        return True
    return True


def _stratum_multi(qty, sector, turn, budget):
    x0, y0, x1, y1 = sector
    width, height = x1 - x0, y1 - y0
    lines, length = height, width
    if turn % 2 == 1:
        lines, length = width, height
    for line in range(lines):
        x, y, dx, dy, direction = x0, y0 + line, 1, 0, East
        if turn % 2 == 1:
            x, y, dx, dy, direction = x0 + line, y0, 0, 1, North
        if line % 2 == 1:
            x += (length - 1) * dx
            y += (length - 1) * dy
            dx, dy = -dx, -dy
            direction = West
            if turn % 2 == 1:
                direction = South
        if not utils_mine.go_to(x, y):
            return False
        for cell in range(length):
            if num_items(Items.Mushroom) >= qty:
                return True
            _visit(qty, x, y, sector, turn)
            if cell < length - 1:
                if not move(direction):
                    return False
                x, y = x + dx, y + dy
    return True


def _prepare_deep_sector(qty, sector, level, budget):
    return _prepare_sector(qty, sector, level, budget, True)


def _collect_layer(qty, sectors, deep=False):
    found, used = _seek_mushroom(_DIG_BUDGET)
    if found == None:
        return False
    if not found:
        return True
    level = get_pos_z()
    quick_print("Mushroom preparing layer", level)
    # This join is a real preparation barrier, before any collection worker.
    prepared = False
    if deep:
        prepared = utils_mine.run_sectors(
            _prepare_deep_sector, Items.Mushroom, qty, sectors, level
        )
    else:
        prepared = utils_mine.run_sectors(
            _prepare_sector, Items.Mushroom, qty, sectors, level
        )
    if not prepared:
        return num_items(Items.Mushroom) >= qty
    quick_print("Mushroom collecting layer", level)
    stalled = 0
    for turn in range(_PASS_LIMIT):
        before = num_items(Items.Mushroom)
        result = utils_mine.run_sectors(
            _stratum_multi, Items.Mushroom, qty, sectors, turn
        )
        # All children are joined, including after a refused action.
        if num_items(Items.Mushroom) >= qty:
            return True
        if not result:
            return False
        if num_items(Items.Mushroom) > before:
            stalled = 0
        else:
            stalled += 1
        # Allow initial rearrangements, then leave an exhausted layer finitely.
        if turn >= 3 and stalled >= 4:
            break
    return True


def collect_current_layer(target_stock, parallel=True, deep=False):
    # A world-owning scenario has already funded/prepared the current layer.
    if not utils_farm.can_start_phase() or num_unlocked(Unlocks.Mushrooms) == 0:
        return False
    if get_ground_type() != Grounds.Mushroom:
        return False
    sectors = utils_mine.sector_plan(parallel)
    return _collect_layer(target_stock, sectors, deep)


def produce_multi(target_stock):
    if num_items(Items.Mushroom) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), True):
        return False
    if num_unlocked(Unlocks.Underground_Senses) == 0 or get_world_size() < 2:
        return False
    sectors = utils_mine.sector_plan(True, target_stock - num_items(Items.Mushroom))
    if len(sectors) == 0 or not utils_mine.prepare():
        return False
    result = _collect_layer(target_stock, sectors)
    # run_sectors has joined every child. A late refusal cannot invalidate stock
    # that another owned worker has already finished collecting.
    return result or num_items(Items.Mushroom) >= target_stock


def farm_multi(target_stock):
    stalled = 0
    while num_items(Items.Mushroom) < target_stock:
        before = num_items(Items.Mushroom)
        if not produce_multi(target_stock):
            return False
        if num_items(Items.Mushroom) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Mushroom)
                return False
        else:
            stalled = 0
    return True
