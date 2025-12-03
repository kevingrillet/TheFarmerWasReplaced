import UMaths


def run():
    import IBone
    import ICactus
    import ICarrots
    import IGold
    import IHayWood
    import IPower
    import IPumpkin

    curr = 1
    clear()
    while True:
        if num_items(Items.Hay) < curr and num_items(Items.Wood) < curr:
            IHayWood.farmHayWood(curr)
        if num_items(Items.Hay) < curr:
            IHayWood.farmHay(curr)
        if num_items(Items.Wood) < curr:
            IHayWood.farm(curr, True)
        if num_items(Items.Carrot) < curr:
            ICarrots.farm(curr)
        if num_items(Items.Pumpkin) < curr:
            IPumpkin.farm(curr, -1)
        if num_items(Items.Cactus) < curr:
            ICactus.farm(curr)
        if num_items(Items.Power) < 10000:
            IPower.farm(10000)
        if num_items(Items.Bone) < curr:
            IBone.farm(curr)
        if num_items(Items.Gold) < curr:
            IGold.farm(curr)
        curr = UMaths.next_val(curr)


def runV2(customItems):
    import UManager

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
    hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
    hasTrees = num_unlocked(Unlocks.Trees) > 0

    clear()
    while True:
        for item in customItems:
            if num_items(item) < next:
                UManager.farm(item, next, hasPolyculture, hasTrees)
        UManager.farm(Items.Power, 10000, hasPolyculture, hasTrees)
        curr, next = UMaths.fibonacci(curr, next)


def runV3():
    import UManager

    t = get_time()
    hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
    hasTrees = num_unlocked(Unlocks.Trees) > 0

    lvls = {
        Unlocks.Speed: 20,
        Unlocks.Grass: 14,
        Unlocks.Expand: 9,
        Unlocks.Carrots: 12,
        Unlocks.Trees: 10,
        Unlocks.Watering: 20,
        Unlocks.Fertilizer: 8,
        Unlocks.Pumpkins: 10,
        Unlocks.Polyculture: 10,
        Unlocks.Mazes: 10,
        Unlocks.Cactus: 10,
        Unlocks.Dinosaurs: 10,
        Unlocks.Leaderboard: 1,
    }

    for lvl in lvls:
        UManager.farm(Items.Power, 10000, hasPolyculture, hasTrees)
        UManager.getSkill(t, hasPolyculture, hasTrees, lvls[lvl], lvl)
