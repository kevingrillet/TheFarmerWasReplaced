"""Mushroom strata and changing-source regressions, not a native scheduler."""

import importlib
import random
import unittest
from collections import deque
from contextlib import contextmanager
from unittest.mock import patch

from test_mining_multi import MiningField

mushroom = importlib.import_module("farm_mushroom")


class StrataField(MiningField):
    """Native push heights and one reward per matching pair.

    Six kinds with no vertical repeats, plus stability-based cave-ins. Worker
    scheduling and action durations remain simplified; this is not the engine.
    """

    def __init__(
        self, top=2, height=8, rows=None, fall=False, seed=0, caveins=True, **kwargs
    ):
        super().__init__(resource="Mushroom", **kwargs)
        self.top, self.height, self.rows = top, height, rows
        self.fall = fall
        self.fallen = False
        self.waiting_source = None
        self.placed, self.pushes, self.seen_rows = {}, [], set()
        self.caveins = caveins
        self.kinds = {}
        self.first_push_depths = None
        self.losses = 0
        self.visits = []
        rng = random.Random(seed)
        for x in range(self.ws):
            for y in range(self.ws):
                previous = -1
                for depth in range(top, top + height):
                    kind = rng.randrange(6)
                    while kind == previous:
                        kind = rng.randrange(6)
                    self.kinds[x, y, depth] = previous = kind

    def clear(self):
        super().clear()
        self.placed.clear()
        self.waiting_source = None

    def block(self, pos, depth):
        if (pos, depth) in self.placed:
            return "Mushroom", self.placed[pos, depth]
        if self.rows is None or pos[1] in self.rows:
            if self.top <= depth < self.top + self.height:
                return "Mushroom", self.kinds[*pos, depth]
        return (
            ("Rock", None) if depth < self.top + self.height + 4 else ("Bedrock", None)
        )

    def ground(self, direction=None):
        x, y = self.pos()
        if direction:
            dx, dy = {
                "North": (0, 1),
                "East": (1, 0),
                "South": (0, -1),
                "West": (-1, 0),
            }[direction]
            x, y = (x + dx) % self.ws, (y + dy) % self.ws
        pos = x, y
        return self.block(pos, self.depths.get(pos, 0))[0]

    def move(self, direction):
        old, depth = self.pos(), -self.z()
        if self.ground() == "Mushroom":
            self.waiting_source = old, depth
        return super().move(direction)

    def dig(self):
        self.seen_rows.add(self.y)
        super().dig()
        if self.caveins:
            self.collapse(self.pos())
        if self.fall and not self.fallen and self.waiting_source:
            pos, depth = self.waiting_source
            if pos != self.pos():
                self.depths[pos] = depth + 4
                self.fallen = True

    def neighbors(self, pos):
        x, y = pos
        return [
            (x + dx, y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx or dy) and 0 <= x + dx < self.ws and 0 <= y + dy < self.ws
        ]

    def clear_to(self, pos, depth):
        old = self.depths.get(pos, 0)
        if depth > old:
            self.losses += sum(
                self.block(pos, d)[0] == "Mushroom" for d in range(old, depth)
            )
            self.depths[pos] = depth

    def collapse(self, origin):
        depth = self.depths[origin]
        for pos in self.neighbors(origin):
            if sum(abs(a - b) for a, b in zip(pos, origin)) == 1:
                if self.block(pos, self.depths.get(pos, 0))[0] == "Rock":
                    self.clear_to(pos, depth - 1)
        # Propagate the stability rule to a fixed point; no wrap at world edges.
        queue = deque(self.neighbors(origin))
        while queue:
            pos = queue.popleft()
            neighbors = self.neighbors(pos)
            deepest = max(self.depths.get(p, 0) for p in neighbors)
            for d in range(deepest - 1, self.depths.get(pos, 0) - 1, -1):
                stability = 10**9 if self.block(pos, d)[0] == "Bedrock" else 3
                if stability < deepest - d:
                    self.clear_to(pos, d + 1)
                    queue.extend(neighbors)
                    break

    def measure(self, direction=None):
        pos = self.pos()
        if direction:
            dx, dy = {
                "North": (0, 1),
                "East": (1, 0),
                "South": (0, -1),
                "West": (-1, 0),
            }[direction]
            pos = (pos[0] + dx) % self.ws, (pos[1] + dy) % self.ws
        self.visits.append((pos, direction))
        return self.block(pos, self.depths.get(pos, 0))[1]

    def can_push(self, direction):
        x, y = self.pos()
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        target = (x + dx) % self.ws, (y + dy) % self.ws
        return self.ground() == "Mushroom" and self.depths.get(target, 0) > -self.z()

    def push(self, direction):
        self.budget()
        if self.first_push_depths is None:
            self.first_push_depths = dict(self.depths)
        if not self.can_push(direction):
            return False
        origin, depth = self.pos(), -self.z()
        kind = self.block(origin, depth)[1]
        # A push does not move the drone.
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        target = (self.x + dx) % self.ws, (self.y + dy) % self.ws
        td = self.depths.get(target, 0)
        below, other = self.block(target, td)
        self.depths[origin] = depth + 1
        self.placed.pop((origin, depth), None)
        if below == "Mushroom" and kind == other:
            self.depths[target] = td + 1
            self.placed.pop((target, td), None)
            self.stock["Mushroom"] += 1
        else:
            self.depths[target] = td - 1
            self.placed[target, td - 1] = kind
        self.pushes.append((origin, target))
        return True

    @contextmanager
    def native(self, **overrides):
        bindings = dict(
            push=self.push,
            can_push=self.can_push,
            measure=self.measure,
        )
        bindings.update(overrides)
        with self.api(mushroom, **bindings):
            yield


