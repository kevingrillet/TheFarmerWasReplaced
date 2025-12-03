def runPower():
    import IMPower

    ws = get_world_size()
    while num_items(Items.Power) < 100000:
        IMPower.farm(100000, False)


runPower()
