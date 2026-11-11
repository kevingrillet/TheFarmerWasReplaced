# Grouped mining worlds: all workers share a coordinator-owned layer height.
import farm_mushroom
import mine_dynamite
import resource_manager
import utils_farm
import utils_mine
import ZZAchievementDLC

LAYERS_PER_WORLD = 256
RICE_FIELDS_PER_WORLD = 4
PYRAMIDS_PER_WORLD = 8


def _fund(item, target):
    return resource_manager.farm(
        item,
        target,
        num_unlocked(Unlocks.Megafarm) > 0,
        num_unlocked(Unlocks.Polyculture) > 0,
        num_unlocked(Unlocks.Trees) > 0,
    )


def requirements():
    ws = get_world_size()
    needs = {}
    if num_unlocked(Unlocks.Rice) > 0:
        cost = get_cost(Entities.Rice)
        for item in cost:
            needs[item] = cost[item] * ws * ws * RICE_FIELDS_PER_WORLD
    if num_unlocked(Unlocks.Pyramid) > 0:
        width = ws - (1 - ws % 2)
        h = width // 2 + 1
        needs[Items.Block] = h * (4 * h * h - 1) // 3 * PYRAMIDS_PER_WORLD
    return needs


def _protected(skip_mushroom):
    grounds = []
    if num_unlocked(Unlocks.Rice) > 0:
        grounds.append(Grounds.Clay)
    if num_unlocked(Unlocks.Mushrooms) > 0 and not skip_mushroom:
        grounds.append(Grounds.Mushroom)
    if num_unlocked(Unlocks.Dynamite) > 0:
        grounds.append(Grounds.Dynamite)
    if num_unlocked(Unlocks.Pyramid) > 0:
        grounds.append(Grounds.Sand)
        grounds.append(Grounds.Limestone)
    if num_unlocked(Unlocks.Treasure_Map) > 0:
        grounds.append(Grounds.Basalt)
        grounds.append(Grounds.Treasure_Map)
    return grounds


def protected_grounds(skip_mushroom=False):
    return _protected(skip_mushroom)


def _rice_cells(cells):
    for x, y, z, ground in cells:
        if not utils_mine.go_to(x, y):
            return False
        if get_ground_type() != Grounds.Clay or get_pos_z() != z:
            continue
        if not plant(Entities.Rice):
            return False
        utils_farm.water()
        if not utils_farm.wait_ripe() or not harvest():
            return False
    return True


def _rice_batch(cells, parallel):
    count = 1
    if parallel:
        count = min(max_drones(), len(cells))
    if len(cells) == 0:
        return True
    groups = []
    for _ in range(count):
        groups.append([])
    for index in range(len(cells)):
        groups[index % count].append(cells[index])
    handles = []
    success = True
    for index in range(count):
        handle = None
        if index < count - 1:
            handle = spawn_drone(_rice_cells, groups[index])
        if handle == None:
            if not _rice_cells(groups[index]):
                success = False
                break
        else:
            handles.append(handle)
    joined = utils_farm.join_workers(handles)
    return success and joined


