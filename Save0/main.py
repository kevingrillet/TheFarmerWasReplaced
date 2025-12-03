import UDebug
import UManager
import LMWood

UDebug.reset()
hasMegafarm = num_unlocked(Unlocks.Megafarm) > 0
hasPolyculture = num_unlocked(Unlocks.Polyculture) > 0
hasTrees = num_unlocked(Unlocks.Trees) > 0
UManager.farm(Items.Power, 100000, hasMegafarm, hasPolyculture, hasTrees)
LMWood.runWood()

# import Leaderboard

# import MStory
# MStory.runUnlocksAll()
# customsMulti = [Items.Power]
# MStory.runInfinite(customsMulti)
# MStory.runInfinite()

# import Hfs
