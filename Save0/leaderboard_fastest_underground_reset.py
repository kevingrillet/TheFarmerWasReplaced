import leaderboard_fastest_reset
import story_mining


def run():
    if not leaderboard_fastest_reset.run():
        return False
    return story_mining.run(True)


if __name__ == "__main__":
    run()
