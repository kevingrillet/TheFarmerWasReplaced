# Deep shaft exploration. Blasts can destroy buried or nearby activities.
import farm_mushroom
import mine_dynamite
import resource_manager
import utils_farm
import utils_mine
import ZZAchievementDLC

ACTIVITIES = [
    "treasure",
    "pyramid",
    "minesweeper",
    # "mushroom",
]
TARGET_DEPTH = None  # None: keep descending. 10000: stop at z <= -10000.
START_NEW_WORLD = False  # False: continue this world without funding or clear.
DYNAMITE_RESERVE = 10000  # Startup stock for an explicitly requested new world.
POWER_RESERVE = 10000
LOG_DEPTH_INTERVAL = 1000


def _pyramid_reserve():
    ws = get_world_size()
    width = ws - (1 - ws % 2)
    h = width // 2 + 1
    return h * (4 * h * h - 1) // 3


def requirements(activities=None):
    if activities == None:
        activities = ACTIVITIES
    needs = {Items.Dynamite: DYNAMITE_RESERVE}
    if num_unlocked(Unlocks.Sunflowers) > 0:
        needs[Items.Power] = POWER_RESERVE
    if "pyramid" in activities and num_unlocked(Unlocks.Pyramid) > 0:
        needs[Items.Block] = _pyramid_reserve()
    return needs


def _protected(activities):
    grounds = []
    for activity in activities:
        if activity == "treasure":
            if num_unlocked(Unlocks.Treasure_Map) > 0:
                grounds += [Grounds.Basalt, Grounds.Treasure_Map]
        elif activity == "pyramid":
            if num_unlocked(Unlocks.Pyramid) > 0:
                grounds += [Grounds.Sand, Grounds.Limestone]
        elif activity == "minesweeper":
            if num_unlocked(Unlocks.Dynamite) > 0:
                grounds.append(Grounds.Dynamite)
        elif activity == "mushroom":
            if num_unlocked(Unlocks.Mushrooms) > 0:
                grounds.append(Grounds.Mushroom)
        else:
            return None
    return grounds


def _blast():
    # Only the parent wears this unique hat, with no activity worker alive.
    if not utils_farm.can_start_phase() or num_items(Items.Dynamite) < 1:
        return False
    before = get_pos_z()
    change_hat(Hats.Explosive_Drill)
    dig()
    change_hat(Hats.Straw_Hat)
    return get_pos_z() < before


def _ignored(hit, ignored):
    return hit in ignored or (-1, -1, hit[2], hit[3]) in ignored


def _discover(protected, ignored):
    hit = get_pos_x(), get_pos_y(), get_pos_z(), get_ground_type()
    if hit[3] in protected and not _ignored(hit, ignored):
        return True, hit
    # Read the four exposed neighbors, without sweeping ordinary field cells.
    for direction, back in [(North, South), (East, West), (South, North), (West, East)]:
        if get_ground_type(direction) not in protected:
            continue
        if not move(direction):
            return False, None
        hit = get_pos_x(), get_pos_y(), get_pos_z(), get_ground_type()
        if not _ignored(hit, ignored):
            return True, hit
        if not move(back):
            return False, None
    return True, None


def _activity(hit, parallel, ignored):
    x, y, z, ground = hit
    quick_print("Deep mining activity", ground, z)
    if ground == Grounds.Mushroom:
        if not farm_mushroom.collect_current_layer(10**30, parallel, True):
            return False
        ignored.add((-1, -1, z, Grounds.Mushroom))
    elif ground == Grounds.Dynamite:
        outcome = mine_dynamite.solve_current_puzzle(parallel)
        quick_print("Deep mining Minesweeper", outcome)
        if outcome == "blocked":
            return False
    elif ground == Grounds.Sand or ground == Grounds.Limestone:
        reserve = _pyramid_reserve()
        if num_items(Items.Block) < reserve:
            quick_print("Deep mining: insufficient Block reserve for pyramid", reserve)
            return False
        outcome, base = ZZAchievementDLC.collect_current_pyramid()
        if not outcome or base == None:
            return False
        bx, by, width, bz = base
        for px in range(bx, bx + width):
            for py in range(by, by + width):
                ignored.add((px, py, bz, Grounds.Limestone))
    else:
        outcome = ZZAchievementDLC.collect_current_treasure()
        if outcome != None and not outcome:
            return False
        basalt_z = z
        if ground == Grounds.Treasure_Map:
            basalt_z += 1
        ignored.add((-1, -1, basalt_z, Grounds.Basalt))
        ignored.add((-1, -1, basalt_z - 1, Grounds.Treasure_Map))
    return True


