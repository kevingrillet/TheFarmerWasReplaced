# Finite mining phases. Funding belongs to resource_manager, not these workers.
import utils_farm
import utils_move

# Installed build 26462009: prospect_quartz consumes one Iron per call.
QUARTZ_PROBE_COST = 1


def prepare():
    if not utils_farm.can_start_phase():
        return False
    change_hat(Hats.Straw_Hat)
    clear()
    return True


def go_to(x, y):
    # Preserve the mining entry point: XY travel only, no digging or world reset.
    return utils_move.go_to(x, y, get_world_size())


def seek(ground, limit=256):
    for _ in range(limit):
        current = get_ground_type()
        if current == ground:
            return True
        if current == Grounds.Bedrock:
            return False
        dig()
    return get_ground_type() == ground


def run_columns(worker, qty, columns, steps, parallel):
    if columns < 0 or steps < 0:
        return False
    if columns == 0 or steps == 0:
        return True
    handles = []
    success = True
    for column in range(columns):
        if not go_to(column, 0):
            success = False
            break
        handle = None
        # The parent must leave the last planting tile too: drones block bamboo.
        if parallel and column < columns - 1:
            handle = spawn_drone(worker, qty, steps)
        if handle == None:
            if not worker(qty, steps):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    return success and joined


def column_plan(item, qty, min_yield):
    missing = qty - num_items(item)
    if missing <= 0 or min_yield <= 0:
        return 0, 0
    ws = get_world_size()
    if ws < 1:
        return 0, 0
    plants = missing // min_yield
    if plants * min_yield < missing:
        plants += 1
    plants = max(1, min(plants, ws * ws))
    columns = min(plants, ws)
    steps = (plants + columns - 1) // columns
    return columns, steps


def produce_columns(worker, item, qty, parallel, min_yield=1):
    if num_items(item) >= qty:
        return True
    columns, steps = column_plan(item, qty, min_yield)
    if columns == 0 or steps == 0:
        return False
    if not prepare():
        return False
    return run_columns(worker, qty, columns, steps, parallel)


def farm_columns(worker, item, qty, parallel, min_yield=1):
    stalled = 0
    while num_items(item) < qty:
        before = num_items(item)
        if not produce_columns(worker, item, qty, parallel, min_yield):
            return False
        if num_items(item) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Mining batches made no progress", item, qty)
                return False
        else:
            stalled = 0
    return True


