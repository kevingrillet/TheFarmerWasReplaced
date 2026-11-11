# Choose here, then execute this file. See docs/benchmarks/README.md.
LEADERBOARD = Leaderboards.Fastest_Reset  # e.g. Leaderboards.Hay_Single
MODE = "leaderboard"  # simulation / leaderboard (Steam).
STRATEGY = "default"  # default / candidate / cheese (see the dictionaries below).
SEED = 0  # Simulation only; a negative value selects a random seed.
SPEEDUP = 1000


# Native category -> (standalone script, simulation resource, single setup).
SCRIPTS = {
    Leaderboards.Hay: ("leaderboard_hay", "hay", False),
    Leaderboards.Hay_Single: ("leaderboard_hay_single", "hay", True),
    Leaderboards.Wood: ("leaderboard_wood", "wood", False),
    Leaderboards.Wood_Single: ("leaderboard_wood_single", "wood", True),
    Leaderboards.Carrots: ("leaderboard_carrot", "carrot", False),
    Leaderboards.Carrots_Single: ("leaderboard_carrot_single", "carrot", True),
    Leaderboards.Pumpkins: ("leaderboard_pumpkin", "pumpkin", False),
    Leaderboards.Pumpkins_Single: ("leaderboard_pumpkin_single", "pumpkin", True),
    Leaderboards.Cactus: ("leaderboard_cactus", "cactus", False),
    Leaderboards.Cactus_Single: ("leaderboard_cactus_single", "cactus", True),
    Leaderboards.Sunflowers: ("leaderboard_power", "power", False),
    Leaderboards.Sunflowers_Single: ("leaderboard_power_single", "power", True),
    Leaderboards.Maze: ("leaderboard_gold", "gold", False),
    Leaderboards.Maze_Single: ("leaderboard_gold_single", "gold", True),
    Leaderboards.Dinosaur: ("leaderboard_bone", "bone", False),
    Leaderboards.Fastest_Reset: ("leaderboard_fastest_reset", "fastest_reset", False),
    Leaderboards.Fastest_Underground_Reset: (
        "leaderboard_fastest_underground_reset",
        "fastest_underground_reset",
        False,
    ),
}

CHEESE_SCRIPTS = {
    Leaderboards.Sunflowers: "leaderboard_power_columns",
    Leaderboards.Maze: "leaderboard_gold_reuse",
    Leaderboards.Dinosaur: "leaderboard_bone_hybrid",
}


CANDIDATE_SCRIPTS = {
    Leaderboards.Carrots: "leaderboard_carrot_polyculture",
    Leaderboards.Carrots_Single: "leaderboard_carrot_single_polyculture",
    Leaderboards.Wood: "leaderboard_wood_polyculture",
    Leaderboards.Wood_Single: "leaderboard_wood_single_polyculture",
    Leaderboards.Pumpkins_Single: "leaderboard_pumpkin_single_pipeline",
    Leaderboards.Sunflowers: "leaderboard_power_global",
}


def _simulation_setup(resource, single):
    if resource == "fastest_reset" or resource == "fastest_underground_reset":
        return {}, {}
    # Production upgrades only: programming features are supplied by simulate().
    # Exclude DLC upgrades from TFWR trials, even when the DLC is installed.
    unlocks = {
        Unlocks.Cactus: -1,
        Unlocks.Carrots: -1,
        Unlocks.Costs: -1,
        Unlocks.Dinosaurs: -1,
        Unlocks.Expand: -1,
        Unlocks.Fertilizer: -1,
        Unlocks.Grass: -1,
        Unlocks.Hats: -1,
        Unlocks.Mazes: -1,
        Unlocks.Megafarm: -1,
        Unlocks.Plant: -1,
        Unlocks.Polyculture: -1,
        Unlocks.Pumpkins: -1,
        Unlocks.Senses: -1,
        Unlocks.Speed: -1,
        Unlocks.Sunflowers: -1,
        Unlocks.Timing: -1,
        Unlocks.Trees: -1,
        Unlocks.Watering: -1,
    }
    if single and resource != "bone":
        # Native single setup: Expand level 5 = 8x8, no Megafarm upgrade.
        unlocks[Unlocks.Expand] = 5
        unlocks[Unlocks.Megafarm] = 0
    qty = 1000000000
    items = {Items.Power: qty}
    if resource == "power":
        # Sunflowers starts with no Power: do not satisfy the goal in the setup.
        items = {Items.Carrot: qty}
    elif resource == "carrot":
        items[Items.Hay] = qty
        items[Items.Wood] = qty
    elif resource == "pumpkin":
        items[Items.Carrot] = qty
    elif resource == "cactus":
        items[Items.Pumpkin] = qty
    elif resource == "gold":
        items[Items.Weird_Substance] = qty
    elif resource == "bone":
        items[Items.Cactus] = qty
    return unlocks, items


def run(leaderboard=None, mode=None, strategy=None, seed=None, speedup=None):
    # None reads the settings above; an explicit seed of 0 remains valid.
    if leaderboard == None:
        leaderboard = LEADERBOARD
    if mode == None:
        mode = MODE
    if strategy == None:
        strategy = STRATEGY
    if seed == None:
        seed = SEED
    if speedup == None:
        speedup = SPEEDUP
    if mode not in ["simulation", "leaderboard"]:
        quick_print("Unknown mode:", mode)
        return False
    if leaderboard not in SCRIPTS:
        quick_print("Unsupported leaderboard:", leaderboard)
        return False
    filename, resource, single = SCRIPTS[leaderboard]
    if strategy == "cheese" and leaderboard in CHEESE_SCRIPTS:
        filename = CHEESE_SCRIPTS[leaderboard]
    elif strategy == "candidate" and leaderboard in CANDIDATE_SCRIPTS:
        filename = CANDIDATE_SCRIPTS[leaderboard]
    elif strategy != "default":
        quick_print("Unsupported strategy for leaderboard:", strategy, leaderboard)
        return False
    if speedup <= 0:
        quick_print("Speedup must be positive")
        return False
    if mode == "simulation":
        if num_unlocked(Unlocks.Simulation) == 0:
            quick_print("Simulation is locked")
            return False
        unlocks, items = _simulation_setup(resource, single)
        quick_print("Simulation:", filename, "seed:", seed)
        elapsed = simulate(filename, unlocks, items, {}, seed, speedup)
        quick_print("Simulation seconds:", elapsed)
        return elapsed
    required = Unlocks.Leaderboard
    if resource == "fastest_underground_reset":
        required = Unlocks.Underground_Leaderboard
    if num_unlocked(required) == 0:
        quick_print("Leaderboard is locked:", required)
        return False
    quick_print("Steam leaderboard:", leaderboard, filename)
    leaderboard_run(leaderboard, filename, speedup)
    return True


if __name__ == "__main__":
    run()
