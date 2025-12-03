def runCactus():
    import IMCactus

    ws = get_world_size()
    while num_items(Items.Cactus) < 33554432:
        IMCactus.farm(ws, False)


runCactus()
