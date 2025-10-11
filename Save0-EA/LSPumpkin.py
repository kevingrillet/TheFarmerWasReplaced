def runPumpkin():
    import IPumpkin

    ws = get_world_size()
    while num_items(Items.Pumpkin) < 100000:
        IPumpkin.innerFarmPumpkin(ws)

runPumpkin()
