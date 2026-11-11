# Cooperative ordinary drills in one shaft, with one owner per depth slot.
import resource_manager
import story_mining_infinite_explosive
import utils_farm
import utils_mine

ACTIVITIES = [
    "treasure",
    "pyramid",
    "minesweeper",
    # "mushroom",
]
TARGET_DEPTH = None
START_NEW_WORLD = False
BATCH_DEPTH = 256  # Pause/join at activities or after this many shaft levels.
DRONE_LIMIT = None  # None: use the available capacity; 1: serial comparison.
WORKER_TIMEOUT = 30  # Seconds without shaft progress before failing finitely.
LOG_DEPTH_INTERVAL = 1000


def requirements(activities=None):
    if activities == None:
        activities = ACTIVITIES
    needs = story_mining_infinite_explosive.requirements(activities)
    needs.pop(Items.Dynamite)
    return needs


def _nearby_activity(neighbors, protected, ignored):
    # The installed native get_pos_z(direction) reads neighbor height without
    # moving. The owning depth slot cannot advance while it checks these sites.
    for direction, x, y in neighbors:
        ground = get_ground_type(direction)
        if ground not in protected:
            continue
        z = get_pos_z(direction)
        if (x, y, z, ground) not in ignored and (-1, -1, z, ground) not in ignored:
            return True
    return False


def _drill_slots(owned, slots, start, floor, protected, ignored):
    x, y = get_pos_x(), get_pos_y()
    ws = get_world_size()
    neighbors = [
        (North, x, (y + 1) % ws),
        (East, (x + 1) % ws, y),
        (South, x, (y - 1) % ws),
        (West, (x - 1) % ws, y),
    ]
    last = None
    deadline = get_time() + WORKER_TIMEOUT
    while True:
        z = get_pos_z()
        if z <= floor:
            return True
        if z != last:
            ground = get_ground_type()
            if get_pos_z() != z:
                continue
            key = x, y, z, ground
            if ground == Grounds.Bedrock or (
                ground in protected
                and key not in ignored
                and (-1, -1, z, ground) not in ignored
            ):
                return True
            if len(protected) > 0:
                nearby = _nearby_activity(neighbors, protected, ignored)
                if get_pos_z() != z:
                    continue
                if nearby:
                    return True
            last = z
            deadline = get_time() + WORKER_TIMEOUT
        if (start - z) % slots in owned:
            # Only one actor owns this height. Others cannot advance the shaft
            # until this actor digs, so its checked ground cannot be stolen.
            if get_pos_z() != z:
                continue
            dig()
            if get_pos_z() >= z:
                return False
        elif get_time() >= deadline:
            return False


def _pipeline(floor, protected, ignored):
    if not utils_farm.can_start_phase():
        return False
    start = get_pos_z()
    slots = 1
    if num_unlocked(Unlocks.Megafarm) > 0:
        slots = max_drones()
    if DRONE_LIMIT != None:
        slots = min(slots, DRONE_LIMIT)
    slots = min(slots, start - floor)
    if slots < 1:
        return True
    owned = set()
    owned.add(slots - 1)
    handles = []
    for index in range(slots - 1):
        handle = spawn_drone(
            _drill_slots, {index}, slots, start, floor, protected, ignored
        )
        if handle == None:
            owned.add(index)
        else:
            handles.append(handle)
    # A refused spawn becomes a parent-owned slot; it never leaves a hole in
    # the turn order. The parent begins only after all spawn attempts.
    success = _drill_slots(owned, slots, start, floor, protected, ignored)
    joined = utils_farm.join_workers(handles)
    return success and joined


def produce_world(
    target_depth=TARGET_DEPTH,
    activities=None,
    start_new_world=START_NEW_WORLD,
    max_phases=None,
):
    if target_depth != None and (target_depth < 1 or target_depth % 1 != 0):
        return False
    if max_phases != None and (max_phases < 1 or max_phases % 1 != 0):
        return False
    if (
        BATCH_DEPTH < 1
        or BATCH_DEPTH % 1 != 0
        or WORKER_TIMEOUT <= 0
        or LOG_DEPTH_INTERVAL < 1
    ):
        return False
    if DRONE_LIMIT != None and (DRONE_LIMIT < 1 or DRONE_LIMIT % 1 != 0):
        return False
    if activities == None:
        activities = ACTIVITIES
    protected = story_mining_infinite_explosive.protected_grounds(activities)
    if (
        protected == None
        or num_unlocked(Unlocks.Underground_Senses) == 0
        or num_unlocked(Unlocks.Timing) == 0
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
    previous = None
    unchanged = 0
    phases = 0
    next_log = (-get_pos_z() // LOG_DEPTH_INTERVAL + 1) * LOG_DEPTH_INTERVAL
    quick_print("Fast mining: continuing this world at", get_pos_z())
    while True:
        z = get_pos_z()
        if -z >= next_log:
            quick_print("Fast mining depth", z)
            next_log = (-z // LOG_DEPTH_INTERVAL + 1) * LOG_DEPTH_INTERVAL
        if target_depth != None and z <= -target_depth:
            return True
        if max_phases != None and phases >= max_phases:
            return True
        shaft = get_pos_x(), get_pos_y(), z
        success, hit = story_mining_infinite_explosive.discover(protected, ignored)
        if not success:
            return False
        if hit != None:
            if hit == previous:
                unchanged += 1
                if unchanged >= 4:
                    quick_print("Fast mining: activity made no progress", hit)
                    return False
            else:
                unchanged = 0
            previous = hit
            if not story_mining_infinite_explosive.collect_activity(
                hit, parallel, ignored
            ):
                quick_print("Fast mining: activity failed; world preserved", hit)
                return False
            if get_pos_z() > shaft[2] and not utils_mine.go_to(shaft[0], shaft[1]):
                return False
            continue
        previous = None
        unchanged = 0
        if get_ground_type() == Grounds.Bedrock:
            return True
        floor = get_pos_z() - BATCH_DEPTH
        if target_depth != None:
            floor = max(floor, -target_depth)
        if not _pipeline(floor, protected, ignored):
            quick_print("Fast mining: cooperative drilling failed; world preserved")
            return False
        phases += 1


def run(target_depth=TARGET_DEPTH, activities=None, start_new_world=START_NEW_WORLD):
    return produce_world(target_depth, activities, start_new_world)


if __name__ == "__main__":
    run()
