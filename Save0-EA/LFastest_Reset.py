def run():
    import UManager

    def startToTrees(t, hasPolyculture, hasTrees):
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Plant)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Grass)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Carrots)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Watering)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Trees)

    def treesToPolyculture(t, hasPolyculture, hasTrees):
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Fertilizer)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Grass)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Trees)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Pumpkins)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Grass)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Trees)
        UManager.getSkill(t, hasPolyculture, hasTrees, 5, Unlocks.Watering)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Fertilizer)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Carrots)
        UManager.getSkill(t, hasPolyculture, hasTrees, 4, Unlocks.Grass)
        UManager.getSkill(t, hasPolyculture, hasTrees, 4, Unlocks.Trees)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Carrots)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Pumpkins)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 4, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 10, Unlocks.Watering)
        UManager.getSkill(t, hasPolyculture, hasTrees, 4, Unlocks.Fertilizer)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Cactus)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Dinosaurs)
        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Mazes)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Polyculture)

    def polycultureToEnd(t, hasPolyculture, hasTrees):
        UManager.getSkill(t, hasPolyculture, hasTrees, 7, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Pumpkins)
        UManager.getSkill(t, hasPolyculture, hasTrees, 12, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 4, Unlocks.Pumpkins)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Expand)

        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Mazes)
        UManager.getSkill(t, hasPolyculture, hasTrees, 2, Unlocks.Cactus)
        UManager.getSkill(t, hasPolyculture, hasTrees, 3, Unlocks.Dinosaurs)

        UManager.getSkill(t, hasPolyculture, hasTrees, 8, Unlocks.Expand)

        UManager.getSkill(t, hasPolyculture, hasTrees, 5, Unlocks.Mazes)
        UManager.getSkill(t, hasPolyculture, hasTrees, 5, Unlocks.Cactus)
        UManager.getSkill(t, hasPolyculture, hasTrees, 5, Unlocks.Dinosaurs)

        UManager.getSkill(t, hasPolyculture, hasTrees, 14, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 14, Unlocks.Grass)
        UManager.getSkill(t, hasPolyculture, hasTrees, 12, Unlocks.Carrots)

        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Dinosaurs)
        UManager.getSkill(t, hasPolyculture, hasTrees, 9, Unlocks.Expand)
        UManager.getSkill(t, hasPolyculture, hasTrees, 20, Unlocks.Speed)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Polyculture)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Fertilizer)

        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Mazes)
        UManager.getSkill(t, hasPolyculture, hasTrees, 6, Unlocks.Cactus)
        UManager.getSkill(t, hasPolyculture, hasTrees, 7, Unlocks.Fertilizer)
        UManager.getSkill(t, hasPolyculture, hasTrees, 8, Unlocks.Polyculture)
        UManager.getSkill(t, hasPolyculture, hasTrees, 8, Unlocks.Mazes)

        UManager.getSkill(t, hasPolyculture, hasTrees, 1, Unlocks.Leaderboard)

    t = get_time()
    startToTrees(t, False, False)
    treesToPolyculture(t, True, False)
    polycultureToEnd(t, True, True)


run()
