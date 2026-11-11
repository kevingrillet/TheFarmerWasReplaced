# Progression producer: absolute stock targets; single/multi entry points.
import utils_farm
import utils_mine


def _neighbors_single(pos, ws):
    # Minesweeper adjacency does not wrap, even though drone movement does.
    x = pos % ws
    below, above = pos >= ws, pos < ws * (ws - 1)
    result = []
    if x > 0:
        if below:
            result.append(pos - ws - 1)
        result.append(pos - 1)
        if above:
            result.append(pos + ws - 1)
    if below:
        result.append(pos - ws)
    if above:
        result.append(pos + ws)
    if x < ws - 1:
        if below:
            result.append(pos - ws + 1)
        result.append(pos + 1)
        if above:
            result.append(pos + ws + 1)
    return result


def _cached_neighbors(cache, pos):
    if pos not in cache:
        cache[pos] = _neighbors_single(pos, cache["size"])
    return cache[pos]


def _deduce_single(clues, flags, ws):
    safe, mines = set(), set()
    constraints = []
    for pos in clues:
        unknown = set()
        remaining = clues[pos]
        for neighbor in _neighbors_single(pos, ws):
            if neighbor in flags:
                remaining -= 1
            elif neighbor not in clues:
                unknown.add(neighbor)
        if remaining < 0 or remaining > len(unknown):
            return None
        if len(unknown) == 0:
            continue
        constraints.append((unknown, remaining))
        if remaining == 0:
            for cell in unknown:
                safe.add(cell)
        elif remaining == len(unknown):
            for cell in unknown:
                mines.add(cell)
    # Subset deductions: B-A contains exactly count(B)-count(A) mines.
    if len(safe) == 0:
        for small, a in constraints:
            for large, b in constraints:
                if len(small) >= len(large):
                    continue
                subset = True
                for cell in small:
                    if cell not in large:
                        subset = False
                        break
                if not subset:
                    continue
                difference = []
                for cell in large:
                    if cell not in small:
                        difference.append(cell)
                count = b - a
                if count < 0 or count > len(difference):
                    return None
                if count == 0:
                    for cell in difference:
                        safe.add(cell)
                elif count == len(difference):
                    for cell in difference:
                        mines.add(cell)
    for cell in safe:
        if cell in mines:
            return None
    return safe, mines, constraints


def _guess_single(clues, flags, constraints, ws):
    # Incomplete information can require a guess. Prefer the lowest local risk.
    risks = {}
    for cells, count in constraints:
        risk = count / len(cells)
        for cell in cells:
            if cell not in flags and (cell not in risks or risk > risks[cell]):
                risks[cell] = risk
    best, best_risk = None, 2
    for cell in risks:
        if risks[cell] < best_risk:
            best, best_risk = cell, risks[cell]
    if best != None:
        return best
    for cell in range(ws * ws):
        if cell not in clues and cell not in flags:
            return cell
    return None


def _new_solver(ws):
    # No full-grid warm-up before the first dig; populate only visited cells.
    neighbors = {"size": ws}
    # Parent-owned: topology, active constraints, reverse index, proven facts.
    return neighbors, {}, {}, set(), set(), set()


def _update_constraint(pos, clues, flags, solver):
    neighbors, active, owners, safe, mines, deferred = solver
    if pos in active:
        old_cells, old_count = active[pos]
        for cell in old_cells:
            owners[cell].remove(pos)
            if len(owners[cell]) == 0:
                owners.pop(cell)
    unknown, remaining = set(), clues[pos]
    for cell in _cached_neighbors(neighbors, pos):
        if cell in flags:
            remaining -= 1
        elif cell not in clues:
            unknown.add(cell)
    if remaining < 0 or remaining > len(unknown):
        return False
    if len(unknown) == 0:
        if pos in active:
            active.pop(pos)
        return True
    active[pos] = unknown, remaining
    for cell in unknown:
        if cell not in owners:
            owners[cell] = set()
        owners[cell].add(pos)
    return True


def _subset_facts(small, a, large, b, safe, mines):
    if len(small) >= len(large):
        return True
    for cell in small:
        if cell not in large:
            return True
    difference = []
    for cell in large:
        if cell not in small:
            difference.append(cell)
    count = b - a
    if count < 0 or count > len(difference):
        return False
    if count == 0:
        for cell in difference:
            safe.add(cell)
    elif count == len(difference):
        for cell in difference:
            mines.add(cell)
    return True


