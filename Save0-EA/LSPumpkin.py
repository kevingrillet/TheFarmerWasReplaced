def runPumpkin():
    import IPumpkin

    ws = get_world_size()
    while num_items(Items.Pumpkin) < 100000:
        IPumpkin.innerfarm(ws)


runPumpkin()
