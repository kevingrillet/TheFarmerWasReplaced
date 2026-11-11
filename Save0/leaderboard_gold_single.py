# Leaderboards.Maze_Single: self-contained wall following in fresh mazes.
TARGET = 616448


def _directions(looking):
    if looking == North:
        return [West, North, East, South]
    elif looking == East:
        return [North, East, South, West]
    elif looking == South:
        return [East, South, West, North]
    return [South, West, North, East]


def run(target=TARGET):
    if num_items(Items.Gold) >= target:
        return True
    ws = get_world_size()
    substance = ws * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
    while num_items(Items.Gold) < target:
        clear()
        if not plant(Entities.Bush) or not use_item(Items.Weird_Substance, substance):
            quick_print("Maze benchmark: creation failed")
            return False
        looking = North
        steps = 0
        while get_entity_type() != Entities.Treasure:
            moved = False
            for direction in _directions(looking):
                if move(direction):
                    looking = direction
                    moved = True
                    break
            steps += 1
            if not moved or steps > 4 * ws * ws:
                quick_print("Maze benchmark: treasure not reached")
                return False
        harvest()
    return True


if __name__ == "__main__":
    run()
