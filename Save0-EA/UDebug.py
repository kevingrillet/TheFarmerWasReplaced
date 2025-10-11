def printUnlocks():
    lvls={}
    for unlock in Unlocks:
        lvls[unlock]=num_unlocked(unlock)
    quick_print(lvls)

def printStorage():
    storage={}
    for item in Items:
        storage[item]=num_items(item)
    quick_print(storage)
