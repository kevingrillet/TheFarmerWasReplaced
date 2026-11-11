# Leaderboards.Sunflowers: candidate adapted from cheese_power.py.
# Persistent columns trade the petal bonus for less orchestration; benchmark it.
TARGET = 100000


def _join(handles):
    success = True
    for handle in handles:
        if not wait_for(handle):
            success = False
    return success


def _column(ws, target):
    best_stock = num_items(Items.Power)
    last_gain = get_time()
    while num_items(Items.Power) < target:
        for _ in range(ws):
            if num_items(Items.Power) >= target:
                return True
            if get_ground_type() != Grounds.Soil:
                till()
                if get_ground_type() != Grounds.Soil:
                    return False
            if get_water() < 0.75:
                use_item(Items.Water)
            entity = get_entity_type()
            if entity != None and can_harvest():
                if not harvest():
                    return False
                entity = None
            if entity == None:
                if not plant(Entities.Sunflower):
                    return False
            elif entity != Entities.Sunflower:
                return False
            if not move(North):
                return False
        stock = num_items(Items.Power)
        if stock > best_stock:
            best_stock = stock
            last_gain = get_time()
        elif get_time() - last_gain > 180:
            return False
    return True


def run(target=TARGET):
    finish_target = target + 1
    if num_items(Items.Power) >= finish_target:
        return True
    if num_drones() != 1 or num_unlocked(Unlocks.Timing) == 0:
        return False
    clear()
    ws = get_world_size()
    handles = []
    success = True
    for x in range(ws):
        if num_items(Items.Power) >= finish_target:
            break
        # The parent farms the last column, or takes over when capacity is full.
        handle = None
        if x < ws - 1:
            handle = spawn_drone(_column, ws, finish_target)
        if handle == None:
            success = _column(ws, finish_target)
            break
        handles.append(handle)
        if not move(East):
            success = False
            break
    joined = _join(handles)
    return success and joined and num_items(Items.Power) >= target


if __name__ == "__main__":
    run()
