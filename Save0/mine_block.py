import utils_farm
import utils_mine


def requirements(target_stock):
    if num_items(Items.Block) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Mining) == 0:
        return None
    return {}


def _column(qty, steps):
    # Works before Underground Senses: no ground or depth API is required.
    for _ in range(steps):
        if num_items(Items.Block) >= qty:
            return True
        dig()
    return True


def _sector(qty, bounds, options, budget):
    return _column(qty, 16)


def _produce(target_stock, parallel):
    if num_items(Items.Block) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    sectors = []
    if parallel:
        sectors = utils_mine.sector_plan(True, target_stock - num_items(Items.Block))
        if len(sectors) == 0:
            return False
    if not utils_mine.prepare():
        return False
    if parallel:
        return utils_mine.run_sectors(_sector, Items.Block, target_stock, sectors)
    return utils_mine.run_columns(_column, target_stock, get_world_size(), 16, parallel)


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Block) < target_stock:
        before = num_items(Items.Block)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Block) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Block)
                return False
        else:
            stalled = 0
    return True


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
