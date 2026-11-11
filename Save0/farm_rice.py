import utils_farm
import utils_mine


def requirements(target_stock):
    if num_items(Items.Rice) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Rice) == 0:
        return None
    return {}


def _column(qty, steps):
    for _ in range(steps):
        if num_items(Items.Rice) >= qty:
            return True
        if not utils_mine.seek(Grounds.Clay):
            return False
        if not plant(Entities.Rice):
            return False
        if not utils_farm.wait_ripe(30):
            return False
        if not harvest():
            return False
        if not move(North):
            return False
    return True


def _produce(target_stock, parallel):
    if num_items(Items.Rice) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), parallel):
        return False
    min_yield = 2 ** (num_unlocked(Unlocks.Rice) - 1)
    return utils_mine.produce_columns(
        _column, Items.Rice, target_stock, parallel, min_yield
    )


def produce_single(target_stock):
    return _produce(target_stock, False)


def produce_multi(target_stock):
    return _produce(target_stock, True)


def _farm(target_stock, parallel):
    stalled = 0
    while num_items(Items.Rice) < target_stock:
        before = num_items(Items.Rice)
        if not _produce(target_stock, parallel):
            return False
        if num_items(Items.Rice) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Rice)
                return False
        else:
            stalled = 0
    return True


def farm_single(target_stock):
    return _farm(target_stock, False)


def farm_multi(target_stock):
    return _farm(target_stock, True)
