def runWood():
    import IHayWood

    ws = get_world_size()
    while num_items(Items.Wood) < 100000:
        # IHayWood.innerfarm(ws)
        IHayWood.innerfarmWithT(ws)


runWood()
