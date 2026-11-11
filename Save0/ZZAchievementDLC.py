# Run on the real save: simulations and leaderboards do not award these feats.
# Edit the two lists below; see docs/guides/achievements.md for native conditions.
import resource_manager
import utils_farm
import utils_mine

# Manual Steam snapshot on 2026-11-10. No automatic filtering.
# Completed tasks stay commented so they can be enabled for another save.
SPECIFIC_TASKS = [
    # "broken_hoe",  # + Unsafe Code
    # "explosive_drill",
    # "rice_terrace",
    # "skyscraper",
    # "pyramid",
    # "colorful_pyramid",
    # "great_pyramid",
    # "treasure_map",  # + Treasure Map Master
    # "matchmaker",
    "long_distance_friendship",
    # "dynamite_specialist",
    # "deep_mining",
]

# Repeated actions, cumulative counters and the specialized speed challenge.
# Ordinary resource collection/grind belongs to story_mining/story_infinite.
GRIND_TASKS = [
    # "builder",
    "big_builder",  # 10,000 placed blocks.
    # "picasso",
    # "prospector",
    # "miner_master",
    # "relentless_miner",
    "egyptologist",
    "big_treasure",
]

TASKS = SPECIFIC_TASKS + GRIND_TASKS
_jump_used = False


def _fund(item, stock):
    return resource_manager.farm(
        item,
        stock,
        num_unlocked(Unlocks.Megafarm) > 0,
        num_unlocked(Unlocks.Polyculture) > 0,
        num_unlocked(Unlocks.Trees) > 0,
    )


def _prepare(skill, size=None):
    global _jump_used
    if num_unlocked(skill) == 0 or not utils_farm.can_start_phase():
        return False
    if size != None and num_unlocked(Unlocks.Debug_2) == 0:
        return False
    change_hat(Hats.Straw_Hat)
    clear()
    if size != None:
        set_world_size(size)
        if get_world_size() != size:
            return False
    # clear() does not renew jump's once-per-program allowance.
    if num_unlocked(Unlocks.Jump) > 0 and not _jump_used:
        if skill != Unlocks.Mining:
            jump(skill)
            _jump_used = True
    return True


def _dig_once():
    if get_ground_type() == Grounds.Bedrock:
        return False
    before = get_pos_z()
    dig()
    return get_pos_z() < before


def _seek(ground, limit=2048):
    for _ in range(limit):
        if get_ground_type() == ground:
            return True
        if not _dig_once():
            return False
    return get_ground_type() == ground


def _dig_to(z, limit=2048, exact=True):
    for _ in range(limit):
        if get_pos_z() <= z:
            return not exact or get_pos_z() == z
        if not _dig_once():
            return False
    return get_pos_z() <= z and (not exact or get_pos_z() == z)


def broken_hoe_unsafe():
    if not _prepare(Unlocks.Mining) or not _seek(Grounds.Rock):
        return False
    till()  # This refusal is the Broken Hoe condition, not an error.
    change_hat(Hats.Brown_Hat)  # Explicit hat: default Straw auto-equips Mining.
    result = _dig_once()
    change_hat(Hats.Straw_Hat)
    return result


def explosive_drill():
    if num_unlocked(Unlocks.Explosive_Drill) == 0:
        return False
    if not _fund(Items.Dynamite, 1) or not _prepare(Unlocks.Mining):
        return False
    change_hat(Hats.Explosive_Drill)
    before = num_items(Items.Dynamite)
    dug = _dig_once()
    change_hat(Hats.Straw_Hat)
    return dug and num_items(Items.Dynamite) < before