def _deduce_incremental(clues, flags, solver, changed):
    neighbors, active, owners, safe, mines, deferred = solver
    dirty = set()
    for cell in changed:
        if cell in clues:
            if cell in mines or cell in flags:
                return None
            if cell in safe:
                safe.remove(cell)
            dirty.add(cell)
        if cell in flags:
            if cell in safe:
                return None
            if cell in mines:
                mines.remove(cell)
        for pos in _cached_neighbors(neighbors, cell):
            if pos in clues:
                dirty.add(pos)
    # Refresh only constraints incident to newly opened/flagged cells.
    for pos in dirty:
        if not _update_constraint(pos, clues, flags, solver):
            return None
        deferred.add(pos)
    for pos in dirty:
        if pos not in active:
            continue
        cells, remaining = active[pos]
        if remaining == 0:
            for cell in cells:
                safe.add(cell)
        elif remaining == len(cells):
            for cell in cells:
                mines.add(cell)
    if len(safe) == 0:
        checked = set()
        pending = []
        for pos in deferred:
            pending.append(pos)
        for pos in pending:
            deferred.remove(pos)
            if pos not in active:
                continue
            cells, count = active[pos]
            for cell in cells:
                # A nonempty subset must share a cell. Distant constraints
                # cannot help, and unchanged pairs retain their previous facts.
                for other in owners[cell]:
                    if other == pos or (pos, other) in checked:
                        continue
                    checked.add((pos, other))
                    checked.add((other, pos))
                    more, total = active[other]
                    if not _subset_facts(cells, count, more, total, safe, mines):
                        return None
                    if not _subset_facts(more, total, cells, count, safe, mines):
                        return None
    for cell in safe:
        if cell in mines:
            return None
    constraints = []
    # Risk evaluation is needed only when no proven move or new flag remains.
    if len(safe) == 0 and len(mines) == 0:
        for pos in active:
            constraints.append(active[pos])
    return safe, mines, constraints


def _reveal_single(pos, depth, ws, clues):
    if not utils_mine.go_to(pos % ws, pos // ws):
        return "blocked"
    # A shaft may reach a deep board while another column is still high above it.
    for _ in range(max(256, get_pos_z() - depth + 1)):
        if get_pos_z() <= depth:
            break
        if get_ground_type() == Grounds.Bedrock:
            return False
        before = get_pos_z()
        dig()
        if get_pos_z() >= before:
            return "blocked"
    if get_pos_z() == depth and get_ground_type() == Grounds.Dynamite:
        dig()
    if get_pos_z() != depth - 1 or get_ground_type() != Grounds.Soot:
        return False
    count = measure()
    if count == None:
        return True
    clues[pos] = count
    return None


def _puzzle_single(qty):
    if not utils_mine.seek(Grounds.Dynamite):
        return False
    depth = get_pos_z()
    ws = get_world_size()
    clues, flags = {}, set()
    solver = _new_solver(ws)
    neighbors = solver[0]
    changed = []
    pending = [get_pos_x() + get_pos_y() * ws]
    queued = {pending[0]}
    for _ in range(ws * ws * 4):
        while len(pending) > 0:
            pos = pending.pop()
            queued.remove(pos)
            if pos in clues or pos in flags:
                continue
            result = _reveal_single(pos, depth, ws, clues)
            if result != None:
                return result
            if num_items(Items.Dynamite) >= qty:
                return True
            changed.append(pos)
            if clues[pos] == 0:
                for neighbor in _cached_neighbors(neighbors, pos):
                    if (
                        neighbor not in clues
                        and neighbor not in flags
                        and neighbor not in queued
                    ):
                        pending.append(neighbor)
                        queued.add(neighbor)
        deduction = _deduce_incremental(clues, flags, solver, changed)
        if deduction == None:
            return False
        safe, mines, constraints = deduction
        old_flags = len(flags)
        changed = []
        for cell in mines:
            if cell not in flags:
                flags.add(cell)
                changed.append(cell)
        for cell in safe:
            if cell not in clues and cell not in flags:
                pending.append(cell)
                queued.add(cell)
        if len(pending) > 0 or len(flags) > old_flags:
            continue
        guess = _guess_single(clues, flags, constraints, ws)
        if guess == None:
            return False
        pending.append(guess)
        queued.add(guess)
    return False


def requirements(target_stock):
    if num_items(Items.Dynamite) >= target_stock:
        return {}
    if num_unlocked(Unlocks.Dynamite) == 0:
        return None
    return {}


def produce_single(target_stock):
    if num_items(Items.Dynamite) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock)) or not utils_mine.prepare():
        return False
    result = _puzzle_single(target_stock)
    # An exploded/unsolved puzzle is an expected attempt, with possible partial yield.
    return result != "blocked"


