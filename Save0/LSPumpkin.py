def runPumpkin():
    import ISPumpkin

    ws = get_world_size()
    ISPumpkin.farm(10000000, -1, False)


runPumpkin()