def miner_master(seconds=60, reserve=4096, target=1000000, max_digs=100000):
    # A measured attempt, never a claim that spending Dynamite awards the feat.
    if seconds <= 0 or seconds > 60 or reserve < 1 or target < 1 or max_digs < 1:
        return False
    if num_unlocked(Unlocks.Explosive_Drill) == 0 or num_unlocked(Unlocks.Timing) == 0:
        return False
    if not _fund(Items.Dynamite, reserve) or not _prepare(Unlocks.Mining):
        return False
    before, fuel = num_items(Items.Block), num_items(Items.Dynamite)
    start = get_time()
    change_hat(Hats.Explosive_Drill)
    success = False
    for _ in range(max_digs):
        if get_time() - start >= seconds or num_items(Items.Dynamite) == 0:
            break
        if not _dig_once():
            break
        elapsed = get_time() - start
        if num_items(Items.Block) - before >= target and elapsed <= seconds:
            success = True
            break
    change_hat(Hats.Straw_Hat)
    quick_print(
        "Miner Master measured",
        num_items(Items.Block) - before,
        "Block in",
        get_time() - start,
        "seconds; Dynamite",
        fuel - num_items(Items.Dynamite),
    )
    return success


def rice_terrace():
    if not _prepare(Unlocks.Rice, 3):
        return False
    # Do not harvest: even mature terraces must still contain their Rice entity.
    for x in range(3):
        for y in range(3):
            if not utils_mine.go_to(x, y) or not _seek(Grounds.Clay):
                return False
            if not plant(Entities.Rice):
                return False
    return True


def builder(count=1000, colored=False):
    if count < 1 or (colored and num_unlocked(Unlocks.Debug_Place) == 0):
        return False
    if not _fund(Items.Block, count) or not _prepare(Unlocks.Mining):
        return False
    for _ in range(count):
        ground = Grounds.Dirt
        if colored:
            ground = Grounds.Block_Red
        z = get_pos_z()
        if not place(ground) or get_pos_z() != z + 1:
            return False
        if not _dig_once() or get_pos_z() != z:
            return False
    return True


def skyscraper():
    if not _fund(Items.Block, 150 * 9) or not _prepare(Unlocks.Mining, 3):
        return False
    # Raise the entire small field in layers to respect the placement height cap.
    for height in range(1, 151):
        for x in range(3):
            for y in range(3):
                if not utils_mine.go_to(x, y) or not place(Grounds.Rock):
                    return False
                if get_pos_z() != height:
                    return False
    return True


def prospector(count=1000):
    if count < 1 or num_unlocked(Unlocks.Prospecting) == 0:
        return False
    if not _fund(Items.Coal, count) or not _prepare(Unlocks.Iron):
        return False
    for _ in range(count):
        before = num_items(Items.Coal)
        prospect_iron()  # None is valid; payment, not finding ore, counts.
        if num_items(Items.Coal) >= before:
            return False
    return True


def deep_mining(depth=10000):
    if depth < 1 or not _prepare(Unlocks.Mining):
        return False
    return _dig_to(-depth, depth + 1, False)


def relentless_miner(depth=1000, worlds=100):
    if depth < 1 or worlds < 1:
        return False
    for index in range(worlds):
        if not deep_mining(depth):
            return False
        quick_print("Accumulated depth this run", (index + 1) * depth)
    return True


def _treasure_route(instructions):
    # Erase closed loops in 3D; revisiting XY after digging is a different block.
    ws = get_world_size()
    position = (get_pos_x(), get_pos_y(), get_pos_z())
    positions, steps = [position], []
    indices = {position: 0}
    for letter in instructions:
        x, y, z = position
        if letter == "N":
            y = (y + 1) % ws
        elif letter == "E":
            x = (x + 1) % ws
        elif letter == "S":
            y = (y - 1) % ws
        elif letter == "W":
            x = (x - 1) % ws
        elif letter == "D":
            z -= 1
        else:
            return None
        position = x, y, z
        if position in indices:
            index = indices[position]
            while len(steps) > index:
                indices.pop(positions.pop())
                steps.pop()
        else:
            indices[position] = len(positions)
            positions.append(position)
            steps.append(letter)
    return steps


