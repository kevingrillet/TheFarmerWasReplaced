def fertilizer():
    # Use fertilizer if available

    if num_items(Items.Fertilizer) > 0:
        use_item(Items.Fertilizer)
        return True
    return False

def fertilizerOrWater():
    if not fertilizer():
        return water()
    return True

def qHarvest():
    # Harvest if possible

    if can_harvest():
        harvest()
        return True
    return False

def qTill():
    # Till the ground if it's not Soil

    if get_ground_type() != Grounds.Soil:
        till()
        return True
    return False

def qTillGrass():
    # Till the ground if it's not Grassland

    if get_ground_type() != Grounds.Grassland:
        till()
        return True
    return False

def tillAll(ws):
    # Till the entire field in a snake-like pattern

    for _ in range(ws):
        for _ in range(ws):
            move(East)
            qTill()
        move(North)

def water():
    # Use water if available and water level is low

    if get_water() < .75 and num_items(Items.Water) > 0:
        use_item(Items.Water)
        return True
    return False
