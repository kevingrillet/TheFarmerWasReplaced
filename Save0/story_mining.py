import resource_manager


def run(stop_at_leaderboard=False):
    # Continue an established farming save. Mining is also the drill upgrade.
    # Order/caps verified against the installed build 26410308; costs stay dynamic.
    t = get_time()
    lvls = [
        (Unlocks.Mining, 1),
        (Unlocks.Underground_Senses, 1),
        (Unlocks.Mining, 2),
        (Unlocks.Coal, 1),
        (Unlocks.Rice, 1),
        (Unlocks.Mining, 3),
        (Unlocks.Rice, 3),
        (Unlocks.Coal, 2),
        (Unlocks.Bamboo, 1),
        (Unlocks.Mining, 4),
        (Unlocks.Bamboo, 3),
        (Unlocks.Iron, 1),
        (Unlocks.Prospecting, 1),
        (Unlocks.Iron, 3),
        (Unlocks.Mining, 5),
        (Unlocks.Quartz, 1),
        (Unlocks.Mining, 6),
        (Unlocks.Quartz, 2),
        (Unlocks.Ore_Boost, 1),
        (Unlocks.Mushrooms, 1),
        (Unlocks.Megafarm, 2),
        (Unlocks.Mining, 7),
        (Unlocks.Mushrooms, 3),
        (Unlocks.Mining, 8),
        (Unlocks.Bamboo, 4),
        (Unlocks.Dynamite, 1),
        (Unlocks.Dynamite, 3),
        (Unlocks.Underground_Leaderboard, 1),
        (Unlocks.Jump, 1),
        (Unlocks.Debug_Place, 1),
        (Unlocks.Special_Soils, 1),
        (Unlocks.Petrified_Pumpkins, 1),
        (Unlocks.Pyramid, 1),
        (Unlocks.Treasure_Map, 1),
    ]
    lvls += [
        (Unlocks.Rice, 8),
        (Unlocks.Bamboo, 8),
        (Unlocks.Coal, 5),
        (Unlocks.Iron, 5),
        (Unlocks.Quartz, 4),
        (Unlocks.Mushrooms, 5),
        (Unlocks.Dynamite, 5),
        (Unlocks.Petrified_Pumpkins, 7),
        (Unlocks.Pyramid, 5),
        (Unlocks.Treasure_Map, 5),
        (Unlocks.Explosive_Drill, 1),
    ]
    for skill, lvl in lvls:
        if stop_at_leaderboard and num_unlocked(Unlocks.Underground_Leaderboard) > 0:
            return True
        if num_unlocked(skill) >= lvl:
            continue
        quick_print("DLC", skill, "LVL", lvl)
        if not resource_manager.get_skill(
            t,
            num_unlocked(Unlocks.Megafarm) > 0,
            num_unlocked(Unlocks.Polyculture) > 0,
            num_unlocked(Unlocks.Trees) > 0,
            lvl,
            skill,
        ):
            quick_print("DLC stopped at", skill, lvl)
            return False
    quick_print("DLC progression completed", get_time() - t)
    return True


if __name__ == "__main__":
    run()
