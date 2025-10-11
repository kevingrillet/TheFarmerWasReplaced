def runCarrot():
    import ICarrots

    ws = get_world_size()
    while num_items(Items.Carrot) < 100000:
        ICarrots.innerFarmCarrot(ws)

runCarrot()