def collect_current_treasure():
    # One parent follows the map in this world; funding/reset belong to callers.
    if not utils_farm.can_start_phase():
        return False
    ground = get_ground_type()
    if ground == Grounds.Basalt:
        map_z = get_pos_z() - 1
        position = measure()
        if position == None:
            return None
        if not utils_mine.go_to(position[0], position[1]):
            return False
        # Native Basalt can still point at a map whose block was consumed.
        # Its map is exactly one layer below this stratum, never a deeper one.
        if get_pos_z() < map_z:
            return None
        if not _dig_to(map_z, max(2048, get_pos_z() - map_z + 1)):
            if get_pos_z() < map_z:
                return None
            return False
        if get_ground_type() != Grounds.Treasure_Map:
            return None
    elif ground != Grounds.Treasure_Map:
        return False
    instructions = measure()
    if instructions == None:
        return False
    instructions = _treasure_route(instructions)
    if instructions == None or len(instructions) == 0 or instructions[0] != "D":
        return False
    if not _dig_once():
        return False
    for step in range(1, len(instructions)):
        letter = instructions[step]
        if letter == "D":
            if not _dig_once():
                return False
        elif letter == "N":
            if not move(North):
                return False
        elif letter == "E":
            if not move(East):
                return False
        elif letter == "S":
            if not move(South):
                return False
        elif letter == "W":
            if not move(West):
                return False
        else:
            return False
    return get_entity_type() == Entities.Underground_Treasure and harvest()


def treasure_maps(count=1):
    if count < 1:
        return False
    for index in range(count):
        if not _prepare(Unlocks.Treasure_Map) or not _seek(Grounds.Basalt):
            return False
        if not collect_current_treasure():
            return False
        quick_print("Treasure maps harvested", index + 1)
    return True


def _find_pyramid(limit=256):
    if limit < 1:
        return False
    level = get_pos_z()
    start_level = level
    parallel = num_unlocked(Unlocks.Megafarm) > 0
    for _ in range(limit + 1):
        result, hits, active, kinds, stability = utils_mine.excavate_band(
            level, [Grounds.Sand, Grounds.Limestone], parallel, True
        )
        if not result:
            return False
        if len(hits) > 0:
            x, y, z, ground = hits[0]
            return utils_mine.go_to(x, y) and _seek(Grounds.Limestone, 32)
        if not active:
            break
        remaining = limit - (start_level - level)
        if remaining <= 0:
            break
        step = 1
        if stability >= 2:
            step = 2
        level -= min(step, remaining)
    return False


