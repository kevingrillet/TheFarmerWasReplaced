# def runHay():
#     import IHayWood

#     ws = get_world_size()
#     while num_items(Items.Hay) < 100000:
#         IHayWood.innerFarmHay(ws)

# runHay()


def runHayPoly():
    import UFarm

    ws = get_world_size()
    companions = {}  # Dictionary to track companion plants positions
    link = {}  # Dictionary to link positions with companions

    while True:
        dX, dY = get_pos_x(), get_pos_y()
        calcCompanion = False

        # Case 1: Current entity is Grass
        if get_entity_type() == Entities.Grass:
            UFarm.qHarvest()

            # If this grass had a companion, remove the mapping
            if (dX, dY) in link:
                companions.pop(link[(dX, dY)])
                link.pop((dX, dY))

            # If a companion plant must be replanted here
            if (dX, dY) in companions:
                entity = companions[(dX, dY)]
                plant(entity)

            # Need to calculate a new companion for this position
            else:
                calcCompanion = True

        # Case 2: Current entity is not Grass (so it's a companion)
        else:
            if (dX, dY) not in companions:
                harvest()
            calcCompanion = True

        # If we need to recalculate companion mapping
        if calcCompanion:
            companion, (cX, cY) = get_companion()

            # Skip carrot (no Till)
            while companion == Entities.Carrot:
                harvest()
                companion, (cX, cY) = get_companion()

            if (cX, cY) not in companions:
                companions[(cX, cY)] = companion
                link[(dX, dY)] = (cX, cY)

        if num_items(Items.Hay) > 100000:
            break

        # Movement: scan the map line by line
        if dY == ws - 1:
            move(East)
        move(North)


runHayPoly()
