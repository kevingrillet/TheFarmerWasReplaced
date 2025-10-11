def init(ws):
    # Initialize position to (0, 0) on a wrap-around grid of size ws x ws

    clear()
    goTo(0, 0, ws)

def goTo(xDest, yDest, ws):
    # Move to the destination (xDest, yDest) on a wrap-around grid of size ws x ws

    x = get_pos_x()
    y = get_pos_y()

    dx = (xDest - x) % ws
    if dx > ws // 2:
        dx -= ws

    dy = (yDest - y) % ws
    if dy > ws // 2:
        dy -= ws

    if dx < 0:
        for _ in range(-dx):
            move(West)
    elif dx > 0:
        for _ in range(dx):
            move(East)

    if dy < 0:
        for _ in range(-dy):
            move(South)
    elif dy > 0:
        for _ in range(dy):
            move(North)

def goToWarpless(xDest, yDest):
    # Move to the destination (xDest, yDest) on a non-wrap-around grid

    x = get_pos_x()
    y = get_pos_y()

    if xDest < x:
        for _ in range(x - xDest):
            move(West)
    elif xDest > x:
        for _ in range(xDest - x):
            move(East)

    if yDest < y:
        for _ in range(y - yDest):
            move(South)
    elif yDest > y:
        for _ in range(yDest - y):
            move(North)
