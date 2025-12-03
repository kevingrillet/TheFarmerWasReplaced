def _move_axis(current, target, positive_dir, negative_dir, ws=None):
    # Move along one axis (with or without warp)

    if ws != None:
        delta = (target - current) % ws
        if delta > ws // 2:
            delta -= ws
    else:
        delta = target - current

    if delta < 0:
        for _ in range(-delta):
            move(negative_dir)
    elif delta > 0:
        for _ in range(delta):
            move(positive_dir)


def init(ws, doClear=False):
    # Initialize position to (0, 0) on a grid of size ws x ws

    if doClear:
        clear()
    goTo(0, 0, ws)


def goTo(xDest, yDest, ws):
    # Move to the destination (xDest, yDest) on a grid of size ws x ws

    _move_axis(get_pos_x(), xDest, East, West, ws)
    _move_axis(get_pos_y(), yDest, North, South, ws)


def goToYX(xDest, yDest, ws):
    # Move to the destination (xDest, yDest) on a wgrid of size ws x ws

    _move_axis(get_pos_y(), yDest, North, South, ws)
    _move_axis(get_pos_x(), xDest, East, West, ws)


def goToWarpless(xDest, yDest):
    # Move to the destination (xDest, yDest) on a non-warp-around grid

    _move_axis(get_pos_x(), xDest, East, West)
    _move_axis(get_pos_y(), yDest, North, South)


def goToWarplessYX(xDest, yDest):
    # Move to the destination (xDest, yDest) on a non-warp-around grid

    _move_axis(get_pos_y(), yDest, North, South)
    _move_axis(get_pos_x(), xDest, East, West)
