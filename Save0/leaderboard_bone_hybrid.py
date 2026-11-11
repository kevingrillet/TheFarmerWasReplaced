# Leaderboards.Dinosaur: candidate adapted from cheese_dino.py.
# Chase safe apples along alternating edges, then finish on a Hamiltonian cycle.
TARGET = 33488928

# Private single-drone state, reinitialized for every tail (not shared workers).
_apple = None
_occupied = 1
_blocked_up = {}
_blocked_down = {}


def _step(direction):
    global _apple
    global _occupied
    if not move(direction):
        return False
    if (get_pos_x(), get_pos_y()) == _apple:
        _apple = measure()
        _occupied += 1
    return True


def _column(target, track=True):
    current = get_pos_x()
    direction = East
    if target < current:
        direction = West
    for _ in range(abs(target - current)):
        if track:
            if not _step(direction):
                return False
        elif not move(direction):
            return False
    return True


def _row(target, track=True):
    current = get_pos_y()
    direction = North
    if target < current:
        direction = South
    for _ in range(abs(target - current)):
        if track:
            if not _step(direction):
                return False
        elif not move(direction):
            return False
    return True


def _stage_up(ws):
    global _blocked_up
    x, y = _apple
    if y == 0 or x == 0 or x == ws - 1 or (x in _blocked_up and y <= _blocked_up[x]):
        if not _column(ws - 1) or not _row(0):
            return 0
        _blocked_up = {}
        return 2
    column = x
    if x % 2 == 0:
        column -= 1
    if column <= get_pos_x():
        if not _column(ws - 1) or not _row(0):
            return 0
        _blocked_up = {}
        return 2
    if not _column(column) or not _row(y):
        return 0
    _blocked_down[column] = y
    _blocked_down[column + 1] = y
    if not _step(East) or not _row(ws - 1):
        return 0
    return 1


def _stage_down(ws):
    global _blocked_down
    x, y = _apple
    if (
        y == ws - 1
        or x == 0
        or x == ws - 1
        or (x in _blocked_down and y >= _blocked_down[x])
    ):
        if not _column(0) or not _row(ws - 1):
            return 0
        _blocked_down = {}
        return 1
    column = x
    if x % 2 == 1:
        column += 1
    if column >= get_pos_x():
        if not _column(0) or not _row(ws - 1):
            return 0
        _blocked_down = {}
        return 1
    if not _column(column) or not _row(y):
        return 0
    _blocked_up[column] = y
    _blocked_up[column - 1] = y
    if not _step(West) or not _row(0):
        return 0
    return 2


def _enter_cycle(ws):
    if not _column(0, False) or not _row(ws - 1, False):
        return False
    for x in range(ws):
        y = ws - 1
        if x % 2 == 1:
            y = 1
            if x in _blocked_up:
                y = _blocked_up[x] + 1
        if not _row(y, False):
            return False
        # The original attempts to leave the field at the rightmost edge.
        if x < ws - 1 and not move(East):
            return False
    return _row(0, False) and _column(0, False)


def _cycle(ws):
    # Each complete cycle visits every tile and must find the next apple.
    for _ in range(ws * ws + 1):
        for pair in range(ws // 2):
            if not _row(ws - 1, False) or not move(East) or not _row(1, False):
                return True
            if pair < ws // 2 - 1 and not move(East):
                return True
        if not _row(0, False) or not _column(0, False):
            return True
    return False


def _grow(ws):
    global _apple
    global _occupied
    global _blocked_up
    global _blocked_down
    _apple = measure()
    _occupied = 1
    _blocked_up = {}
    _blocked_down = {}
    if _apple == None:
        return False
    # On a 4x4 field the aggressive turns leave too little room for transition.
    if ws == 4:
        return _cycle(ws)
    if not _row(ws - 1):
        return False
    stage = 1
    for _ in range(ws * ws * 4):
        if _apple == None:
            return False
        if stage == 1:
            stage = _stage_up(ws)
        else:
            stage = _stage_down(ws)
            if stage == 1 and _occupied > 4 * (ws - 1) - 4:
                if not _enter_cycle(ws):
                    return False
                return _cycle(ws)
        if stage == 0:
            return False
    return False


def run(target=TARGET):
    if num_items(Items.Bone) >= target:
        return True
    if num_drones() != 1:
        return False
    ws = get_world_size()
    if ws < 4:
        quick_print("Dinosaur hybrid: an even field of at least 4x4 is required")
        return False
    if ws % 2 == 1:
        ws -= 1
        set_world_size(ws)
        if get_world_size() != ws:
            return False
    while num_items(Items.Bone) < target:
        clear()
        before = num_items(Items.Bone)
        change_hat(Hats.Dinosaur_Hat)
        success = _grow(ws)
        # Cleanup also runs on failed movement or missing apples.
        change_hat(Hats.Straw_Hat)
        if not success or num_items(Items.Bone) <= before:
            quick_print("Dinosaur hybrid: incomplete tail or no bones collected")
            return False
    return True


if __name__ == "__main__":
    run()
