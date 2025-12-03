import IMCactus
import IMCarrots
import IMGold
import IMHay
import IMPolyculture
import IMPower
import IMPumpkin
import IMWood
import ISBone
import ISCactus
import ISCarrots
import ISGold
import ISHayWood
import ISPolyculture
import ISPower
import ISPumpkin
import UDebug


def farm(item, qty, hasMegafarm, hasPolyculture, hasTrees, debug=False):
    # Farm the specified item until the desired quantity is reached

    if debug:
        quick_print("To farm", qty, item)
        UDebug.printStorage()
    if item == Items.Hay:
        if hasMegafarm and hasPolyculture:
            IMPolyculture.farm(Entities.Grass, qty)
        elif hasMegafarm:
            IMHay.farm(qty)
        elif hasPolyculture:
            ISPolyculture.farm(Entities.Grass, qty)
        else:
            ISHayWood.farmHay(qty)
    elif item == Items.Wood:
        if hasMegafarm and hasPolyculture:
            IMPolyculture.farm(Entities.Tree, qty)
        elif hasMegafarm:
            IMWood.farm(qty)
        elif hasPolyculture:
            ISPolyculture.farm(Entities.Tree, qty)
        else:
            ISHayWood.farm(qty, hasTrees)
    elif item == Items.Carrot:
        if hasMegafarm and hasPolyculture:
            IMPolyculture.farm(Entities.Carrot, qty)
        elif hasMegafarm:
            IMCarrots.farm(qty)
        elif hasPolyculture:
            ISPolyculture.farm(Entities.Carrot, qty)
        else:
            ISCarrots.farm(qty)
    elif item == Items.Pumpkin:
        if hasMegafarm:
            IMPumpkin.farm(qty, -1)
        else:
            ISPumpkin.farm(qty, -1)
    elif item == Items.Weird_Substance:
        if hasMegafarm:
            IMPumpkin.farm(-1, qty)
        else:
            ISPumpkin.farm(-1, qty)
    elif item == Items.Cactus:
        if hasMegafarm:
            IMCactus.farm(qty)
        else:
            ISCactus.farm(qty)
    elif item == Items.Bone:
        ISBone.farm(qty)
    elif item == Items.Gold:
        if hasMegafarm:
            IMGold.farm(qty)
        else:
            ISGold.farm(qty)
    elif item == Items.Power:
        if hasMegafarm:
            IMPower.farm(qty)
        else:
            ISPower.farm(qty)
    if debug:
        quick_print("Farmed", qty, item)
        UDebug.printStorage()


def checkRequirement(entity, qty, debug=False):
    # Determine how much of each item is needed to farm the entity

    hasMegafarm = num_unlocked(Unlocks.Megafarm) > 0
    hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
    hasTrees = num_unlocked(Unlocks.Trees) > 0
    if entity == Entities.Carrot:
        qtyChk = 1.5 * (qty - num_items(Items.Carrot)) / num_unlocked(Unlocks.Carrots)
    elif entity == Entities.Pumpkin:
        ws = get_world_size()
        grid = ws
        if grid > 6:
            grid = 6
        pumpkinAgv = (ws**2) * grid
        pumpkinMul = (qty - num_items(Items.Pumpkin)) / pumpkinAgv
        qtyChk = 2 * (ws**2) * pumpkinMul / num_unlocked(Unlocks.Pumpkins)
    elif entity == Entities.Cactus:
        ws = get_world_size()
        cactusCnt = (ws**2) / 2
        cactusAvg = cactusCnt**2
        cactusMul = (qty - num_items(Items.Cactus)) / cactusAvg
        qtyChk = (ws**2) * cactusMul * 1.25 / num_unlocked(Unlocks.Cactus)
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
        gooAgv = 0.75 * (ws**2) * grid
        gooMul = (qty - num_items(Items.Weird_Substance)) / gooAgv
        qtyChk = 2 * (ws**2) * gooMul
        entity = Entities.Pumpkin
    else:
        qtyChk = qty

    cost = get_cost(entity)
    for item in cost:
        itemCost = cost[item] * qtyChk
        if debug:
            quick_print("To farm", qty, entity, "require", itemCost, item)
        while num_items(item) < itemCost:
            farm(item, itemCost, hasMegafarm, hasPolyculture, hasTrees, debug)


def getSkill(t, hasMegafarm, hasPolyculture, hasTrees, level, skill):
    # Unlock the specified skill to the desired level

    lt = get_time()
    curr = num_unlocked(skill)
    while curr < level:
        cost = get_cost(skill)
        for item in cost:
            farm(item, cost[item], hasMegafarm, hasPolyculture, hasTrees)
        unlock(skill)
        et = get_time()
        curr = num_unlocked(skill)
        quick_print(skill, "LVL", curr, "Completion", et - lt, "Global", et - t)
        UDebug.printStorage()
