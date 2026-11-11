import utils_farm
import utils_move


def requirements(target_stock):
    if num_items(Items.Bone) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Dinosaurs) == 0 or get_world_size() < 2:
        return None
    ws = get_world_size()
    ws -= ws % 2
    # A complete tail uses at most area apples, including the initially placed one.
    # get_cost(Apple) already includes the Dinosaur upgrade multiplier.
    return utils_farm.seed_requirements(Entities.Apple, ws * ws)


def _fill_even(ws):
    # At most area cycles to fill the tail. False move means a normal collision.
    for _ in range(ws * ws + 1):
        for _ in range(ws - 1):
            if not move(North):
                return True
        if not move(East):
            return True
        for row_pair in range(ws // 2):
            for _ in range(ws - 2):
                if not move(East):
                    return True
            if not move(South):
                return True
            for _ in range(ws - 2):
                if not move(West):
                    return True
            if row_pair < ws // 2 - 1 and not move(South):
                return True
        if not move(West):
            return True
    quick_print("Dinosaur tail did not fill")
    return False


def produce_single(target_stock):
    if num_items(Items.Bone) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock)):
        return False
    ws = get_world_size()
    if ws % 2 == 1:
        ws -= 1
        set_world_size(ws)
    clear()
    change_hat(Hats.Dinosaur_Hat)
    success = _fill_even(ws)
    change_hat(Hats.Straw_Hat)
    if not success:
        return False
    return utils_move.go_to(0, 0, ws)


def farm_single(target_stock):
    while num_items(Items.Bone) < target_stock:
        before = num_items(Items.Bone)
        if not produce_single(target_stock):
            return False
        if num_items(Items.Bone) <= before:
            quick_print("No bones collected")
            return False
    return True
