# Leaderboards.Dinosaur: standalone resource benchmark.
TARGET = 33488928


def _move_axis(current, target, positive, negative, ws):
    delta = (target - current) % ws
    if delta > ws // 2:
        delta -= ws
    if delta < 0:
        for _ in range(-delta):
            move(negative)
    else:
        for _ in range(delta):
            move(positive)


def _go_to(x, y, ws):
    _move_axis(get_pos_x(), x, East, West, ws)
    _move_axis(get_pos_y(), y, North, South, ws)


def _fill_even(ws):
    while True:
        for _ in range(ws - 1):
            if not move(North):
                return
        if not move(East):
            return
        for row_pair in range(ws // 2):
            for _ in range(ws - 2):
                if not move(East):
                    return
            if not move(South):
                return
            for _ in range(ws - 2):
                if not move(West):
                    return
            if row_pair < ws // 2 - 1:
                if not move(South):
                    return
        if not move(West):
            return


def run(target=TARGET):
    if num_items(Items.Bone) >= target:
        return True
    ws = get_world_size()
    if ws < 2:
        quick_print("Dinosaur benchmark: world too small")
        return False
    if ws % 2 == 1:
        ws -= 1
        set_world_size(ws)
    while num_items(Items.Bone) < target:
        _go_to(0, 0, ws)
        before = num_items(Items.Bone)
        change_hat(Hats.Dinosaur_Hat)
        _fill_even(ws)
        change_hat(Hats.Straw_Hat)
        if num_items(Items.Bone) <= before:
            quick_print("Dinosaur benchmark: no bones collected")
            return False
    return True


if __name__ == "__main__":
    run()
