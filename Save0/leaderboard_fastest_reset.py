import resource_manager


def run():
    t = get_time()
    has_megafarm = num_unlocked(Unlocks.Megafarm) > 0
    has_polyculture = num_unlocked(Unlocks.Polyculture) > 0
    # has_sunflowers = num_unlocked(Unlocks.Sunflowers) > 0
    has_trees = num_unlocked(Unlocks.Trees) > 0

    # https://youtu.be/hd_b_svu_oim74
    lvls = [
        (Unlocks.Expand, 1),  # Grid: 3x1 | Drones: 1
        (Unlocks.Plant, 1),
        (Unlocks.Speed, 1),
        (Unlocks.Expand, 2),  # Grid: 3x3 | Drones: 1
        (Unlocks.Speed, 2),
        (Unlocks.Carrots, 1),
        (Unlocks.Grass, 2),
        (Unlocks.Trees, 1),
        (Unlocks.Trees, 2),
        (Unlocks.Expand, 3),  # Grid: 4x4 | Drones: 1
        (Unlocks.Carrots, 2),
        (Unlocks.Speed, 3),
        (Unlocks.Watering, 1),
        (Unlocks.Expand, 4),  # Grid: 6x6 | Drones: 1
        (Unlocks.Watering, 2),
        (Unlocks.Carrots, 3),
        (Unlocks.Grass, 3),
        (Unlocks.Sunflowers, 1),
        (Unlocks.Fertilizer, 1),
        (Unlocks.Speed, 4),
        (Unlocks.Watering, 3),
        (Unlocks.Pumpkins, 1),
        (Unlocks.Pumpkins, 2),
        (Unlocks.Polyculture, 1),
        (Unlocks.Trees, 3),
        (Unlocks.Fertilizer, 2),
        (Unlocks.Watering, 4),
        (Unlocks.Speed, 5),
        (Unlocks.Mazes, 1),
        # (Unlocks.Megafarm, 1),  # Grid: 6x6 | Drones: 2
        (Unlocks.Expand, 5),  # Grid: 8x8 | Drones: 2
        (Unlocks.Grass, 4),
        (Unlocks.Trees, 4),
        (Unlocks.Watering, 5),
        (Unlocks.Fertilizer, 3),
        (Unlocks.Carrots, 4),
        (Unlocks.Watering, 5),
        (Unlocks.Pumpkins, 3),
        (Unlocks.Expand, 6),  # Grid: 12x12 | Drones: 2
        (Unlocks.Cactus, 1),
        (Unlocks.Dinosaurs, 1),
        (Unlocks.Dinosaurs, 2),
        (Unlocks.Polyculture, 2),
        (Unlocks.Polyculture, 3),
        (Unlocks.Mazes, 2),
        # (Unlocks.Megafarm, 2),  # Grid: 12x12 | Drones: 4
        # (Unlocks.Megafarm, 3),  # Grid: 12x12 | Drones: 8
        (Unlocks.Grass, 5),
        (Unlocks.Trees, 5),
        (Unlocks.Trees, 6),
        (Unlocks.Fertilizer, 4),
        (Unlocks.Watering, 6),
        (Unlocks.Watering, 7),
        (Unlocks.Mazes, 3),
        # (Unlocks.Megafarm, 4),  # Grid: 12x12 | Drones: 16
        (Unlocks.Carrots, 5),
        (Unlocks.Carrots, 6),
        (Unlocks.Pumpkins, 4),
        (Unlocks.Pumpkins, 5),
        (Unlocks.Pumpkins, 6),
        (Unlocks.Expand, 7),  # Grid: 16x16 | Drones: 16
        (Unlocks.Cactus, 2),
        (Unlocks.Cactus, 3),
        (Unlocks.Dinosaurs, 3),
        (Unlocks.Dinosaurs, 4),
        (Unlocks.Dinosaurs, 5),
        (Unlocks.Mazes, 4),
        (Unlocks.Leaderboard, 1),
    ]

    for skill, lvl in lvls:
        if num_unlocked(skill) >= lvl:
            continue
        quick_print("Work on", skill, "LVL", lvl)
        # if not has_megafarm:
        #     has_megafarm = num_unlocked(Unlocks.Megafarm) > 0
        if not has_polyculture:
            has_polyculture = num_unlocked(Unlocks.Polyculture) > 0
        if not has_trees:
            has_trees = num_unlocked(Unlocks.Trees) > 0
        # if not has_sunflowers:
        #     has_sunflowers = num_unlocked(Unlocks.Sunflowers) > 0
        # if has_sunflowers:
        #     resource_manager.farm(Items.Power, 10000, has_megafarm, has_polyculture, has_trees)
        if not resource_manager.get_skill(
            t, has_megafarm, has_polyculture, has_trees, lvl, skill
        ):
            quick_print("Reset stopped at", skill, lvl)
            return False
    return True


if __name__ == "__main__":
    run()