def farm_single(target_stock):
    stalled = 0
    while num_items(Items.Dynamite) < target_stock:
        before = num_items(Items.Dynamite)
        if not produce_single(target_stock):
            return False
        if num_items(Items.Dynamite) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Dynamite)
                return False
        else:
            stalled = 0
    return True


def _approach_sector(qty, sector, depth, budget):
    for _ in range(256):
        if num_items(Items.Dynamite) >= qty or get_pos_z() <= depth:
            return True
        if (
            get_ground_type() == Grounds.Dynamite
            or get_ground_type() == Grounds.Bedrock
        ):
            return True
        dig()
    return False


def _reveal_worker(cells, qty, depth, ws):
    discovered = {}
    for pos in cells:
        if num_items(Items.Dynamite) >= qty:
            return True, discovered
        result = _reveal_single(pos, depth, ws, discovered)
        if result != None:
            return result, discovered
    return None, discovered


def _reveal_batch_multi(cells, qty, depth, ws, clues, changed=None):
    count = min(max_drones(), len(cells))
    if count < 1:
        return None
    handles = []
    results = []
    for index in range(count):
        group = []
        for offset in range(
            index * len(cells) // count, (index + 1) * len(cells) // count
        ):
            group.append(cells[offset])
        handle = None
        if index < count - 1:
            handle = spawn_drone(_reveal_worker, group, qty, depth, ws)
        if handle == None:
            result = _reveal_worker(group, qty, depth, ws)
            results.append(result)
            if result[0] != None:
                break
        else:
            handles.append(handle)
    # The parent alone merges copied results and makes new deductions/guesses.
    for handle in handles:
        results.append(wait_for(handle))
    state = None
    for result, discovered in results:
        for pos in discovered:
            if changed != None and pos not in clues:
                changed.append(pos)
            clues[pos] = discovered[pos]
        if result == "blocked":
            state = "blocked"
        elif result != None and state != "blocked":
            state = result
    return state


def _puzzle_multi(qty):
    if not utils_mine.seek(Grounds.Dynamite):
        return False
    depth = get_pos_z()
    ws = get_world_size()
    first = get_pos_x() + get_pos_y() * ws
    sectors = utils_mine.sector_plan(True)
    if not utils_mine.run_sectors(
        _approach_sector, Items.Dynamite, qty, sectors, depth
    ):
        return "blocked"
    clues, flags = {}, set()
    solver = _new_solver(ws)
    changed = []
    pending = [first]
    for _ in range(ws * ws * 4):
        cells, queued = [], set()
        for pos in pending:
            if pos not in clues and pos not in flags and pos not in queued:
                cells.append(pos)
                queued.add(pos)
        if len(cells) > 0:
            result = _reveal_batch_multi(cells, qty, depth, ws, clues, changed)
            if result != None:
                return result
        if num_items(Items.Dynamite) >= qty:
            return True
        deduction = _deduce_incremental(clues, flags, solver, changed)
        if deduction == None:
            return False
        safe, mines, constraints = deduction
        old_flags = len(flags)
        changed = []
        for pos in mines:
            if pos not in flags:
                flags.add(pos)
                changed.append(pos)
        pending = []
        for pos in safe:
            if pos not in clues and pos not in flags:
                pending.append(pos)
        if len(pending) > 0 or len(flags) > old_flags:
            continue
        guess = _guess_single(clues, flags, constraints, ws)
        if guess == None:
            return False
        # A guess is always alone; only proven-safe cells run concurrently.
        pending.append(guess)
    return False


def solve_current_puzzle(parallel=True):
    # Solve the existing board completely, without resetting its terrain.
    if not utils_farm.can_start_phase() or num_unlocked(Unlocks.Dynamite) == 0:
        return "blocked"
    if get_ground_type() != Grounds.Dynamite:
        return "blocked"
    target = num_items(Items.Dynamite) + 10**30
    if parallel:
        return _puzzle_multi(target)
    return _puzzle_single(target)


def produce_multi(target_stock):
    if num_items(Items.Dynamite) >= target_stock:
        return True
    if not utils_farm.preflight(requirements(target_stock), True):
        return False
    if num_unlocked(Unlocks.Underground_Senses) == 0 or not utils_mine.prepare():
        return False
    return _puzzle_multi(target_stock) != "blocked"


def farm_multi(target_stock):
    stalled = 0
    while num_items(Items.Dynamite) < target_stock:
        before = num_items(Items.Dynamite)
        if not produce_multi(target_stock):
            return False
        if num_items(Items.Dynamite) <= before:
            stalled += 1
            if stalled >= 8:
                quick_print("Production made no progress", Items.Dynamite)
                return False
        else:
            stalled = 0
    return True
