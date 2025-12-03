import UManager
import UMaths


def runInfinite(customItems=None):
    if customItems == None:
        customItems = [
            Items.Hay,
            Items.Wood,
            Items.Carrot,
            Items.Pumpkin,
            Items.Cactus,
            Items.Bone,
            Items.Gold,
        ]

    curr = 1
    next = 1
    hasMegafarm = num_unlocked(Unlocks.Megafarm) > 0
    hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
    hasTrees = num_unlocked(Unlocks.Trees) > 0

    clear()
    while True:
        for item in customItems:
            if num_items(item) < next:
                UManager.farm(item, next, hasMegafarm, hasPolyculture, hasTrees, True)
        UManager.farm(Items.Power, 10000, hasMegafarm, hasPolyculture, hasTrees, True)
        curr, next = UMaths.fibonacci(curr, next)


def runUnlocksAll():
    t = get_time()
    hasMegafarm = num_unlocked(Unlocks.Megafarm) > 0
    hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
    hasTrees = num_unlocked(Unlocks.Trees) > 0

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
        if not hasMegafarm and num_unlocked(Unlocks.Megafarm) > 0:
            hasMegafarm = num_unlocked(Unlocks.Megafarm) > 0
        if not hasPolyculture and num_unlocked(Unlocks.Polyculture) > 0:
            hasPolyculture = True
        if not hasTrees and num_unlocked(Unlocks.Trees) > 0:
            hasTrees = num_unlocked(Unlocks.Trees) > 0
        UManager.farm(Items.Power, 10000, hasMegafarm, hasPolyculture, hasTrees)
        UManager.getSkill(t, hasMegafarm, hasPolyculture, hasTrees, lvl, skill)
