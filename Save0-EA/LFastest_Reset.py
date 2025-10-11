def run():
    import UManager

    def startToTrees(t, hasT, hasP):
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Plant)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Grass)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Carrots)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Watering)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Trees)

    def treesToPolyculture(t, hasT, hasP):
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Fertilizer)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Grass)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Trees)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Pumpkins)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Grass)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Trees)
        UManager.getSkill(t, hasT, hasP, 5, Unlocks.Watering)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Fertilizer)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Carrots)
        UManager.getSkill(t, hasT, hasP, 4, Unlocks.Grass)
        UManager.getSkill(t, hasT, hasP, 4, Unlocks.Trees)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Carrots)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Pumpkins)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 4, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 10, Unlocks.Watering)
        UManager.getSkill(t, hasT, hasP, 4, Unlocks.Fertilizer)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Cactus)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Dinosaurs)
        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Mazes)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Polyculture)

    def polycultureToEnd(t, hasT, hasP):
        UManager.getSkill(t, hasT, hasP, 7, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Pumpkins)
        UManager.getSkill(t, hasT, hasP, 12, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 4, Unlocks.Pumpkins)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Expand)

        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Mazes)
        UManager.getSkill(t, hasT, hasP, 2, Unlocks.Cactus)
        UManager.getSkill(t, hasT, hasP, 3, Unlocks.Dinosaurs)

        UManager.getSkill(t, hasT, hasP, 8, Unlocks.Expand)

        UManager.getSkill(t, hasT, hasP, 5, Unlocks.Mazes)
        UManager.getSkill(t, hasT, hasP, 5, Unlocks.Cactus)
        UManager.getSkill(t, hasT, hasP, 5, Unlocks.Dinosaurs)

        UManager.getSkill(t, hasT, hasP, 14, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 14, Unlocks.Grass)
        UManager.getSkill(t, hasT, hasP, 12, Unlocks.Carrots)

        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Dinosaurs)
        UManager.getSkill(t, hasT, hasP, 9, Unlocks.Expand)
        UManager.getSkill(t, hasT, hasP, 20, Unlocks.Speed)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Polyculture)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Fertilizer)

        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Mazes)
        UManager.getSkill(t, hasT, hasP, 6, Unlocks.Cactus)
        UManager.getSkill(t, hasT, hasP, 7, Unlocks.Fertilizer)
        UManager.getSkill(t, hasT, hasP, 8, Unlocks.Polyculture)
        UManager.getSkill(t, hasT, hasP, 8, Unlocks.Mazes)

        UManager.getSkill(t, hasT, hasP, 1, Unlocks.Leaderboard)

    t = get_time()
    startToTrees(t, False, False)
    treesToPolyculture(t, True, False)
    polycultureToEnd(t, True, True)

run()
