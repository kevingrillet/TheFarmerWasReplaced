import resource_manager
import story_farm
import story_infinite
import story_mining
import story_mining_infinite
import story_mining_infinite_explosive
import story_mining_infinite_fast

INFINITE_MODE = "mining"  # mining / explosive / fast / resources
POWER_TARGET = 1000000  # Total stock before starting infinite; 0 skips this step.


def run():
    if INFINITE_MODE not in ["resources", "mining", "explosive", "fast"] or POWER_TARGET < 0:
        quick_print("Invalid infinite configuration", INFINITE_MODE, POWER_TARGET)
        return False
    if not story_farm.run():
        return False
    if not story_mining.run():
        return False
    if POWER_TARGET > 0 and num_items(Items.Power) < POWER_TARGET:
        quick_print("Preparing infinite Power stock", POWER_TARGET)
        if not resource_manager.farm(
            Items.Power,
            POWER_TARGET,
            num_unlocked(Unlocks.Megafarm) > 0,
            num_unlocked(Unlocks.Polyculture) > 0,
            num_unlocked(Unlocks.Trees) > 0,
        ):
            quick_print("Cannot prepare infinite Power stock", POWER_TARGET)
            return False
    if INFINITE_MODE == "mining":
        return story_mining_infinite.run()
    if INFINITE_MODE == "explosive":
        return story_mining_infinite_explosive.run()
    if INFINITE_MODE == "fast":
        return story_mining_infinite_fast.run()
    return story_infinite.run()


if __name__ == "__main__":
    run()