class MushroomTests(unittest.TestCase):
    def test_full_layer_is_prepared_before_first_push_with_six_random_kinds(self):
        for parallel in (False, True):
            for seed in range(5):
                with self.subTest(parallel=parallel, seed=seed):
                    field = StrataField(ws=8, capacity=4, top=60, seed=seed)
                    with field.native():
                        result = (
                            mushroom.produce_multi(100)
                            if parallel
                            else mushroom.produce_single(100)
                        )
                    self.assertTrue(result)
                    self.assertGreaterEqual(field.stock["Mushroom"], 100)
                    self.assertEqual(field.worlds, 1)
                    self.assertIsNotNone(field.first_push_depths)
                    for x in range(field.ws):
                        for y in range(field.ws):
                            self.assertGreaterEqual(
                                field.first_push_depths.get((x, y), 0), field.top
                            )
                    self.assertEqual(field.losses, 0)
                    self.assertEqual(field.spawned, field.joined)

    def test_matching_checks_each_direction_without_excavating_or_following(self):
        for direction, offset in (
            ("East", (1, 0)),
            ("North", (0, 1)),
            ("West", (-1, 0)),
            ("South", (0, -1)),
        ):
            with self.subTest(direction=direction):
                field = StrataField(ws=3, capacity=1)
                field.x = field.y = 1
                field.depths = {(x, y): 2 for x in range(3) for y in range(3)}
                target = 1 + offset[0], 1 + offset[1]
                field.depths[target] = 3
                field.kinds[1, 1, 2] = field.kinds[*target, 3] = 4
                with field.native():
                    self.assertTrue(mushroom._visit(1, 1, 1, (0, 0, 3, 3), 0))
                self.assertEqual(field.pushes, [((1, 1), target)])
                self.assertEqual(field.stock["Mushroom"], 1)
                self.assertEqual(field.pos(), (1, 1))
                self.assertFalse(field.digs)

    def test_collection_covers_rows_and_columns_and_does_not_dig_under_pushes(self):
        field = StrataField(ws=8, capacity=4)
        visits = []
        original = mushroom._visit

        def visit(qty, x, y, sector, turn):
            visits.append((x, y, turn))
            return original(qty, x, y, sector, turn)

        with field.native(), patch.object(mushroom, "_visit", side_effect=visit):
            self.assertTrue(mushroom.produce_multi(100000))
        expected = {(x, y) for x in range(8) for y in range(8)}
        for turn in (0, 1, 2, 3):
            self.assertEqual({(x, y) for x, y, t in visits if t == turn}, expected)
        self.assertLess(max(t for _, _, t in visits), mushroom._PASS_LIMIT)
        # One sacrificial mushroom per sector; the rest are paired, not drilled.
        self.assertEqual(sum(g == "Mushroom" for _, g in field.digs), 4)
        self.assertGreater(field.stock["Mushroom"], 150)
        self.assertEqual(field.spawned, field.joined)

    def test_preparation_failure_joins_workers_before_reporting_failure(self):
        field = StrataField(ws=8, capacity=4, top=60)
        dig = field.dig

        def fail_child():
            if not field.in_worker:
                dig()

        with field.native(dig=fail_child):
            self.assertFalse(mushroom.produce_multi(100))
        self.assertTrue(field.spawned)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pushes)
        self.assertFalse(field.pending)

    def test_single_recovers_after_source_falls_or_disappears(self):
        for height in (4, 8):
            with self.subTest(height=height):
                field = StrataField(ws=8, capacity=1, height=height, fall=True)
                with field.native():
                    self.assertTrue(mushroom.farm_single(6))
                self.assertTrue(field.fallen)
                self.assertGreaterEqual(field.stock["Mushroom"], 6)

    def test_multi_recovers_when_prepared_destination_is_no_longer_lower(self):
        field = StrataField(ws=8, capacity=4, fall=True)
        with field.native():
            self.assertTrue(mushroom.farm_multi(20))
        self.assertTrue(field.fallen)
        self.assertGreaterEqual(field.stock["Mushroom"], 20)
        self.assertEqual(field.spawned, field.joined)

    def test_stratum_after_256_digs_is_reached_in_both_modes(self):
        for parallel in (False, True):
            with self.subTest(parallel=parallel):
                field = StrataField(ws=8, capacity=4, top=300)
                with field.native():
                    result = (
                        mushroom.farm_multi(8) if parallel else mushroom.farm_single(8)
                    )
                self.assertTrue(result)
                self.assertGreaterEqual(field.stock["Mushroom"], 8)
                self.assertEqual(field.spawned, field.joined)

    def test_hollow_seed_row_does_not_hide_other_rows(self):
        field = StrataField(ws=8, capacity=1, rows={0, 2, 4, 6})
        with field.native():
            self.assertTrue(mushroom.farm_multi(8))
        self.assertGreaterEqual(field.stock["Mushroom"], 8)
        self.assertGreater(len(field.seen_rows), 1)

    def test_completed_stock_wins_over_late_failure_after_join(self):
        field = StrataField(ws=8, capacity=4)

        def finished(*args):
            if field.in_worker:
                field.stock["Mushroom"] = 114
                return True
            return False

        with (
            field.native(),
            patch.object(mushroom, "_stratum_multi", side_effect=finished),
        ):
            self.assertTrue(mushroom.produce_multi(100))
        self.assertTrue(field.spawned)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_empty_strata_stop_after_eight_funded_worlds(self):
        for parallel in (False, True):
            with self.subTest(parallel=parallel):
                field = StrataField(ws=8, capacity=4, rows=set())
                with field.native():
                    result = (
                        mushroom.farm_multi(100)
                        if parallel
                        else mushroom.farm_single(100)
                    )
                self.assertFalse(result)
                self.assertEqual(field.worlds, 8)
                self.assertEqual(field.stock["Mushroom"], 0)
                self.assertEqual(field.spawned, field.joined)

    def test_no_excavation_progress_fails_and_joins_workers(self):
        field = StrataField(ws=8, capacity=4)
        with field.native(dig=lambda: None):
            self.assertFalse(mushroom.produce_multi(100))
        # The reference shaft fails before children need to be spawned.
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)


if __name__ == "__main__":
    unittest.main()
