"""Coal sheet/search fixtures; neither full native physics nor a speed benchmark."""

import importlib
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from test_mining_multi import MiningField

coal = importlib.import_module("mine_coal")


class CoalField(MiningField):
    """Thin Dirt sheets above Clay, with optionally simplified native cave-ins."""

    def __init__(self, ws=8, capacity=4, sheets=(2, 4), clay=6):
        super().__init__(ws=ws, capacity=capacity)
        self.sheets = {
            depth: {(x, y) for x in range(ws) for y in range(ws)} for depth in sheets
        }
        self.clay = clay
        self.excavations = []
        self.owned_column = None
        self.collapse = True
        self.reject_spawns = self.fail_dig = False
        self.fail_at = None
        self.last_return = {}

    def z(self, direction=None):
        x, y = self.pos()
        if direction:
            dx, dy = {
                "North": (0, 1),
                "East": (1, 0),
                "South": (0, -1),
                "West": (-1, 0),
            }[direction]
            x, y = (x + dx) % self.ws, (y + dy) % self.ws
        return -self.depths.get((x, y), 0)

    def at(self, pos, depth):
        if depth >= self.clay:
            return "Clay"
        if pos in self.sheets.get(depth, set()):
            return "Coal"
        return "Grassland" if depth == 0 else "Dirt"

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
        return self.at(pos, self.depths.get(pos, 0))

    def dig(self):
        self.budget()
        if self.owned_column is not None and self.x != self.owned_column:
            raise AssertionError("worker dug outside its owned column")
        depth, ground = -self.z(), self.ground()
        self.excavations.append((self.worlds, self.pos(), depth, ground))
        if ground in ("Clay", "Rock", "Bedrock"):
            raise AssertionError("Coal search dug into the stopping layer")
        if self.fail_dig or self.fail_at == (self.x, self.y, depth):
            return None
        self.depths[self.pos()] = depth + 1
        if ground == "Coal":
            self.stock["Coal"] += 2
        self.stock["Block"] = self.stock.get("Block", 0) + 1
        if self.collapse:
            # Native auto-removal affects ordinary neighboring topsoil, not Coal.
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                pos = self.x + dx, self.y + dy
                if self.inside(pos) and self.at(pos, self.depths.get(pos, 0)) not in (
                    "Coal",
                    "Clay",
                ):
                    self.depths[pos] = max(self.depths.get(pos, 0), depth)
            self.relax()
        return None

    def inside(self, pos):
        return all(0 <= value < self.ws for value in pos)

    def relax(self):
        # Non-wrapping eight-neighbor stability, simplified to exposed blocks.
        changed = True
        while changed:
            changed = False
            for x in range(self.ws):
                for y in range(self.ws):
                    pos, depth = (x, y), self.depths.get((x, y), 0)
                    neighbors = [
                        self.depths.get((x + dx, y + dy), 0)
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        if (dx or dy) and self.inside((x + dx, y + dy))
                    ]
                    stability = 3 if self.at(pos, depth) == "Clay" else 1
                    floor = max(neighbors, default=depth) - stability
                    if depth < floor:
                        self.depths[pos] = floor
                        changed = True

    def spawn(self, function, *args):
        if self.reject_spawns:
            return None
        return super().spawn(function, *args)

    def wait_for(self, handle):
        function, args, *_ = self.pending[handle]
        old = self.owned_column
        if function is coal._column:
            self.owned_column = args[0]
        try:
            result = super().wait_for(handle)
            self.last_return[handle] = result
            return result
        finally:
            self.owned_column = old

    @contextmanager
    def api(self, **overrides):
        with super().api(coal, **overrides):
            yield


