import resource_manager
import utils_farm
import utils_math

MINING_MODE = "layers"  # layers / individual


def _mine_group(items, target):
    import story_mining_infinite

    stalled = {}
    for item in items:
        stalled[item] = 0
    while True:
        missing, before = [], {}
        for item in items:
            before[item] = num_items(item)
            if before[item] < target:
                missing.append(item)
        if len(missing) == 0:
            return True
        if not story_mining_infinite.produce_world():
            return False
        for item in missing:
            if num_items(item) > before[item]:
                stalled[item] = 0
            else:
                stalled[item] += 1
                if stalled[item] >= 8:
                    quick_print("Grouped mining made no progress", item, target)
                    return False


def default_items():
    items = [
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Bone,
        Items.Gold,
    ]
    for skill, item in [
        (Unlocks.Mining, Items.Block),
        (Unlocks.Coal, Items.Coal),
        (Unlocks.Rice, Items.Rice),
        (Unlocks.Bamboo, Items.Bamboo),
        (Unlocks.Iron, Items.Iron),
        (Unlocks.Quartz, Items.Quartz),
        (Unlocks.Mushrooms, Items.Mushroom),
        (Unlocks.Dynamite, Items.Dynamite),
    ]:
        if num_unlocked(skill) > 0:
            items.append(item)
    return items


def run(custom_items=None, mining_mode=None):
    if custom_items == None:
        custom_items = default_items()
    if len(custom_items) == 0 or not utils_farm.can_start_phase():
        return False
    if mining_mode == None:
        mining_mode = MINING_MODE
    if mining_mode not in ["layers", "individual"]:
        return False
    grouped = []
    ready = True
    for skill in [
        Unlocks.Underground_Senses,
        Unlocks.Mushrooms,
        Unlocks.Dynamite,
        Unlocks.Pyramid,
        Unlocks.Treasure_Map,
    ]:
        if num_unlocked(skill) == 0:
            ready = False
    if mining_mode == "layers" and ready:
        for item in custom_items:
            if item in [
                Items.Block,
                Items.Coal,
                Items.Iron,
                Items.Quartz,
                Items.Rice,
                Items.Mushroom,
                Items.Dynamite,
            ]:
                grouped.append(item)

    curr = 1
    next = 1
    has_megafarm = num_unlocked(Unlocks.Megafarm) > 0
    has_polyculture = num_unlocked(Unlocks.Polyculture) > 0
    has_trees = num_unlocked(Unlocks.Trees) > 0

    while True:
        for item in custom_items:
            if item in grouped:
                continue
            if num_items(item) < next:
                if not resource_manager.farm(
                    item, next, has_megafarm, has_polyculture, has_trees, True
                ):
                    return False
        if len(grouped) > 0 and not _mine_group(grouped, next):
            return False
        if num_unlocked(Unlocks.Sunflowers) > 0:
            if not resource_manager.farm(
                Items.Power, 10000, has_megafarm, has_polyculture, has_trees, True
            ):
                return False
        curr, next = utils_math.fibonacci(curr, next)


if __name__ == "__main__":
    run()
