import utils_farm
import utils_mine


def requirements(target_stock):
    if num_items(Items.Quartz) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Quartz) == 0:
        return None
    return utils_mine.ore_requirements(Items.Iron)


def produce_single(target_stock):
    if num_items(Items.Quartz) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock)):
        return False
    return utils_mine.produce_ore(
        Grounds.Quartz, Items.Quartz, target_stock, Items.Iron
    )


def farm_single(target_stock):
    if num_items(Items.Quartz) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock)):
        return False
    return utils_mine.farm_ore(Grounds.Quartz, Items.Quartz, target_stock, Items.Iron)


def produce_multi(target_stock):
    if num_items(Items.Quartz) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), True):
        return False
    return utils_mine.produce_ore(
        Grounds.Quartz, Items.Quartz, target_stock, Items.Iron, True
    )


def farm_multi(target_stock):
    if num_items(Items.Quartz) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), True):
        return False
    return utils_mine.farm_ore(
        Grounds.Quartz, Items.Quartz, target_stock, Items.Iron, True
    )