def process_discoveries(hits, level, parallel, rice_left, pyramids_left, ignored):
    # One parent handles current-world activities; no preparation or funding here.
    mushroom_handled = False
    rice = []
    for hit in hits:
        if hit[3] == Grounds.Clay:
            rice.append(hit)
    if len(rice) > rice_left:
        quick_print("Grouped mining: funded Rice budget exhausted")
        return True, True, rice_left, pyramids_left, mushroom_handled
    if not _rice_batch(rice, parallel):
        return False, False, rice_left, pyramids_left, mushroom_handled
    rice_left -= len(rice)
    done = set()
    for x, y, z, ground in hits:
        key = x, y, z, ground
        if ground == Grounds.Clay or key in ignored or ground in done:
            continue
        if not utils_mine.go_to(x, y):
            return False, False, rice_left, pyramids_left, mushroom_handled
        if get_pos_z() != z or get_ground_type() != ground:
            continue  # A completed structure may invalidate other hits.
        if ground == Grounds.Mushroom:
            if not farm_mushroom.collect_current_layer(10**30, parallel):
                return False, False, rice_left, pyramids_left, mushroom_handled
            mushroom_handled = True
            # Blast worlds can expose several different Mushroom heights at once.
            ignored.add((-1, -1, z, Grounds.Mushroom))
            done.add(ground)
        elif ground == Grounds.Dynamite:
            outcome = mine_dynamite.solve_current_puzzle(parallel)
            if outcome == "blocked":
                return False, False, rice_left, pyramids_left, mushroom_handled
            quick_print("Grouped mining Dynamite puzzle", outcome)
            done.add(ground)
        elif ground == Grounds.Sand or ground == Grounds.Limestone:
            if pyramids_left == 0:
                quick_print("Grouped mining: funded pyramid budget exhausted")
                return True, True, rice_left, pyramids_left, mushroom_handled
            outcome, base = ZZAchievementDLC.collect_current_pyramid()
            if not outcome or base == None:
                quick_print("Grouped mining: pyramid could not be restored")
                return False, False, rice_left, pyramids_left, mushroom_handled
            bx, by, width, bz = base
            for px in range(bx, bx + width):
                for py in range(by, by + width):
                    ignored.add((px, py, bz, Grounds.Limestone))
            pyramids_left -= 1
        elif ground == Grounds.Basalt or ground == Grounds.Treasure_Map:
            outcome = ZZAchievementDLC.collect_current_treasure()
            if outcome != None and not outcome:
                quick_print("Grouped mining: treasure route failed")
                return False, False, rice_left, pyramids_left, mushroom_handled
            quick_print("Grouped mining treasure", outcome, "resuming layer", level)
            # All Basalt at this height points to the same map. Retire
            # the whole observed stratum, not only the first visited tile.
            basalt_z = z
            if ground == Grounds.Treasure_Map:
                basalt_z += 1
            for landmark in hits:
                if (landmark[3] == Grounds.Basalt and landmark[2] == basalt_z) or (
                    landmark[3] == Grounds.Treasure_Map and landmark[2] == basalt_z - 1
                ):
                    ignored.add(landmark)
    return True, False, rice_left, pyramids_left, mushroom_handled


def produce_world(max_layers=LAYERS_PER_WORLD):
    if max_layers < 1 or num_unlocked(Unlocks.Underground_Senses) == 0:
        return False
    if not utils_farm.can_start_phase():
        return False
    # Funding can reset worlds: it is complete before this world is prepared.
    needs = requirements()
    for item in needs:
        if not _fund(item, needs[item]):
            return False
    if not utils_mine.prepare():
        return False
    parallel = num_unlocked(Unlocks.Megafarm) > 0
    ws = get_world_size()
    rice_left = ws * ws * RICE_FIELDS_PER_WORLD
    pyramids_left = PYRAMIDS_PER_WORLD
    level = get_pos_z()
    start_level = level
    skipped_mushroom = False
    ignored = set()
    quick_print("Grouped mining world", max_layers, "layers")
    for _ in range(max_layers + 1):
        finished = False
        for attempt in range(ws * ws + 8):
            result, hits, active, kinds, stability = utils_mine.excavate_band(
                level, _protected(skipped_mushroom), parallel, False, ignored
            )
            if not result:
                return False
            if Grounds.Mushroom not in kinds:
                skipped_mushroom = False
            if len(hits) == 0:
                finished = True
                break
            success, end_world, rice_left, pyramids_left, handled = process_discoveries(
                hits, level, parallel, rice_left, pyramids_left, ignored
            )
            skipped_mushroom = skipped_mushroom or handled
            if not success:
                return False
            if end_world:
                return True
        if not finished:
            quick_print("Grouped mining: special layer did not finish", level)
            return False
        if not active:
            return True
        remaining = max_layers - (start_level - level)
        if remaining <= 0:
            return True
        # Discard foundation/map markers after all columns passed their height.
        keep = set()
        for key in ignored:
            if key[2] <= level:
                keep.add(key)
        ignored = keep
        step = 1
        if stability >= 2:
            step = 2
        level -= min(step, remaining)
    return True


def run(max_layers=LAYERS_PER_WORLD):
    while True:
        if num_unlocked(Unlocks.Sunflowers) > 0 and not _fund(Items.Power, 10000):
            return False
        if not produce_world(max_layers):
            return False
        # Bamboo is cultivated, not a natural underground block. Grow it between
        # completed mining worlds, with Rice funded by the normal manager.
        if num_unlocked(Unlocks.Bamboo) > 0:
            ws = get_world_size()
            yield_min = 64 * 2 ** (num_unlocked(Unlocks.Bamboo) - 1)
            target = num_items(Items.Bamboo) + yield_min * (ws // 2) * ws
            if not _fund(Items.Bamboo, target):
                return False


if __name__ == "__main__":
    run()
