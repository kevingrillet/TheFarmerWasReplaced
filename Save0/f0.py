import resource_manager
import story_mining_infinite_fast


def _farm(i, q):
    resource_manager.farm(i, q, True, True, True)


def run():
    _farm(Items.Power, 1000000)
    _farm(Items.Bamboo, 1000000000)
    _farm(Items.Coal, 500000)

    _farm(Items.Power, 1000000)
    while True:
        story_mining_infinite_fast.run(
            None,
            [
                # "treasure",
                "pyramid",
                # "minesweeper",
                # "mushroom",
            ],
        )


if __name__ == "__main__":
    run()
