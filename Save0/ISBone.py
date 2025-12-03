import UManager
import UMove


def _chkApple(tailSize):
    # Increase tail length if current entity is an apple

    if get_entity_type() == Entities.Apple:
        tailSize += 1
    return tailSize


def _chkAppleAndMove(tailSize, direction):
    # Check apple and move in the given direction

    tailSize = _chkApple(tailSize)
    move(direction)
    return tailSize


def innerfarmDumb(ws):
    # Simple bone farming loop with basic movement pattern

    tail = 0
    change_hat(Hats.Dinosaur_Hat)
    while tail < ws**2 - 1:
        x, y = measure()
        UMove.goToWarpless(x, y)
        newTail = _chkApple(tail)
        if tail == newTail:
            break
        tail = newTail
    change_hat(Hats.Straw_Hat)


def innerfarmZZ(ws):
    # Zigzag pattern for even-sized worlds to maximize apple collection (Hamiltonian cycle)

    tail = 0
    change_hat(Hats.Dinosaur_Hat)
    while tail < ws**2 - 1:
        for _ in range(ws - 1):
            tail = _chkAppleAndMove(tail, North)
        tail = _chkAppleAndMove(tail, East)
        for _ in range(ws / 2):
            for _ in range(ws - 2):
                tail = _chkAppleAndMove(tail, East)
            tail = _chkAppleAndMove(tail, South)
            for _ in range(ws - 2):
                tail = _chkAppleAndMove(tail, West)
            tail = _chkAppleAndMove(tail, South)
        tail = _chkAppleAndMove(tail, West)
    change_hat(Hats.Straw_Hat)


def innerfarmZZV2(ws):
    # Zigzag pattern for even-sized worlds to maximize apple collection (Hamiltonian cycle)
    # No tail check, just a full scan

    change_hat(Hats.Dinosaur_Hat)
    while True:
        for _ in range(ws - 1):
            if not move(North):
                break
        if not move(East):
            break
        for _ in range(ws / 2):
            for _ in range(ws - 2):
                if not move(East):
                    break
            if not move(South):
                break
            for _ in range(ws - 2):
                if not move(West):
                    break
            if not move(South):
                break
        if not move(West):
            break
    change_hat(Hats.Straw_Hat)


def farm(qty, checkRequirement=True):
    # Main function to farm bones until the required quantity is reached

    if checkRequirement:
        UManager.checkRequirement(Entities.Dinosaur, qty)
    ws = get_world_size()
    UMove.init(ws)
    if ws % 2 == 0:
        while num_items(Items.Bone) < qty:
            innerfarmZZV2(ws)
    else:
        if num_unlocked(Unlocks.Auto_Unlock):
            ws -= 1
            set_world_size(ws)
            while num_items(Items.Bone) < qty:
                innerfarmZZV2(ws)
        else:
            while num_items(Items.Bone) < qty:
                innerfarmDumb(ws)
