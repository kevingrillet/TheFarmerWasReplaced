import utils_farm


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
            if not move(negative_dir):
                return False
    elif delta > 0:
        for _ in range(delta):
            if not move(positive_dir):
                return False
    return True


def init(ws, do_clear=False):
    # Initialize position to (0, 0) on a grid of size ws x ws
    if ws < 1 or ws != get_world_size():
        return False
    if do_clear:
        if not utils_farm.can_start_phase():
            return False
        clear()
    return go_to(0, 0, ws)


def go_to(x_dest, y_dest, ws):
    # Move to the destination (x_dest, y_dest) on a grid of size ws x ws

    if not _move_axis(get_pos_x(), x_dest, East, West, ws):
        return False
    return _move_axis(get_pos_y(), y_dest, North, South, ws)


def go_to_yx(x_dest, y_dest, ws):
    # Move to the destination, completing Y before X.

    if not _move_axis(get_pos_y(), y_dest, North, South, ws):
        return False
    return _move_axis(get_pos_x(), x_dest, East, West, ws)


def go_to_warpless(x_dest, y_dest):
    # Plan a direct X/Y path, without using the edge wrap as a shortcut.

    if not _move_axis(get_pos_x(), x_dest, East, West):
        return False
    return _move_axis(get_pos_y(), y_dest, North, South)


def go_to_warpless_yx(x_dest, y_dest):
    # Plan a direct Y/X path, without using the edge wrap as a shortcut.

    if not _move_axis(get_pos_y(), y_dest, North, South):
        return False
    return _move_axis(get_pos_x(), x_dest, East, West)
