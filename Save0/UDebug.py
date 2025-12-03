def printUnlocks():
    lvls = {}
    for unlock in Unlocks:
        lvls[unlock] = num_unlocked(unlock)
    quick_print(lvls)


def printStorage():
    storage = {}
    for item in Items:
        storage[item] = num_items(item)
    quick_print(storage)


def reset():
    import UMove

    harvest()
    change_hat(Hats.Straw_Hat)
    UMove.goTo(0, 0, get_world_size())
    clear()


def sim():
    QTY = 1000000000
    filename = "f0"
    sim_unlocks = Unlocks
    sim_items = {
        Items.Hay: QTY,
        Items.Wood: QTY,
        Items.Carrot: QTY,
        Items.Pumpkin: QTY,
        Items.Cactus: QTY,
        Items.Bone: QTY,
        Items.Weird_Substance: QTY,
        Items.Gold: QTY,
        Items.Water: QTY,
        Items.Fertilizer: QTY,
        Items.Power: QTY,
    }
    sim_globals = {}
    seed = 0
    speedup = 64
    run_time = simulate(filename, sim_unlocks, sim_items, sim_globals, seed, speedup)
    quick_print(run_time)
