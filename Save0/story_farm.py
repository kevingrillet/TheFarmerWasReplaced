import resource_manager


def run():
    t = get_time()
    has_megafarm = num_unlocked(Unlocks.Megafarm) > 0
    has_polyculture = num_unlocked(Unlocks.Polyculture) > 0
    has_trees = num_unlocked(Unlocks.Trees) > 0

    lvls = [
        (Unlocks.Expand, 6),
        (Unlocks.Carrots, 6),
        (Unlocks.Pumpkins, 5),
        (Unlocks.Cactus, 1),
        (Unlocks.Mazes, 1),
        (Unlocks.Dinosaurs, 1),
        (Unlocks.Polyculture, 2),
        (Unlocks.Grass, 8),
        (Unlocks.Trees, 8),
        (Unlocks.Carrots, 7),
        (Unlocks.Pumpkins, 6),
        (Unlocks.Expand, 7),
        (Unlocks.Polyculture, 2),
        (Unlocks.Cactus, 2),
        (Unlocks.Mazes, 2),
        (Unlocks.Dinosaurs, 2),
        (Unlocks.Grass, 9),
        (Unlocks.Trees, 9),
        (Unlocks.Carrots, 8),
        (Unlocks.Pumpkins, 7),
        (Unlocks.Expand, 8),
        (Unlocks.Polyculture, 3),
        (Unlocks.Grass, 10),
        (Unlocks.Trees, 10),
        (Unlocks.Carrots, 10),
        (Unlocks.Watering, 9),
        (Unlocks.Fertilizer, 4),
        (Unlocks.Pumpkins, 10),
        (Unlocks.Cactus, 3),
        (Unlocks.Mazes, 3),
        (Unlocks.Dinosaurs, 3),
        (Unlocks.Polyculture, 4),
        (Unlocks.Cactus, 4),
        (Unlocks.Mazes, 4),
        (Unlocks.Dinosaurs, 4),
        (Unlocks.Polyculture, 5),
        (Unlocks.Expand, 9),
        (Unlocks.Cactus, 5),
        (Unlocks.Mazes, 5),
        (Unlocks.Dinosaurs, 5),
        (Unlocks.Cactus, 6),
        (Unlocks.Mazes, 6),
        (Unlocks.Dinosaurs, 6),
        (Unlocks.Debug_2, 1),
        (Unlocks.Simulation, 1),
        (Unlocks.Leaderboard, 1),
        (Unlocks.Megafarm, 5),
        (Unlocks.The_Farmers_Remains, 1),
        (Unlocks.Top_Hat, 1),
    ]

    for skill, lvl in lvls:
        if num_unlocked(skill) >= lvl:
            continue
        quick_print("Work on", skill, "LVL", lvl)
        if not has_megafarm and num_unlocked(Unlocks.Megafarm) > 0:
            has_megafarm = num_unlocked(Unlocks.Megafarm) > 0
        if not has_polyculture and num_unlocked(Unlocks.Polyculture) > 0:
            has_polyculture = True
        if not has_trees and num_unlocked(Unlocks.Trees) > 0:
            has_trees = num_unlocked(Unlocks.Trees) > 0
        if num_unlocked(Unlocks.Sunflowers) > 0:
            if not resource_manager.farm(
                Items.Power, 10000, has_megafarm, has_polyculture, has_trees
            ):
                quick_print("Base story stopped: Power production failed")
                return False
        if not resource_manager.get_skill(
            t, has_megafarm, has_polyculture, has_trees, lvl, skill
        ):
            quick_print("Base story stopped at", skill, lvl)
            return False
    return True


if __name__ == "__main__":
    run()