def _pyramid_base_single(preserve=False):
    z = get_pos_z()
    ws = get_world_size()
    pending = [(get_pos_x(), get_pos_y())]
    visited, base = set(), []
    while len(pending) > 0:
        x, y = pending.pop()
        if (x, y) in visited or x < 0 or y < 0 or x >= ws or y >= ws:
            continue
        visited.add((x, y))
        if not utils_mine.go_to(x, y):
            return None
        if get_pos_z() < z:
            continue
        if preserve:
            for _ in range(max(2048, get_pos_z() - z + 1)):
                if get_pos_z() <= z or get_ground_type() == Grounds.Sand:
                    break
                if not _dig_once():
                    return None
        elif not _dig_to(z, max(2048, get_pos_z() - z + 1)):
            return None
        if get_ground_type() != Grounds.Limestone and not (
            preserve and get_ground_type() == Grounds.Sand and get_pos_z() > z
        ):
            continue
        base.append((x, y))
        pending += [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    if len(base) == 0:
        return None
    x0, y0 = base[0]
    x1, y1 = x0, y0
    for x, y in base:
        x0, y0 = min(x0, x), min(y0, y)
        x1, y1 = max(x1, x), max(y1, y)
    width = x1 - x0 + 1
    if width < 5 or width % 2 == 0 or y1 - y0 + 1 != width:
        return None
    if len(base) != width * width:
        return None
    return x0, y0, width, z


def _pyramid_probe(x, y, z, preserve):
    if not utils_mine.go_to(x, y):
        return False, False
    for _ in range(max(2048, get_pos_z() - z + 1)):
        current = get_pos_z()
        ground = get_ground_type()
        if current <= z or ground == Grounds.Limestone or ground == Grounds.Bedrock:
            break
        if preserve and ground == Grounds.Sand:
            break
        if not _dig_once():
            return False, False
    current = get_pos_z()
    ground = get_ground_type()
    if (
        current > z
        and ground not in [Grounds.Limestone, Grounds.Bedrock]
        and not (preserve and ground == Grounds.Sand)
    ):
        return False, False
    inside = current == z and ground == Grounds.Limestone
    if preserve and current > z and ground == Grounds.Sand:
        inside = True
    return True, inside


def _pyramid_ray(origin, z, preserve, dx, dy):
    x, y = origin
    last = origin
    ws = get_world_size()
    for _ in range(ws):
        x, y = x + dx, y + dy
        if x < 0 or y < 0 or x >= ws or y >= ws:
            break
        success, inside = _pyramid_probe(x, y, z, preserve)
        if not success:
            return False, last
        if not inside:
            break
        last = x, y
    return True, last


def _clear_pyramid_rows(base, preserve, x0, x1):
    bx, by, width, z = base
    for row in range(x1 - x0):
        for offset in range(width):
            y = by + offset
            if row % 2 == 1:
                y = by + width - 1 - offset
            success, inside = _pyramid_probe(x0 + row, y, z, preserve)
            if not success or not inside:
                return False
    return True


def _pyramid_base(preserve=False, parallel=None):
    if parallel == None:
        parallel = num_unlocked(Unlocks.Megafarm) > 0
    if not parallel or num_unlocked(Unlocks.Megafarm) == 0 or max_drones() < 2:
        return _pyramid_base_single(preserve)
    if not utils_farm.can_start_phase():
        return None
    origin = get_pos_x(), get_pos_y()
    z = get_pos_z()
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    handles, results = [], []
    for index in range(4):
        dx, dy = directions[index]
        handle = None
        if index < 3:
            handle = spawn_drone(_pyramid_ray, origin, z, preserve, dx, dy)
        if handle == None:
            results.append(_pyramid_ray(origin, z, preserve, dx, dy))
        else:
            handles.append(handle)
    for handle in handles:
        results.append(wait_for(handle))
    x0, y0 = origin
    x1, y1 = origin
    for success, position in results:
        if not success:
            return None
        x, y = position
        x0, y0 = min(x0, x), min(y0, y)
        x1, y1 = max(x1, x), max(y1, y)
    width = x1 - x0 + 1
    if width < 5 or width % 2 == 0 or y1 - y0 + 1 != width:
        return None
    base = x0, y0, width, z
    count = min(width, max_drones())
    handles = []
    success = True
    for index in range(count):
        start = x0 + index * width // count
        end = x0 + (index + 1) * width // count
        handle = None
        if index < count - 1:
            handle = spawn_drone(_clear_pyramid_rows, base, preserve, start, end)
        if handle == None:
            if not _clear_pyramid_rows(base, preserve, start, end):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    if not success or not joined:
        return None
    return base


def _restore_pyramid_single(base, colored):
    x0, y0, width, z = base
    for layer in range(width // 2 + 1):
        for x in range(x0 + layer, x0 + width - layer):
            for y in range(y0 + layer, y0 + width - layer):
                if not utils_mine.go_to(x, y):
                    return False
                if not colored and get_pos_z() > z + layer:
                    # Existing sand above this layer already supplies its support.
                    if get_ground_type() != Grounds.Sand:
                        return False
                    continue
                if get_pos_z() != z + layer:
                    return False
                ground = Grounds.Sand
                if colored:
                    ground = Grounds.Block_Red
                if not place(ground):
                    return False
                if get_pos_z() != z + layer + 1:
                    # Completing an existing ruin can remove all sand before
                    # the loop reaches its last geometric cell.
                    if not utils_mine.go_to(x0 + width // 2, y0 + width // 2):
                        return False
                    return get_entity_type() == Entities.Sunflower and harvest()
    if not utils_mine.go_to(x0 + width // 2, y0 + width // 2):
        return False
    return get_entity_type() == Entities.Sunflower and harvest()


def _pyramid_rows(base, layer, x0, x1, colored):
    bx, by, width, z = base
    side = width - 2 * layer
    level = z + layer
    if not utils_mine.go_to(x0, by + layer):
        return False
    ground = Grounds.Sand
    if colored:
        ground = Grounds.Block_Red
    for row in range(x1 - x0):
        direction = North
        if row % 2 == 1:
            direction = South
        for column in range(side):
            current = get_pos_z()
            if not colored and current > level:
                if get_ground_type() != Grounds.Sand:
                    return False
            else:
                if current != level or not place(ground):
                    return False
                if get_pos_z() != level + 1:
                    return False
            if column < side - 1 and not move(direction):
                return False
        if row < x1 - x0 - 1 and not move(East):
            return False
    return True


def _pyramid_layer(base, layer, colored):
    bx, by, width, z = base
    side = width - 2 * layer
    count = min(side, max_drones())
    handles = []
    success = True
    for index in range(count):
        x0 = bx + layer + index * side // count
        x1 = bx + layer + (index + 1) * side // count
        handle = None
        if index < count - 1:
            handle = spawn_drone(_pyramid_rows, base, layer, x0, x1, colored)
        if handle == None:
            if not _pyramid_rows(base, layer, x0, x1, colored):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    return success and joined


def _restore_pyramid(base, colored, parallel=None):
    if parallel == None:
        parallel = num_unlocked(Unlocks.Megafarm) > 0
    if not parallel or num_unlocked(Unlocks.Megafarm) == 0 or max_drones() < 2:
        return _restore_pyramid_single(base, colored)
    if not utils_farm.can_start_phase():
        return False
    bx, by, width, z = base
    height = width // 2 + 1
    cx, cy = bx + width // 2, by + width // 2
    if not utils_mine.go_to(cx, cy):
        return False
    if get_entity_type() == Entities.Sunflower:
        return harvest()
    top = get_pos_z()
    if top < z or top > z + height:
        return False
    if top == z + height:
        # Withhold the apex: native completion removes the entire pyramid.
        # Otherwise one worker could finish while others still place blocks.
        if colored or get_ground_type() != Grounds.Sand or not _dig_once():
            return False
        if get_pos_z() != z + height - 1:
            return False
    for layer in range(height - 1):
        if not _pyramid_layer(base, layer, colored):
            return False
    # All children have joined. Only the parent closes and harvests the pyramid.
    if not utils_mine.go_to(cx, cy) or get_pos_z() != z + height - 1:
        return False
    ground = Grounds.Sand
    if colored:
        ground = Grounds.Block_Red
    if not place(ground):
        return False
    return get_entity_type() == Entities.Sunflower and harvest()


def collect_current_pyramid(colored=False, min_width=5, parallel=None):
    # The caller owns funding and the world; do not prepare, jump or clear here.
    if not utils_farm.can_start_phase():
        return False, None
    change_hat(Hats.Straw_Hat)
    if not _seek(Grounds.Limestone, 32):
        return False, None
    base = _pyramid_base(not colored, parallel)
    if base == None or base[2] < min_width:
        return False, base
    return _restore_pyramid(base, colored, parallel), base


def pyramids(count=1, colored=False, min_width=5, attempts=40, size=None):
    if count < 1 or num_unlocked(Unlocks.Pyramid) == 0:
        return False
    if colored and num_unlocked(Unlocks.Debug_Place) == 0:
        return False
    available = get_world_size()
    if size != None:
        available = size
    if available < max(6, min_width):
        return False
    width = available - (1 - available % 2)
    h = width // 2 + 1
    reserve = h * (4 * h * h - 1) // 3
    completed = 0
    for _ in range(max(count, attempts)):
        if not _fund(Items.Block, reserve) or not _prepare(Unlocks.Pyramid, size):
            return False
        if get_world_size() < max(6, min_width):
            quick_print("Pyramid needs a larger field", min_width)
            return False
        if not _find_pyramid():
            continue
        result, base = collect_current_pyramid(colored, min_width)
        if base == None or base[2] < min_width:
            continue
        if not result:
            return False
        completed += 1
        quick_print("Pyramids harvested", completed, "width", base[2])
        if completed >= count:
            return True
    return False


def dynamite_specialist(attempts=10):
    import mine_dynamite

    if attempts < 1:
        return False
    for _ in range(attempts):
        if not _prepare(Unlocks.Dynamite, 32):
            return False
        if not _dig_to(-600, 2048, False):
            return False
        # A stock goal must never terminate this puzzle before all duds are dug.
        result = mine_dynamite._puzzle_single(num_items(Items.Dynamite) + 10**30)
        if result == "blocked":
            return False
        if result:
            return True
    return False


def _mushroom_surface(bottom):
    kind = None
    if get_pos_z() > bottom and get_ground_type() == Grounds.Mushroom:
        kind = measure()
    return get_pos_z(), kind


def matchmaker(max_moves=20000, size=16):
    if max_moves < 1 or size < 8 or not _prepare(Unlocks.Mushrooms, size):
        return False
    if not _seek(Grounds.Mushroom):
        return False
    top = get_pos_z()
    height = 0
    # One sacrificial column measures the stratum; all other blocks are pushed.
    while get_ground_type() == Grounds.Mushroom and height < 16:
        z = get_pos_z()
        if not _dig_once():
            return False
        if get_pos_z() != z - 1:
            return False
        height += 1
    if height == 0 or get_ground_type() == Grounds.Mushroom:
        return False
    surface = {}
    bottom = top - height
    for x in range(size):
        for y in range(size):
            if not utils_mine.go_to(x, y):
                return False
            if get_pos_z() > top and not _dig_to(top):
                return False
            surface[(x, y)] = _mushroom_surface(bottom)
    before = num_items(Items.Mushroom)
    pair_yield = 2 ** (num_unlocked(Unlocks.Mushrooms) - 1)
    previous = None
    calm = 0
    goal = before + (95 * size * size * height // 200 + 1) * pair_yield
    for index in range(max_moves):
        matched = 2 * (num_items(Items.Mushroom) - before) / pair_yield
        # Installed controller requires strictly more than 95%, not >= 95%.
        if 100 * matched > 95 * size * size * height:
            return True
        chosen, choices, found_match = None, 0, False
        for x, y in surface:
            z, kind = surface[(x, y)]
            if kind == None:
                continue
            for dx, dy, direction in [
                (1, 0, East),
                (-1, 0, West),
                (0, 1, North),
                (0, -1, South),
            ]:
                target = ((x + dx) % size, (y + dy) % size)
                tz, other = surface[target]
                if tz >= z or previous == (target, (x, y)):
                    continue
                if kind == other:
                    chosen = (x, y), target, direction
                    found_match = True
                    break
                choices += 1
                if chosen == None or random() < 1 / choices:
                    chosen = (x, y), target, direction
            if found_match:
                break
        if chosen == None or calm >= size * size or index >= max_moves // 2:
            _compact_mushrooms(surface, bottom, goal, max_moves - index, size)
            break
        source, target, direction = chosen
        if not utils_mine.go_to(source[0], source[1]) or not push(direction):
            return False
        surface[source] = _mushroom_surface(bottom)
        if not move(direction):
            return False
        surface[target] = _mushroom_surface(bottom)
        previous = source, target
        if found_match:
            calm = 0
        else:
            calm += 1
    if num_items(Items.Mushroom) >= goal:
        return True
    quick_print("Matchmaker incomplete; retry on a new stratum")
    return False


def _mushroom_path(surface, source, target, size):
    # Route only through empty columns. A carried block cannot climb a step.
    queue, seen = [source], {source: None}
    cursor = 0
    while cursor < len(queue):
        pos = queue[cursor]
        cursor += 1
        z = surface[pos][0]
        if pos != source:
            z += 1
        for dx, dy, direction in [
            (1, 0, East),
            (-1, 0, West),
            (0, 1, North),
            (0, -1, South),
        ]:
            nxt = ((pos[0] + dx) % size, (pos[1] + dy) % size)
            if nxt in seen or surface[nxt][0] >= z:
                continue
            if nxt != target and surface[nxt][1] != None:
                continue
            seen[nxt] = (pos, direction)
            if nxt == target:
                path = []
                while nxt != source:
                    prev, step = seen[nxt]
                    path.append(step)
                    nxt = prev
                return path
            queue.append(nxt)
    return None


def _compact_mushrooms(surface, bottom, goal, budget, size):
    blocked = set()
    collector = None
    used = 0
    for _ in range(size * size * 16):
        if num_items(Items.Mushroom) >= goal:
            return True
        if used >= budget:
            break
        if collector == None:
            for pos in surface:
                z, kind = surface[pos]
                if kind != None or pos in blocked or z < bottom - 1:
                    continue
                safe = True
                floor = bottom - 1
                # Do not collapse a high surviving part of the colony.
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        near = pos[0] + dx, pos[1] + dy
                        if near in surface and surface[near][0] > floor + 3:
                            safe = False
                if safe:
                    collector = pos
                    if not utils_mine.go_to(pos[0], pos[1]) or not _dig_to(floor):
                        return False
                    if get_ground_type() == Grounds.Mushroom:
                        return False  # Never mix a different natural stratum.
                    surface[pos] = get_pos_z(), None
                    break
            if collector == None:
                break
        kind = surface[collector][1]
        chosen, route = None, None
        for source in surface:
            other = surface[source][1]
            if source == collector or other == None or (kind != None and other != kind):
                continue
            if kind == None:
                count = 0
                for pos in surface:
                    if surface[pos][1] == other:
                        count += 1
                if count < 2:
                    continue
            path = _mushroom_path(surface, source, collector, size)
            if path != None and used + len(path) <= budget:
                chosen, route = source, path
                break
        if chosen == None:
            blocked.add(collector)
            collector = None
            continue
        if not utils_mine.go_to(chosen[0], chosen[1]):
            return False
        for index in range(len(route) - 1, -1, -1):
            if not push(route[index]):
                return False
            used += 1
            kind = None
            if get_ground_type() == Grounds.Mushroom:
                kind = measure()
            surface[chosen] = get_pos_z(), kind
            if not move(route[index]):
                return False
            chosen = get_pos_x(), get_pos_y()
            kind = None
            if get_ground_type() == Grounds.Mushroom:
                kind = measure()
            surface[chosen] = get_pos_z(), kind
    return num_items(Items.Mushroom) >= goal


def long_distance_friendship(limit=2048):
    if limit < 1 or get_world_size() < 4 or not _prepare(Unlocks.Mushrooms):
        return False
    if not utils_mine.go_to(0, 0) or not _seek(Grounds.Mushroom):
        return False
    original_z, kind = get_pos_z(), measure()
    source_x, target_x = 0, get_world_size() - 1
    gap = False
    used = 0
    # Carry the original mushroom between opposite edges as both wells descend.
    # A permanent shallow source can cave in long before a second colony appears.
    while used < limit:
        if not utils_mine.go_to(source_x, 0):
            return False
        source_z = get_pos_z()
        if get_ground_type() != Grounds.Mushroom or measure() != kind:
            quick_print("Long Distance Friendship: carried source was lost")
            return False
        if not utils_mine.go_to(target_x, 0):
            return False
        while get_pos_z() > source_z - 2:
            ground = get_ground_type()
            if ground != Grounds.Mushroom and get_pos_z() < original_z:
                gap = True
            if gap and ground == Grounds.Mushroom and get_pos_z() < source_z and measure() == kind:
                break
            if used >= limit or not _dig_once():
                return False
            used += 1
        ground = get_ground_type()
        if ground != Grounds.Mushroom and get_pos_z() < original_z:
            gap = True
        matching = ground == Grounds.Mushroom and measure() == kind
        if matching and not gap:
            # Do not consume the source by matching within its original colony.
            # Native generation has no equal consecutive vertical types.
            if used >= limit or not _dig_once():
                return False
            used += 1
            ground = get_ground_type()
            if ground != Grounds.Mushroom and get_pos_z() < original_z:
                gap = True
            if ground == Grounds.Mushroom and measure() == kind:
                return False
            matching = False
        if not utils_mine.go_to(source_x, 0):
            return False
        if get_pos_z() != source_z or get_ground_type() != Grounds.Mushroom or measure() != kind:
            quick_print("Long Distance Friendship: source collapsed during excavation")
            return False
        direction = West
        if source_x != 0:
            direction = East
        before = num_items(Items.Mushroom)
        if not can_push(direction) or not push(direction):
            return False
        if matching and gap:
            return num_items(Items.Mushroom) > before
        if num_items(Items.Mushroom) > before:
            return False
        source_x, target_x = target_x, source_x
        if not utils_mine.go_to(source_x, 0) or get_pos_z() >= source_z:
            return False
    quick_print("Long Distance Friendship: search budget exhausted", used)
    return False


def _restore_size(size):
    if get_world_size() == size:
        return True
    if num_unlocked(Unlocks.Debug_2) == 0 or not utils_farm.can_start_phase():
        return False
    set_world_size(size)
    return get_world_size() == size


def run_tasks(tasks=None):
    if tasks == None:
        tasks = TASKS
    if len(tasks) == 0:
        return True
    size = get_world_size()
    completed, failed, seen = [], [], set()
    for task in tasks:
        if task in seen:
            continue
        seen.add(task)
        if not utils_farm.can_start_phase() or not _restore_size(size):
            quick_print("DLC achievement sequence stopped: workers or field size")
            return False
        result = run(task)
        if result:
            completed.append(task)
        else:
            failed.append(task)
        quick_print("DLC task actions result", task, result)
    restored = utils_farm.can_start_phase() and _restore_size(size)
    quick_print("DLC task actions completed", completed)
    quick_print("DLC tasks to review or retry", failed)
    # Successful actions are not a claim that Steam awarded the achievement.
    return restored and len(failed) == 0


def run(task=None):
    if task == None:
        return run_tasks()
    quick_print("DLC achievement task", task)
    if task == "broken_hoe":
        return broken_hoe_unsafe()
    if task == "explosive_drill":
        return explosive_drill()
    if task == "rice_terrace":
        return rice_terrace()
    if task == "builder":
        return builder()
    if task == "big_builder":
        return builder(10000)
    if task == "picasso":
        return builder(1000, True)
    if task == "skyscraper":
        return skyscraper()
    if task == "prospector":
        return prospector()
    if task == "miner_master":
        return miner_master()
    if task == "deep_mining":
        return deep_mining()
    if task == "relentless_miner":
        return relentless_miner()
    if task == "treasure_map":
        return treasure_maps()
    if task == "big_treasure":
        return treasure_maps(200)
    if task == "pyramid":
        return pyramids()
    if task == "egyptologist":
        return pyramids(200, False, 5, 600, 8)
    if task == "great_pyramid":
        return pyramids(1, False, 29)
    if task == "colorful_pyramid":
        return pyramids(1, True)
    if task == "matchmaker":
        return matchmaker()
    if task == "long_distance_friendship":
        return long_distance_friendship()
    if task == "dynamite_specialist":
        return dynamite_specialist()
    quick_print("Unknown DLC achievement task", task)
    return False


if __name__ == "__main__":
    quick_print("DLC achievement sequence result", run_tasks())
