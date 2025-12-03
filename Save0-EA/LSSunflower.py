def runPower():
    import IPower

    ws = get_world_size()
    while num_items(Items.Power) < 100000:
        IPower.innerfarm(ws)


runPower()