def sector_plan(parallel, max_workers=None, min_width=3):
    # Balanced rectangles cover the field; nearby holes amplify cave-ins.
    ws = get_world_size()
    if ws < 1 or min_width < 1:
        return []
    count = 1
    if parallel:
        count = min(max_drones(), max(1, ws // min_width) ** 2)
    if max_workers != None:
        if max_workers <= 0:
            return []
        count = min(count, max(1, max_workers // 1))
    if count < 1:
        return []
    rows = 1
    while rows * rows < count:
        rows += 1
    sectors = []
    for row in range(rows):
        columns = count // rows
        if row < count % rows:
            columns += 1
        for column in range(columns):
            sectors.append(
                (
                    column * ws // columns,
                    row * ws // rows,
                    (column + 1) * ws // columns,
                    (row + 1) * ws // rows,
                )
            )
    return sectors


def run_sectors(worker, item, qty, sectors, options=None, probe_budget=0):
    if num_items(item) >= qty or len(sectors) == 0:
        return True
    if probe_budget < 0:
        return False
    ws = get_world_size()
    for x0, y0, x1, y1 in sectors:
        if x0 < 0 or y0 < 0 or x0 >= x1 or y0 >= y1 or x1 > ws or y1 > ws:
            return False
    handles = []
    success = True
    count = len(sectors)
    for index in range(count):
        if num_items(item) >= qty:
            break
        sector = sectors[index]
        x0, y0, x1, y1 = sector
        if not go_to((x0 + x1 - 1) // 2, (y0 + y1 - 1) // 2):
            success = False
            break
        # Divide a funded shared reserve once, never per copied worker state.
        allowance = probe_budget // count
        if index < probe_budget % count:
            allowance += 1
        handle = None
        if index < count - 1:
            handle = spawn_drone(worker, qty, sector, options, allowance)
        if handle == None:
            if not worker(qty, sector, options, allowance):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    return success and joined


def _excavate_sector(sector, level, protected, first_only, ignored, survey):
    x0, y0, x1, y1 = sector
    hits, kinds = [], set()
    remaining = False
    stability = 2
    for row in range(y1 - y0):
        y = y0 + row
        x, direction = x0, East
        if row % 2 == 1:
            x, direction = x1 - 1, West
        if not go_to(x, y):
            return False, hits, remaining, kinds, 0
        for column in range(x1 - x0):
            for _ in range(2048):
                ground = get_ground_type()
                z = get_pos_z()
                blocked = ground in protected
                if blocked and len(ignored) > 0:
                    blocked = (x, y, z, ground) not in ignored
                if blocked or ground == Grounds.Bedrock or z <= level:
                    break
                dig()
                if get_pos_z() >= z:
                    return False, hits, remaining, kinds, 0
            ground = get_ground_type()
            z = get_pos_z()
            key = x, y, z, ground
            if z >= level:
                kinds.add(ground)
            if ground in protected and key not in ignored and z >= level:
                hits.append(key)
                if first_only:
                    return True, hits, True, kinds, 0
            elif ground != Grounds.Bedrock and get_pos_z() > level:
                return False, hits, remaining, kinds, 0
            if ground != Grounds.Bedrock:
                remaining = True
                if survey:
                    # A two-layer band needs every surviving surface at the
                    # same height, with stability >=2. Never infer buried layers.
                    if z != level:
                        stability = 0
                    elif stability > 0:
                        observed = get_stability()
                        if observed == None:
                            stability = 0
                        else:
                            stability = min(stability, observed)
            if column < x1 - x0 - 1:
                if not move(direction):
                    return False, hits, remaining, kinds, 0
                if direction == East:
                    x += 1
                else:
                    x -= 1
    return True, hits, remaining, kinds, stability


def _excavate(level, protected, parallel, first_only, ignored, survey):
    # The caller owns the numeric height. No worker may start another layer;
    # every handle is joined before landmarks or the next height are processed.
    if not utils_farm.can_start_phase():
        return False, [], False, set(), 0
    if ignored == None:
        ignored = set()
    sectors = sector_plan(parallel)
    if len(sectors) == 0:
        return False, [], False, set(), 0
    handles, results = [], []
    for index in range(len(sectors)):
        handle = None
        if index < len(sectors) - 1:
            handle = spawn_drone(
                _excavate_sector,
                sectors[index],
                level,
                protected,
                first_only,
                ignored,
                survey,
            )
        if handle == None:
            result = _excavate_sector(
                sectors[index], level, protected, first_only, ignored, survey
            )
            results.append(result)
            if not result[0] or (first_only and len(result[1]) > 0):
                break
        else:
            handles.append(handle)
    for handle in handles:
        results.append(wait_for(handle))
    success, hits, remaining, kinds = True, [], False, set()
    stability = 2
    for result, found, active, types, observed in results:
        if not result:
            success = False
        hits += found
        remaining = remaining or active
        stability = min(stability, observed)
        for ground in types:
            kinds.add(ground)
    return success, hits, remaining, kinds, stability


def excavate_layer(level, protected, parallel=True, first_only=False, ignored=None):
    # Keep the original four-value contract, without extra stability observations.
    result, hits, active, kinds, stability = _excavate(
        level, protected, parallel, first_only, ignored, False
    )
    return result, hits, active, kinds


def excavate_band(level, protected, parallel=True, first_only=False, ignored=None):
    # Fifth value: minimum exposed stability capped at 2, or 0 for uneven terrain.
    # Only a complete preceding survey >=2 permits a two-layer next step.
    return _excavate(level, protected, parallel, first_only, ignored, True)


def _survey_sector(sector, protected, ignored):
    x0, y0, x1, y1 = sector
    hits, kinds = [], set()
    candidate = None
    active = False
    for row in range(y1 - y0):
        x, direction = x0, East
        if row % 2 == 1:
            x, direction = x1 - 1, West
        y = y0 + row
        if not go_to(x, y):
            return False, hits, candidate, active, kinds
        for column in range(x1 - x0):
            ground, z = get_ground_type(), get_pos_z()
            kinds.add(ground)
            if ground != Grounds.Bedrock:
                active = True
                key = x, y, z, ground
                if (
                    ground in protected
                    and key not in ignored
                    and (-1, -1, z, ground) not in ignored
                ):
                    hits.append(key)
                elif candidate == None or z > candidate[2]:
                    candidate = key
            if column < x1 - x0 - 1:
                if not move(direction):
                    return False, hits, candidate, active, kinds
                if direction == East:
                    x += 1
                else:
                    x -= 1
    return True, hits, candidate, active, kinds


def survey_surface(protected, parallel=True, ignored=None):
    # Read-only heads: no digging, funding or hat changes in scout workers.
    if not utils_farm.can_start_phase():
        return False, [], [], False, set()
    if ignored == None:
        ignored = set()
    sectors = sector_plan(parallel)
    if len(sectors) == 0:
        return False, [], [], False, set()
    handles, results = [], []
    for index in range(len(sectors)):
        handle = None
        if index < len(sectors) - 1:
            handle = spawn_drone(_survey_sector, sectors[index], protected, ignored)
        if handle == None:
            result = _survey_sector(sectors[index], protected, ignored)
            results.append(result)
            if not result[0]:
                break
        else:
            handles.append(handle)
    for handle in handles:
        results.append(wait_for(handle))
    success, hits, sites, active, kinds = True, [], [], False, set()
    for result, found, site, remaining, types in results:
        success = success and result
        hits += found
        if site != None:
            sites.append(site)
        active = active or remaining
        for ground in types:
            kinds.add(ground)
    return success, hits, sites, active, kinds


def _ore_sector(qty, sector, options, budget):
    ground, item, prospect = options
    x0, y0, x1, y1 = sector
    home_x, home_y = (x0 + x1 - 1) // 2, (y0 + y1 - 1) // 2
    x, y = home_x, home_y
    following = False
    dig_hint = False
    rock_seen = False
    directions = [
        (North, South, 0, 1),
        (East, West, 1, 0),
        (South, North, 0, -1),
        (West, East, -1, 0),
    ]
    for _ in range(256):
        if num_items(item) >= qty:
            return True
        current = get_ground_type()
        if current == Grounds.Bedrock:
            if x == home_x and y == home_y:
                return True
            if not go_to(home_x, home_y):
                return False
            x, y = home_x, home_y
            following = False
            dig_hint = False
            continue
        if current == Grounds.Rock:
            rock_seen = True
        if current == ground:
            dig()
            following = True
            dig_hint = False
            continue
        found = False
        for direction, reverse, dx, dy in directions:
            nx, ny = x + dx, y + dy
            if x0 <= nx and nx < x1 and y0 <= ny and ny < y1:
                if get_ground_type(direction) == ground:
                    if not move(direction):
                        return False
                    x, y = nx, ny
                    following = True
                    found = True
                    break
        if found:
            continue
        if following:
            # The accessible vein ended. Resume drilling at this sector's seed.
            following = False
            dig_hint = False
            if x != home_x or y != home_y:
                if not go_to(home_x, home_y):
                    return False
                x, y = home_x, home_y
                continue
        if (
            prospect == Items.Coal
            and current == Grounds.Rock
            and budget > 0
            and num_items(Items.Coal) > 0
        ):
            budget -= 1
            direction = prospect_iron()
            # None can mean iron directly below, not just absence of a vein.
            dig_hint = direction == None
            for candidate, reverse, dx, dy in directions:
                if candidate == direction:
                    nx, ny = x + dx, y + dy
                    if x0 <= nx and nx < x1 and y0 <= ny and ny < y1:
                        if not move(direction):
                            return False
                        x, y = nx, ny
                        dig_hint = True
                        found = True
                    break
        elif (
            prospect == Items.Iron
            and rock_seen
            and budget > 0
            and num_items(Items.Iron) >= QUARTZ_PROBE_COST
        ):
            budget -= 1
            distance = prospect_quartz()
            dig_hint = distance != None
            if distance != None:
                for direction, reverse, dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if x0 <= nx and nx < x1 and y0 <= ny and ny < y1:
                        if budget < 1 or num_items(Items.Iron) < QUARTZ_PROBE_COST:
                            break
                        if not move(direction):
                            return False
                        budget -= 1
                        candidate = prospect_quartz()
                        if candidate != None and candidate < distance:
                            x, y = nx, ny
                            found = True
                            break
                        if not move(reverse):
                            return False
        if found:
            continue
        if not dig_hint and (x != home_x or y != home_y):
            if not go_to(home_x, home_y):
                return False
            x, y = home_x, home_y
            continue
        dig()
    return True


def _produce_ore_multi(ground, item, qty, prospect):
    if num_items(item) >= qty:
        return True
    if not utils_farm.preflight(ore_requirements(prospect), True):
        return False
    if num_unlocked(Unlocks.Underground_Senses) == 0:
        return False
    sectors = sector_plan(True, qty - num_items(item))
    if len(sectors) == 0:
        return False
    budget = 0
    if prospect == Items.Coal and num_unlocked(Unlocks.Prospecting) > 0:
        budget = min(64, num_items(Items.Coal))
    elif prospect == Items.Iron:
        budget = min(128, num_items(Items.Iron) // QUARTZ_PROBE_COST)
    if not prepare():
        return False
    return run_sectors(
        _ore_sector, item, qty, sectors, (ground, item, prospect), budget
    )


def ore_requirements(prospect):
    if prospect == Items.Coal and num_unlocked(Unlocks.Prospecting) > 0:
        if num_items(Items.Coal) < 32:
            return {Items.Coal: 64}
    if prospect == Items.Iron and num_items(Items.Iron) < 64:
        return {Items.Iron: 128}
    return {}


def produce_ore(ground, item, qty, prospect=None, parallel=False):
    if parallel:
        return _produce_ore_multi(ground, item, qty, prospect)
    if num_items(item) >= qty:
        return True
    if not utils_farm.is_funded(ore_requirements(prospect)) or not prepare():
        return False
    directions = [North, East, South, West]
    for _ in range(256):
        if num_items(item) >= qty:
            return True
        current = get_ground_type()
        if current == Grounds.Bedrock:
            break
        if current == ground:
            # Native dig() returns None; resource observations measure its effect.
            dig()
            continue
        found = False
        for direction in directions:
            if get_ground_type(direction) == ground:
                if not move(direction):
                    return False
                found = True
                break
        if found:
            continue
        if (
            prospect == Items.Coal
            and num_unlocked(Unlocks.Prospecting) > 0
            and num_items(Items.Coal) > 0
        ):
            direction = prospect_iron()
            if direction != None:
                if not move(direction):
                    return False
                continue
        elif (
            prospect == Items.Iron
            and num_items(Items.Iron) >= QUARTZ_PROBE_COST
            and (current == Grounds.Rock or get_pos_z() < -48)
        ):
            distance = prospect_quartz()
            if distance != None:
                for direction, reverse in [(East, West), (North, South)]:
                    if num_items(Items.Iron) < QUARTZ_PROBE_COST:
                        break
                    if not move(direction):
                        return False
                    candidate = prospect_quartz()
                    if candidate != None and candidate < distance:
                        found = True
                        break
                    if not move(reverse):
                        return False
                    if num_items(Items.Iron) < QUARTZ_PROBE_COST:
                        break
                    if not move(reverse):
                        return False
                    candidate = prospect_quartz()
                    if candidate != None and candidate < distance:
                        found = True
                        break
                    if not move(direction):
                        return False
                if found:
                    continue
        dig()
    return True


def farm_ore(ground, item, qty, prospect=None, parallel=False):
    stalled = 0
    while num_items(item) < qty:
        before = num_items(item)
        if not produce_ore(ground, item, qty, prospect, parallel):
            return False
        if num_items(item) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Ore search made no progress", item, qty)
                return False
        else:
            stalled = 0
    return True
