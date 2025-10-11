def runCactus():
    import ICactus

    ws = get_world_size()
    while num_items(Items.Cactus) < 100000:
        ICactus.innerFarmCactusV1(ws)

runCactus()
