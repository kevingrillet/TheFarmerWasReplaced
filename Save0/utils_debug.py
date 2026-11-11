def print_unlocks():
    lvls = {}
    for unlock in Unlocks:
        lvls[unlock] = num_unlocked(unlock)
    quick_print(lvls)
    return lvls


def print_storage():
    storage = {}
    for item in Items:
        storage[item] = num_items(item)
    quick_print(storage)
    return storage


def reset():
    # Clear the world, not progression. Preserve the existing harvest/hat sequence.
    import utils_farm
    import utils_move

    if not utils_farm.can_start_phase():
        return False
    harvest()
    change_hat(Hats.Straw_Hat)
    if not utils_move.go_to(0, 0, get_world_size()):
        return False
    clear()
    return True


def sim(
    filename="leaderboard_hay_single",
    sim_unlocks=None,
    sim_items=None,
    sim_globals=None,
    seed=0,
    speedup=64,
):
    # Keep the original Hay setup by default; explicit empty inputs stay empty.
    if num_unlocked(Unlocks.Simulation) == 0:
        quick_print("Simulation is locked")
        return None
    if sim_unlocks == None:
        sim_unlocks = Unlocks
    if sim_items == None:
        qty = 1000000000
        sim_items = {
            Items.Hay: 0,
            Items.Wood: qty,
            Items.Carrot: qty,
            Items.Pumpkin: qty,
            Items.Cactus: qty,
            Items.Bone: qty,
            Items.Weird_Substance: qty,
            Items.Gold: qty,
            Items.Water: qty,
            Items.Fertilizer: qty,
            Items.Power: qty,
        }
    if sim_globals == None:
        sim_globals = {}
    run_time = simulate(filename, sim_unlocks, sim_items, sim_globals, seed, speedup)
    quick_print(run_time)
    return run_time


def profile_carrot(target_stock, multi=False):
    # Measure the migrated producer and its funding, with polyculture disabled.
    if num_items(Items.Carrot) >= target_stock:
        quick_print("Carrot profile skipped: target already satisfied")
        return True
    if num_unlocked(Unlocks.Timing) == 0:
        quick_print("Carrot profile requires Timing")
        return False
    import resource_manager

    started = get_time()
    started_ticks = get_tick_count()
    success = resource_manager.farm(
        Items.Carrot,
        target_stock,
        multi,
        False,
        num_unlocked(Unlocks.Trees) > 0,
    )
    elapsed = get_time() - started
    ticks = get_tick_count() - started_ticks
    quick_print("Carrot profile", success, "seconds", elapsed, "ticks", ticks)
    return success
