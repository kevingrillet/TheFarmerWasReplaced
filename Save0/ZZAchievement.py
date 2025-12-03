def droneFlip():
    # Fashion Show
    hats = [Hats.Brown_Hat, Hats.Gray_Hat, Hats.Green_Hat, Hats.Purple_Hat]
    change_hat(hats[(get_pos_x() + get_pos_y()) % len(hats) - 1])

    # Acrobat, Master Acrobat
    for _ in range(40):
        do_a_flip()


def hfs():
    clear()
    while get_pos_x() != 0:
        move(East)
    while get_pos_y() != 0:
        move(North)

    drones = []
    for _ in range(32):
        # Megafarm, Higher-Order Programming,
        drones.append(spawn_drone(droneFlip))
        move(East)

    # Feels Good
    pet_the_piggy()

    # Healer
    use_item(Items.Weird_Substance)
    move(North)
    use_item(Items.Weird_Substance)

    while num_drones() > 1:
        do_a_flip()
    move(South)


def recycling():
    ws = 5
    nb_drones = ws**2
    substance = get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
    times_reused = 0
    drones = []

    def gen():
        global substance
        plant(Entities.Bush)
        use_item(Items.Weird_Substance, substance)

    def maze():
        global times_reused
        while True:
            if num_drones() == 25:
                if get_entity_type() == Entities.Treasure:
                    if times_reused >= 300:
                        times_reused = 0
                        harvest()
                        gen()
                    else:
                        use_item(Items.Weird_Substance, substance)
                        times_reused += 1

    clear()
    set_world_size(ws)

    while get_pos_x() != 0:
        move(East)
    while get_pos_y() != 0:
        move(North)

    while num_drones() <= nb_drones:
        if (get_pos_x(), get_pos_y()) not in drones:
            spawn_drone(maze)
            drones.append((get_pos_x(), get_pos_y()))
            move(North)
        else:
            move(East)
    gen()


def stackOverflow():
    stackOverflow()


def wrongOrder():
    def plantAll():
        do_a_flip()
        for x in range(3):
            for y in range(3):
                if can_harvest():
                    harvest()
                    harvest()
                till()
                plant(Entities.Cactus)
                move(North)
            move(East)
        do_a_flip()
        do_a_flip()
        do_a_flip()

    def sortCols():
        move(North)
        for x in range(3):
            swapping = True
            while swapping:
                swapping = False
                if measure() < measure(North):
                    swapping = True
                    swap(North)
                if measure() > measure(South):
                    swapping = True
                    swap(South)
            move(East)
        move(South)

    def sortRows():
        move(East)
        for y in range(3):
            swapping = True
            while swapping:
                swapping = False
                if measure() < measure(East):
                    swapping = True
                    swap(East)
                if measure() > measure(West):
                    swapping = True
                    swap(West)
            move(North)
        move(West)

    clear()
    set_world_size(3)
    while get_pos_x() != 0:
        move(East)
    while get_pos_y() != 0:
        move(North)

    plantAll()
    sortCols()
    sortRows()
    harvest()