class CoalTests(unittest.TestCase):
    def test_probe_layout_matches_32_rectangles_4_by_8_and_adapts_to_capacity(self):
        field = CoalField(ws=32, capacity=32)
        with field.api():
            sites = coal._sites(True, 1000000)
        self.assertEqual(len(sites), 32)
        self.assertEqual({x for x, _ in sites}, set(range(1, 32, 4)))
        self.assertEqual({y for _, y in sites}, set(range(3, 32, 8)))
        for ws, capacity in ((1, 1), (3, 32), (8, 4), (12, 3), (32, 1)):
            field = CoalField(ws, capacity)
            with self.subTest(ws=ws, capacity=capacity), field.api():
                sites = coal._sites(True, 1000000)
            self.assertTrue(1 <= len(sites) <= capacity)
            self.assertEqual(len(set(sites)), len(sites))
            self.assertTrue(all(field.inside(pos) for pos in sites))

    def test_probe_digs_at_most_twice_and_returns_coal_without_mining_it(self):
        field = CoalField(sheets=(2,))
        with field.api():
            success, hits, done = coal._probe(3, 3, 100, field.ws)
        self.assertTrue(success)
        self.assertFalse(done)
        self.assertIn((3, 3, -2), hits)
        self.assertEqual(len(field.excavations), 2)
        self.assertEqual(field.stock["Coal"], 0)

    def test_probe_does_not_dig_below_visible_neighbor_coal(self):
        field = CoalField(sheets=(2,))
        field.depths[4, 3] = 2
        with field.api():
            success, hits, done = coal._probe(3, 3, 100, field.ws)
        self.assertTrue(success)
        self.assertIn((4, 3, -2), hits)
        self.assertFalse(field.excavations)

    def test_diagonal_connections_and_side_branches_are_collected_without_dirt_digs(
        self,
    ):
        cells = {(1, 1), (2, 2), (3, 3), (3, 4), (4, 4), (4, 3), (4, 2), (5, 1)}
        for capacity in (1, 2, 4, 32):
            field = CoalField(ws=8, capacity=capacity, sheets=(2,))
            field.sheets[2] = cells
            field.depths = {(x, y): 2 for x in range(8) for y in range(8)}
            with self.subTest(capacity=capacity), field.api():
                self.assertTrue(coal._collect(-2, [(1, 1)], 1000, True, 8))
            mined = {pos for _, pos, _, ground in field.excavations if ground == "Coal"}
            self.assertEqual(mined, cells)
            self.assertTrue(all(ground == "Coal" for *_, ground in field.excavations))
            self.assertCountEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_column_collection_never_follows_a_lower_sheet(self):
        field = CoalField(sheets=(2, 3, 4))
        field.depths = {(x, y): 2 for x in range(8) for y in range(8)}
        with field.api():
            self.assertTrue(coal._collect(-2, [(3, 3)], 10000, True, 8))
        self.assertEqual(field.stock["Coal"], 128)
        self.assertEqual({depth for _, _, depth, _ in field.excavations}, {2})

    def test_diagonal_fringe_discovers_coal_exposed_by_neighbor_topsoil_removal(self):
        field = CoalField(sheets=(2,))
        cells = {(1, 1), (2, 2), (3, 3), (4, 4)}
        field.sheets[2] = cells
        field.depths[1, 1] = 2
        with field.api():
            self.assertTrue(coal._collect(-2, [(1, 1)], 1000, True, 8))
        self.assertEqual({pos for _, pos, _, _ in field.excavations}, cells)
        self.assertEqual(field.stock["Coal"], 8)

    def test_column_finishes_one_direction_before_traveling_to_the_other_end(self):
        field = CoalField(sheets=(2,))
        field.sheets[2] = {(3, y) for y in range(8)}
        field.depths = {(x, y): 2 for x in range(8) for y in range(8)}
        with field.api():
            self.assertTrue(coal._column(3, [3], -2, 1000, 8)[0])
        self.assertEqual(
            [pos[1] for _, pos, _, _ in field.excavations], [3, 4, 5, 6, 7, 2, 1, 0]
        )

    def test_one_world_finishes_known_sheets_top_down_and_stops_at_clay(self):
        for capacity in (1, 2, 4, 32):
            field = CoalField(ws=8, capacity=capacity)
            with self.subTest(capacity=capacity), field.api():
                self.assertTrue(coal.produce_multi(10000))
            depths = [
                depth for _, _, depth, ground in field.excavations if ground == "Coal"
            ]
            self.assertEqual(depths, sorted(depths))
            self.assertEqual(field.stock["Coal"], 256)
            self.assertEqual(field.worlds, 1)
            self.assertTrue(
                all(depth < field.clay for _, _, depth, _ in field.excavations)
            )
            self.assertCountEqual(field.spawned, field.joined)

    def test_absolute_goal_renews_only_after_workers_join(self):
        for parallel in (False, True):
            field = CoalField()
            field.stock["Coal"] = 10
            with self.subTest(parallel=parallel), field.api():
                if parallel:
                    result = coal.farm_multi(300)
                else:
                    result = coal.farm_single(300)
            self.assertTrue(result)
            self.assertGreaterEqual(field.stock["Coal"], 300)
            self.assertEqual(field.worlds, 2)
            self.assertCountEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_spawn_refusals_fall_back_on_parent(self):
        field = CoalField()
        field.reject_spawns = True
        with field.api():
            self.assertTrue(coal.farm_multi(100))
        self.assertGreaterEqual(field.stock["Coal"], 100)
        self.assertFalse(field.pending)

    def test_survey_failure_still_joins_every_child(self):
        field = CoalField()
        original = coal.utils_mine.go_to

        def move(x, y):
            return False if (x, y) == (5, 5) else original(x, y)

        with field.api(), patch.object(coal.utils_mine, "go_to", side_effect=move):
            success, _, _ = coal._survey([(1, 1), (5, 1), (1, 5), (5, 5)], 100, True, 8)
        self.assertFalse(success)
        self.assertEqual(len(field.joined), 3)
        self.assertCountEqual(field.spawned, field.joined)

    def test_collection_failure_still_joins_every_child(self):
        field = CoalField()
        field.depths = {(x, y): 2 for x in range(8) for y in range(8)}
        field.fail_at = (3, 1, 2)
        with field.api():
            self.assertFalse(
                coal._collect(-2, [(x, 1) for x in range(4)], 10000, True, 8)
            )
        self.assertEqual(len(field.joined), 3)
        self.assertCountEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_empty_world_is_a_finite_phase_and_eight_empty_worlds_stop_goal(self):
        field = CoalField(sheets=())
        with field.api():
            self.assertFalse(coal.farm_multi(100))
        self.assertEqual(field.worlds, 8)
        self.assertCountEqual(field.spawned, field.joined)

    def test_search_budget_is_finite_without_clay(self):
        field = CoalField(sheets=(), clay=100000)
        with field.api(), patch.object(coal, "SEARCH_ROUNDS", 3):
            self.assertTrue(coal.produce_single(100))
        self.assertEqual(len(field.excavations), 6)

    def test_satisfied_goal_and_invalid_configuration_do_not_clear_or_spawn(self):
        field = CoalField()
        with field.api():
            self.assertTrue(coal.farm_multi(0))
            with patch.object(coal, "PROBE_DIGS", 0):
                self.assertFalse(coal.produce_multi(10))
        self.assertFalse(field.worlds or field.spawned or field.excavations)

    def test_locked_senses_or_coal_and_unowned_workers_fail_before_prepare(self):
        for locked in ("Coal", "Underground_Senses", "Megafarm"):
            field = CoalField()
            with field.api(num_unlocked=lambda skill: int(skill != locked)):
                self.assertFalse(coal.produce_multi(10))
            self.assertEqual(field.worlds, 0)
        field = CoalField()
        with field.api(num_drones=lambda: 2):
            self.assertFalse(coal.produce_multi(10))
        self.assertEqual(field.worlds, 0)


if __name__ == "__main__":
    unittest.main()
