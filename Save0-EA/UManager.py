import IBone
import ICactus
import ICarrots
import IGold
import IHayWood
import IPolyculture
import IPower
import IPumpkin
import UDebug

def farm(item, qty, hasT, hasP):
    # Farm the specified item until the desired quantity is reached

    if item == Items.Hay:
        if hasP:
            IPolyculture.farm(Entities.Grass, qty)
        else:
            IHayWood.farmHay(qty)
    elif item == Items.Wood:
        if hasP:
            IPolyculture.farm(Entities.Tree, qty)
        else:
            IHayWood.farmWood(qty, hasT)
    elif item == Items.Carrot:
        if hasP:
            IPolyculture.farm(Entities.Carrot, qty)
        else:
            ICarrots.farmCarrot(qty)
    elif item == Items.Pumpkin:
        IPumpkin.farmPumpkin(qty, -1)
    elif item == Items.Weird_Substance:
        IPumpkin.farmPumpkin(-1, qty)
    elif item == Items.Cactus:
        ICactus.farmCactus(qty)
    elif item == Items.Bone:
        IBone.farmBone(qty)
    elif item == Items.Gold:
        IGold.farmGold(qty)
    elif item == Items.Power:
        IPower.farmPower(qty)

def checkRequirement(entity, qty):
    # Determine how much of each item is needed to farm the entity

    hasP = num_unlocked(Unlocks.Polyculture) > 0
    hasT = num_unlocked(Unlocks.Trees) > 0
    if entity == Entities.Carrot:
        qtyChk = 1.5 * (qty - num_items(Items.Carrot)) / num_unlocked(Unlocks.Carrots)
    elif entity == Entities.Pumpkin:
        ws = get_world_size()
        grid = ws
        if grid > 5:
            grid = 5
        pumpkinAgv = (ws ** 2) * grid
        pumpkinMul = (qty - num_items(Items.Pumpkin)) / pumpkinAgv
        qtyChk = (ws ** 2) * pumpkinMul
    elif entity == Entities.Cactus:
        ws = get_world_size()
        cactusCnt = (ws**2)/2
        cactusAvg = cactusCnt**2
        cactusMul = (qty - num_items(Items.Cactus)) / cactusAvg
        qtyChk = 2 * (ws ** 2) * cactusMul * 1.25
    elif entity == Entities.Sunflower:
        qtyChk = (qty - num_items(Items.Power)) / num_unlocked(Unlocks.Sunflowers)
    elif entity == Entities.Dinosaur:
        missing = qty - num_items(Items.Bone)
        bones = (get_world_size() ** 2) ** 2
        qtyChk = missing / bones + 100
    elif entity == Items.Weird_Substance:
        ws = get_world_size()
        grid = ws
        if grid > 5:
            grid = 5
        gooAgv = 0.75 * (ws ** 2) * grid
        gooMul = (qty - num_items(Items.Weird_Substance)) / gooAgv
        qtyChk = 2 * (ws ** 2) * gooMul
        entity = Entities.Pumpkin
    else:
        qtyChk = qty

    cost = get_cost(entity)
    for item in cost:
        itemCost = cost[item] * qtyChk
        while num_items(item) < itemCost:
            farm(item, itemCost, hasT, hasP)

def getSkill(t, hasT, hasP, level, skill):
    # Unlock the specified skill to the desired level

    lt = get_time()
    while num_unlocked(skill) < level:
        if skill == Unlocks.Expand and level == 7:
            cost = {Items.Bone:5000}
        elif skill == Unlocks.Expand and level == 9:
            cost = {Items.Bone:80000}
        else:
            cost = get_cost(skill)
        for item in cost:
            farm(item, cost[item], hasT, hasP)
        unlock(skill)
        et = get_time()
        quick_print(skill, "LVL", num_unlocked(skill), "Completion", et-lt, "Global", et-t)
        UDebug.printStorage()