def protected_grounds(activities):
    return _protected(activities)


def discover(protected, ignored):
    return _discover(protected, ignored)


def collect_activity(hit, parallel, ignored):
    return _activity(hit, parallel, ignored)


def produce_world(
    target_depth=TARGET_DEPTH,
    max_blasts=None,
    activities=None,
    start_new_world=START_NEW_WORLD,
):
    if target_depth != None and (target_depth < 1 or target_depth % 1 != 0):
        return False
    if max_blasts != None and (max_blasts < 1 or max_blasts % 1 != 0):
        return False
    if LOG_DEPTH_INTERVAL < 1 or DYNAMITE_RESERVE < 0 or POWER_RESERVE < 0:
        return False
    if activities == None:
        activities = ACTIVITIES
    protected = _protected(activities)
    if (
        protected == None
        or num_unlocked(Unlocks.Explosive_Drill) == 0
        or num_unlocked(Unlocks.Underground_Senses) == 0
    ):
        return False
    if not utils_farm.can_start_phase():
        return False
    if start_new_world:
        needs = requirements(activities)
        for item in needs:
            if not resource_manager.farm_current(item, needs[item]):
                return False
        if not utils_mine.prepare():
            return False
    change_hat(Hats.Straw_Hat)
    parallel = num_unlocked(Unlocks.Megafarm) > 0
    ignored = set()
    shots = 0
    previous = None
    unchanged = 0
    ordinary = False
    next_log = (-get_pos_z() // LOG_DEPTH_INTERVAL + 1) * LOG_DEPTH_INTERVAL
    quick_print("Deep mining: continuing this world at", get_pos_z())
    while True:
        z = get_pos_z()
        if -z >= next_log:
            quick_print("Deep mining depth", z)
            next_log = (-z // LOG_DEPTH_INTERVAL + 1) * LOG_DEPTH_INTERVAL
        if target_depth != None and z <= -target_depth:
            return True
        if max_blasts != None and shots >= max_blasts:
            return True
        shaft = get_pos_x(), get_pos_y(), z
        success, hit = _discover(protected, ignored)
        if not success:
            return False
        if hit != None:
            if hit == previous:
                unchanged += 1
                if unchanged >= 4:
                    quick_print("Deep mining: activity made no progress", hit)
                    return False
            else:
                unchanged = 0
            previous = hit
            if not _activity(hit, parallel, ignored):
                quick_print("Deep mining: activity failed; world preserved", hit)
                return False
            # A collector may finish on a shallower tile. Keep the deeper shaft.
            if get_pos_z() > shaft[2] and not utils_mine.go_to(shaft[0], shaft[1]):
                return False
            continue
        previous = None
        unchanged = 0
        if get_ground_type() == Grounds.Bedrock:
            return True
        if num_items(Items.Dynamite) > 0:
            if not _blast():
                quick_print("Deep mining: explosive drill made no progress")
                return False
            shots += 1
        else:
            if not ordinary:
                quick_print(
                    "Deep mining: no Dynamite; continuing with the ordinary drill"
                )
                ordinary = True
            before = get_pos_z()
            dig()
            if get_pos_z() >= before:
                quick_print("Deep mining: ordinary drill made no progress")
                return False


def run(target_depth=TARGET_DEPTH, activities=None, start_new_world=START_NEW_WORLD):
    # Never renew the world or run a funding farm during the descent.
    return produce_world(target_depth, None, activities, start_new_world)


if __name__ == "__main__":
    run()
