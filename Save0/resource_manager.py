import utils_debug


def farm(item, qty, has_megafarm, has_polyculture, has_trees, debug=False, trail=None):
    # Absolute goal. Dependency work is complete before a funded phase starts.
    if num_items(item) >= qty:
        return True
    if trail == None:
        trail = []
    if item in trail:
        quick_print("Cyclic production requirements", trail, item)
        return False
    trail = trail + [item]
    if debug:
        quick_print("To farm", qty, item)
        utils_debug.print_storage()
    stalled = 0
    while num_items(item) < qty:
        before = num_items(item)
        if item == Items.Hay:
            if has_polyculture:
                import farm_polyculture

                entity = Entities.Grass
                needs = farm_polyculture.requirements(entity, qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_polyculture.produce_multi(entity, qty)
                else:
                    result = farm_polyculture.produce_single(entity, qty)
            else:
                import farm_hay

                needs = farm_hay.requirements(qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_hay.farm_multi(qty)
                else:
                    result = farm_hay.farm_single(qty)
        elif item == Items.Wood:
            if has_polyculture:
                import farm_polyculture

                entity = Entities.Tree
                if not has_trees:
                    entity = Entities.Bush
                needs = farm_polyculture.requirements(entity, qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_polyculture.produce_multi(entity, qty)
                else:
                    result = farm_polyculture.produce_single(entity, qty)
            else:
                import farm_wood

                needs = farm_wood.requirements(qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_wood.farm_multi(qty)
                else:
                    result = farm_wood.farm_single(qty, has_trees)
        elif item == Items.Carrot:
            if has_polyculture:
                import farm_polyculture

                entity = Entities.Carrot
                needs = farm_polyculture.requirements(entity, qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_polyculture.produce_multi(entity, qty)
                else:
                    result = farm_polyculture.produce_single(entity, qty)
            else:
                import farm_carrot

                needs = farm_carrot.requirements(qty)
                if not _fund_requirements(
                    needs, has_megafarm, has_polyculture, has_trees, debug, trail
                ):
                    return False
                if has_megafarm:
                    result = farm_carrot.farm_multi(qty)
                else:
                    result = farm_carrot.farm_single(qty)
        elif item == Items.Pumpkin:
            import farm_pumpkin

            needs = farm_pumpkin.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_pumpkin.produce_multi(qty)
            else:
                result = farm_pumpkin.produce_single(qty)
        elif item == Items.Cactus:
            import farm_cactus

            needs = farm_cactus.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_cactus.produce_multi(qty)
            else:
                result = farm_cactus.produce_single(qty)
        elif item == Items.Power:
            import farm_power

            needs = farm_power.requirements(qty, has_megafarm)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_power.produce_multi(qty)
            else:
                result = farm_power.produce_single(qty)
        elif item == Items.Gold:
            import farm_gold

            needs = farm_gold.requirements(qty, has_megafarm)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_gold.produce_multi(qty)
            else:
                result = farm_gold.produce_single(qty)
        elif item == Items.Bone:
            import farm_bone

            needs = farm_bone.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            result = farm_bone.produce_single(qty)
        elif item == Items.Weird_Substance:
            import farm_pumpkin

            needs = farm_pumpkin.goo_requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_pumpkin.produce_goo_multi(qty)
            else:
                result = farm_pumpkin.produce_goo_single(qty)
        elif item == Items.Block:
            if num_unlocked(Unlocks.Mining) == 0:
                return False
            import mine_block

            needs = mine_block.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = mine_block.produce_multi(qty)
            else:
                result = mine_block.produce_single(qty)
        elif item == Items.Rice:
            if num_unlocked(Unlocks.Rice) == 0:
                return False
            import farm_rice

            needs = farm_rice.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_rice.produce_multi(qty)
            else:
                result = farm_rice.produce_single(qty)
        elif item == Items.Bamboo:
            if num_unlocked(Unlocks.Bamboo) == 0:
                return False
            import farm_bamboo

            needs = farm_bamboo.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_bamboo.produce_multi(qty)
            else:
                result = farm_bamboo.produce_single(qty)
        elif item == Items.Coal:
            if num_unlocked(Unlocks.Coal) == 0:
                return False
            import mine_coal

            needs = mine_coal.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = mine_coal.produce_multi(qty)
            else:
                result = mine_coal.produce_single(qty)
        elif item == Items.Iron:
            if num_unlocked(Unlocks.Iron) == 0:
                return False
            import mine_iron

            needs = mine_iron.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = mine_iron.produce_multi(qty)
            else:
                result = mine_iron.produce_single(qty)
        elif item == Items.Quartz:
            if num_unlocked(Unlocks.Quartz) == 0:
                return False
            import mine_quartz

            needs = mine_quartz.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = mine_quartz.produce_multi(qty)
            else:
                result = mine_quartz.produce_single(qty)
        elif item == Items.Mushroom:
            if num_unlocked(Unlocks.Mushrooms) == 0:
                return False
            import farm_mushroom

            needs = farm_mushroom.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = farm_mushroom.produce_multi(qty)
            else:
                result = farm_mushroom.produce_single(qty)
        elif item == Items.Dynamite:
            if num_unlocked(Unlocks.Dynamite) == 0:
                return False
            import mine_dynamite

            needs = mine_dynamite.requirements(qty)
            if not _fund_requirements(
                needs, has_megafarm, has_polyculture, has_trees, debug, trail
            ):
                return False
            if has_megafarm:
                result = mine_dynamite.produce_multi(qty)
            else:
                result = mine_dynamite.produce_single(qty)
        elif item == Items.Fertilizer:
            result = _wait_passive(item, qty, Unlocks.Fertilizer)
        elif item == Items.Water:
            result = _wait_passive(item, qty, Unlocks.Watering)
        else:
            quick_print("Unsupported resource", item)
            return False
        # None is never a successful producer result.
        if not result:
            quick_print("Production phase failed", item, qty)
            return False
        if num_items(item) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", item, qty)
                return False
        else:
            stalled = 0
    if debug:
        quick_print("Farmed", qty, item)
        utils_debug.print_storage()
    return True


def farm_current(item, qty):
    return farm(
        item,
        qty,
        num_unlocked(Unlocks.Megafarm) > 0,
        num_unlocked(Unlocks.Polyculture) > 0,
        num_unlocked(Unlocks.Trees) > 0,
    )


def _fund_requirements(
    needs, has_megafarm, has_polyculture, has_trees, debug=False, trail=None
):
    if needs == None:
        quick_print("Production requirements unavailable")
        return False
    for _ in range(8):
        for item in needs:
            if not farm(
                item,
                needs[item],
                has_megafarm,
                has_polyculture,
                has_trees,
                debug,
                trail,
            ):
                quick_print("Cannot fund resource", item, needs[item])
                return False
        ready = True
        for item in needs:
            if num_items(item) < needs[item]:
                ready = False
                break
        if ready:
            return True
    quick_print("Cannot retain all production ingredients")
    return False


def _wait_passive(item, qty, skill):
    if num_unlocked(skill) == 0:
        return False
    timed = num_unlocked(Unlocks.Timing) > 0
    deadline = 0
    if timed:
        deadline = get_time() + 180
    previous = num_items(item)
    idle = 0
    while num_items(item) < qty:
        current = num_items(item)
        if current > previous:
            idle = 0
            previous = current
            if timed:
                deadline = get_time() + 180
        else:
            idle += 1
            if timed:
                if get_time() > deadline:
                    return False
            elif idle > 262144:
                return False
    return True


def get_skill(t, has_megafarm, has_polyculture, has_trees, level, skill):
    # Unlock the specified skill to the desired level

    lt = get_time()
    curr = num_unlocked(skill)
    while curr < level:
        cost = get_cost(skill)
        if len(cost) == 0:
            quick_print("Upgrade level unavailable", skill, level)
            return False
        if not _fund_requirements(cost, has_megafarm, has_polyculture, has_trees):
            quick_print("Cannot fund upgrade", skill, level)
            return False
        if not unlock(skill):
            quick_print("Upgrade refused", skill, level)
            return False
        et = get_time()
        previous = curr
        curr = num_unlocked(skill)
        if curr <= previous:
            quick_print("Upgrade made no progress", skill, level)
            return False
        quick_print(skill, "LVL", curr, "Completion", et - lt, "Global", et - t)
        utils_debug.print_storage()
    return True
