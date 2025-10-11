import UFarm
import UManager
import UMove

def innerFarmPower(ws):
    # Plant and harvest sunflowers in a systematic way

    def _plant(ws):
        # Plant sunflowers across the grid and group them by petal count
        petals={}
        for i in range(7, 15+1):
            petals[i]=[]

        for x in range(ws):
            for y in range(ws):
                UMove.goTo(x, y, ws)
                UFarm.qHarvest()
                UFarm.qTill()
                UFarm.water()
                plant(Entities.Sunflower)
                petals[measure()].append((x, y))
        return petals

    def _harvest(petals, ws):
        # Harvest sunflowers starting from the ones with most petals
        while len(petals) > 0:
            best = max(petals)
            for sunflower in petals[best]:
                x, y = sunflower
                UMove.goTo(x, y, ws)
                if UFarm.qHarvest():
                    petals[best].remove((x, y))
                else:
                    UFarm.fertilizerOrWater()

            if len(petals[best]) == 0:
                petals.pop(best)

    _harvest(_plant(ws), ws)

def farmPower(qty):
    # Generate power by growing and harvesting sunflowers

    UManager.checkRequirement(Entities.Sunflower, qty)
    ws = get_world_size()
    UMove.init(ws)
    while num_items(Items.Power) < qty:
        innerFarmPower(ws)
