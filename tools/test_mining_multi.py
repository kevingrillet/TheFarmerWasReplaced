"""Mining geometry/ownership fixtures, not native timing or a complete engine."""

import copy
import importlib
import unittest
from collections import Counter
from contextlib import ExitStack, contextmanager
from unittest.mock import Mock, patch

from test_multi_leaderboards import Field
from test_producer_contract import Symbols

helpers = importlib.import_module("utils_mine")
farm_utils = importlib.import_module("utils_farm")
manager = importlib.import_module("resource_manager")


class MiningField(Field):
    """Queued workers with independent cursors and shared stock/terrain.

    Optional Coal cave-ins destroy four neighbors without paying for them.
    Native stability propagation, durations and concurrency are not emulated.
    """

    def __init__(self, ws=12, capacity=4, resource="Coal"):
        super().__init__(ws=ws, capacity=capacity)
        self.resource = resource
        self.depths, self.layers = {}, {}
        self.digs, self.probes = [], []
        self.worlds = 0
        self.empty = self.cave_ins = self.in_worker = False
        self.sector = None
        self.stock.update(Coal=64, Iron=128)
        self.stock[resource] = 0
        self.limit = 2000000

    def clear(self):
        super().clear()
        if self.in_worker:
            raise AssertionError("worker cleared the shared world")
        self.worlds += 1
        self.depths.clear()
        self.events.append(("clear", self.worlds))

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
        depth = self.depths.get((x, y), 0)
        layers = self.layers.get((x, y))
        if layers is None:
            layers = ["Grassland", "Dirt", "Rock", "Rock", self.resource, self.resource]
            if self.empty:
                layers = ["Grassland", "Dirt"]
        return layers[depth] if depth < len(layers) else "Bedrock"

    def dig(self):
        self.budget()
        if self.sector:
            x0, y0, x1, y1 = self.sector
            if not (x0 <= self.x < x1 and y0 <= self.y < y1):
                raise AssertionError("worker dug outside its sector")
        ground = self.ground()
        self.digs.append((self.pos(), ground))
        if ground == "Bedrock":
            return None
        self.depths[self.pos()] = self.depths.get(self.pos(), 0) + 1
        if ground in ("Coal", "Iron", "Quartz"):
            self.stock[ground] = self.stock.get(ground, 0) + 1
        self.stock["Block"] = self.stock.get("Block", 0) + 1
        if self.cave_ins and ground == "Coal":
            depth = self.depths[self.pos()]
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                pos = ((self.x + dx) % self.ws, (self.y + dy) % self.ws)
                self.depths[pos] = max(self.depths.get(pos, 0), depth)
        return None

    def prospect(self, item):
        self.budget()
        if self.stock.get(item, 0) < 1:
            raise AssertionError("unfunded prospect")
        self.stock[item] -= 1
        self.probes.append((item, self.pos(), self.ground()))
        return None

    def spawn(self, function, *args):
        return super().spawn(function, *copy.deepcopy(args))

    def wait_for(self, handle):
        previous = self.in_worker
        self.in_worker = True
        try:
            return super().wait_for(handle)
        finally:
            self.in_worker = previous

    @contextmanager
    def api(self, *modules, **overrides):
        bindings = dict(
            Hats=Symbols(),
            get_ground_type=self.ground,
            get_pos_z=self.z,
            get_stability=lambda direction=None: {
                "Rock": 3,
                "Clay": 3,
                "Iron": 3,
                "Quartz": 5,
                "Mushroom": 3,
                "Limestone": 3,
                "Sand": 2,
                "Petrified_Pumpkin": 8,
            }.get(self.ground(direction), 1),
            dig=self.dig,
            prospect_iron=lambda: self.prospect("Coal"),
            prospect_quartz=lambda: self.prospect("Iron"),
            Items=Symbols(),
            Entities=Symbols(),
            Grounds=Symbols(),
            Unlocks=Symbols(),
            num_unlocked=lambda _: 1,
            max_drones=lambda: self.capacity,
            get_time=lambda: self.calls / 100,
            change_hat=lambda _: None,
        )
        bindings.update(overrides)
        with ExitStack() as stack:
            for module in (helpers, farm_utils, helpers.utils_move, *modules):
                stack.enter_context(super().api(module, **bindings))
            yield


class MushroomField(MiningField):
    def __init__(self, **kwargs):
        super().__init__(resource="Mushroom", **kwargs)
        self.pushed, self.pushes = {}, []

    def clear(self):
        super().clear()
        self.pushed.clear()

    def ground(self, direction=None):
        if direction:
            origin = self.pos()
            self.move(direction)
            value = self.ground()
            self.x, self.y = origin
            return value
        depth = self.depths.get(self.pos(), 0)
        if (self.pos(), depth) in self.pushed or depth in (2, 3, 6, 7):
            return "Mushroom"
        return "Rock" if depth < 9 else "Bedrock"

    def mushroom_type(self):
        depth = self.depths.get(self.pos(), 0)
        return self.pushed.get((self.pos(), depth), (self.x + self.y) % 2)

    def measure(self, direction=None):
        origin = self.pos()
        if direction:
            self.move(direction)
        value = self.mushroom_type() if self.ground() == "Mushroom" else None
        self.x, self.y = origin
        return value

    def can_push(self, direction):
        x, y = self.pos()
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        target = ((x + dx) % self.ws, (y + dy) % self.ws)
        return self.ground() == "Mushroom" and self.depths.get(target, 0) > -self.z()

    def push(self, direction):
        if self.ground() != "Mushroom":
            return False
        origin, origin_depth, kind = self.pos(), -self.z(), self.mushroom_type()
        self.move(direction)
        target, target_depth = self.pos(), -self.z()
        self.pushes.append((origin, target))
        if self.sector:
            x0, y0, x1, y1 = self.sector
            if not (x0 <= self.x < x1 and y0 <= self.y < y1):
                raise AssertionError("mushroom pushed into another sector")
        if target_depth <= origin_depth:
            self.x, self.y = origin
            return False
        if self.ground() == "Mushroom" and self.mushroom_type() == kind:
            self.stock["Mushroom"] += 1
            self.depths[target] = target_depth + 1
        else:
            self.depths[target] = target_depth - 1
            self.pushed[(target, target_depth - 1)] = kind
        self.depths[origin] = origin_depth + 1
        self.pushed.pop((origin, origin_depth), None)
        self.x, self.y = origin
        return True


class DynamiteField(MiningField):
    def __init__(self, ws=6, capacity=4, mines=((2, 2),)):
        super().__init__(ws=ws, capacity=capacity, resource="Dynamite")
        self.mines = set(mines)
        self.revealed = set()
        self.solved = self.exploded = False

    def clear(self):
        super().clear()
        self.revealed.clear()
        self.solved = self.exploded = False

    def ground(self, direction=None):
        if direction:
            return super().ground(direction)
        depth = -self.z()
        if self.exploded and depth >= 2:
            return "Bedrock"
        return (
            ["Grassland", "Dirt", "Dynamite", "Soot"][depth] if depth < 4 else "Bedrock"
        )

    def dig(self):
        if self.ground() != "Dynamite":
            return super().dig()
        self.budget()
        self.digs.append((self.pos(), "Dynamite"))
        if self.pos() in self.mines:
            if self.in_worker or self.pending:
                raise AssertionError("a speculative mine was opened concurrently")
            self.exploded = True
            for x in range(self.ws):
                for y in range(self.ws):
                    self.depths[(x, y)] = 4
            return None
        self.revealed.add(self.pos())
        self.depths[self.pos()] = 3
        self.stock["Dynamite"] += 1
        if len(self.revealed) == self.ws * self.ws - len(self.mines):
            self.solved = True
            self.stock["Dynamite"] += len(self.mines) ** 2
            for pos in self.mines:
                self.depths[pos] = 3
        return None

    def measure(self):
        if self.ground() != "Soot":
            raise AssertionError("measured away from a revealed soot cell")
        if self.solved:
            return None
        return sum(
            abs(x - self.x) <= 1 and abs(y - self.y) <= 1 and (x, y) != self.pos()
            for x, y in self.mines
        )


class MiningMultiTests(unittest.TestCase):
    def test_sector_partition_covers_field_with_unique_spread_centres(self):
        for size in (1, 3, 8, 12, 32):
            for capacity in (1, 2, 4, 7, 32):
                field = MiningField(ws=size, capacity=capacity)
                with self.subTest(size=size, capacity=capacity), field.api():
                    sectors = helpers.sector_plan(True)
                coverage, centres = Counter(), set()
                for x0, y0, x1, y1 in sectors:
                    centres.add(((x0 + x1 - 1) // 2, (y0 + y1 - 1) // 2))
                    coverage.update(
                        (x, y) for x in range(x0, x1) for y in range(y0, y1)
                    )
                self.assertEqual(len(centres), len(sectors))
                self.assertLessEqual(len(sectors), capacity)
                self.assertEqual(set(coverage.values()), {1})
                self.assertEqual(len(coverage), size * size)
                if size == 32:
                    self.assertEqual(len(sectors), capacity)

    def test_sector_failure_joins_children_and_divides_one_probe_reserve(self):
        field, received = MiningField(ws=12, capacity=4), []

        def worker(qty, bounds, options, budget):
            received.append((field.pos(), budget))
            return bounds != (6, 6, 12, 12)

        with field.api():
            sectors = helpers.sector_plan(True)
            self.assertFalse(
                helpers.run_sectors(worker, "Iron", 1000, sectors, None, 11)
            )
        self.assertEqual(sum(budget for _, budget in received), 11)
        self.assertEqual(len({pos for pos, _ in received}), 4)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_ore_producers_finish_and_join_at_multiple_capacities(self):
        for item in ("Coal", "Iron", "Quartz"):
            module = importlib.import_module("mine_" + item.lower())
            for capacity in (1, 2, 4, 32):
                field = MiningField(ws=32, capacity=capacity, resource=item)
                field.cave_ins = item == "Coal"
                if item == "Coal":
                    # Coal belongs to the shallow Dirt band, before Rock/Clay.
                    field.layers = {
                        (x, y): ["Grassland", "Dirt", "Coal", "Coal", "Clay"]
                        for x in range(field.ws)
                        for y in range(field.ws)
                    }
                with self.subTest(item=item, capacity=capacity), field.api(module):
                    self.assertTrue(module.farm_multi(10))
                self.assertGreaterEqual(field.stock[item], 10)
                self.assertEqual(field.spawned, field.joined)
                self.assertFalse(field.pending)
                if capacity > 1:
                    self.assertTrue(field.spawned)

    def test_sector_travel_failure_joins_already_started_workers(self):
        field = MiningField(ws=12, capacity=4)
        with field.api():
            sectors = helpers.sector_plan(True)
            with patch.object(helpers, "go_to", side_effect=[True, False]):
                self.assertFalse(
                    helpers.run_sectors(lambda *args: True, "Iron", 1000, sectors)
                )
        self.assertEqual(len(field.joined), 1)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_depleted_vein_returns_to_its_initial_drilling_column(self):
        field = MiningField(ws=5, capacity=1)
        field.layers = {(x, y): ["Bedrock"] for x in range(5) for y in range(5)}
        field.layers[(2, 2)] = ["Rock", "Coal", "Bedrock"]
        field.layers[(3, 2)] = ["Coal", "Rock", "Bedrock"]
        field.x = field.y = 2
        with field.api():
            self.assertTrue(
                helpers._ore_sector(2, (0, 0, 5, 5), ("Coal", "Coal", None), 0)
            )
        self.assertEqual([pos for pos, _ in field.digs], [(3, 2), (2, 2), (2, 2)])

    def test_workers_do_not_chase_an_ore_in_the_next_sector(self):
        field = MiningField(ws=6, capacity=1)
        field.layers = {(x, y): ["Bedrock"] for x in range(6) for y in range(6)}
        field.layers[(1, 1)] = ["Rock", "Coal", "Bedrock"]
        field.layers[(2, 1)] = ["Coal", "Rock", "Bedrock"]
        field.layers[(3, 1)] = ["Coal", "Bedrock"]
        field.x = field.y = 1
        with field.api():
            self.assertTrue(
                helpers._ore_sector(2, (0, 0, 3, 3), ("Coal", "Coal", None), 0)
            )
        self.assertNotIn((3, 1), field.depths)
        self.assertTrue(all(pos[0] < 3 for pos, _ in field.digs))

    def test_iron_none_can_mean_ore_directly_below(self):
        field = MiningField(ws=3, capacity=1, resource="Iron")
        field.layers[(1, 1)] = ["Rock", "Iron", "Bedrock"]
        field.x = field.y = 1
        with field.api():
            self.assertTrue(
                helpers._ore_sector(1, (0, 0, 3, 3), ("Iron", "Iron", "Coal"), 1)
            )
        self.assertEqual(field.stock["Iron"], 1)
        self.assertEqual(len(field.probes), 1)

    def test_quartz_compares_probe_distances_and_restores_rejected_probe_positions(
        self,
    ):
        field = MiningField(ws=3, capacity=1, resource="Quartz")
        field.layers = {
            (x, y): ["Rock", "Rock", "Rock", "Bedrock"]
            for x in range(3)
            for y in range(3)
        }
        field.layers[(2, 1)] = ["Rock", "Rock", "Quartz", "Bedrock"]
        field.x = field.y = 1

        def probe():
            field.prospect("Iron")
            return (
                (field.x - 2) ** 2 + (field.y - 1) ** 2 + (field.z() + 2) ** 2
            ) ** 0.5

        with field.api(prospect_quartz=probe):
            self.assertTrue(
                helpers._ore_sector(1, (0, 0, 3, 3), ("Quartz", "Quartz", "Iron"), 3)
            )
        self.assertEqual([pos for _, pos, _ in field.probes], [(1, 1), (1, 2), (2, 1)])
        self.assertTrue(all(pos == (2, 1) for pos, _ in field.digs))
        self.assertEqual(field.stock["Quartz"], 1)

    def test_32_workers_do_not_overspend_the_funded_probe_reserve(self):
        for item, currency, limit in (("Iron", "Coal", 64), ("Quartz", "Iron", 128)):
            module = importlib.import_module("mine_" + item.lower())
            field = MiningField(ws=32, capacity=32, resource=item)
            with self.subTest(item=item), field.api(module):
                self.assertTrue(module.produce_multi(10000))
            self.assertLessEqual(len(field.probes), limit)
            self.assertGreater(len(field.probes), 0)
            self.assertTrue(all(probe[0] == currency for probe in field.probes))
            self.assertGreaterEqual(field.stock[currency], 0)
            self.assertEqual(field.spawned, field.joined)

    def test_unfunded_or_missing_senses_fail_before_clearing(self):
        module = importlib.import_module("mine_iron")
        for unavailable in ("Coal", "Underground_Senses"):
            field = MiningField(resource="Iron")
            if unavailable == "Coal":
                field.stock["Coal"] = 0
            with field.api(
                module, num_unlocked=lambda skill: int(skill != unavailable)
            ):
                self.assertFalse(module.produce_multi(10))
            self.assertEqual(field.worlds, 0)
            self.assertFalse(field.spawned)

    def test_block_multi_requires_no_underground_sensors(self):
        module = importlib.import_module("mine_block")
        field = MiningField(ws=12, capacity=4, resource="Block")
        forbidden = Mock(side_effect=AssertionError("Block used Underground Senses"))
        with field.api(
            module,
            num_unlocked=lambda skill: int(skill != "Underground_Senses"),
            get_ground_type=forbidden,
            get_pos_z=forbidden,
        ):
            self.assertTrue(module.farm_multi(16))
        forbidden.assert_not_called()
        self.assertTrue(field.spawned)
        self.assertEqual(field.spawned, field.joined)

    def test_empty_world_search_is_bounded(self):
        module, field = importlib.import_module("mine_coal"), MiningField(capacity=4)
        field.empty = True
        with field.api(module):
            self.assertFalse(module.farm_multi(10))
        self.assertEqual(field.worlds, 8)
        self.assertEqual(field.spawned, field.joined)

    def test_mushrooms_use_owned_lanes_and_join(self):
        module = importlib.import_module("farm_mushroom")
        for capacity in (1, 2, 4, 32):
            field = MushroomField(ws=32, capacity=capacity)
            original = module._stratum_multi

            def worker(qty, sector, options, budget):
                previous, field.sector = field.sector, sector
                try:
                    return original(qty, sector, options, budget)
                finally:
                    field.sector = previous

            with (
                self.subTest(capacity=capacity),
                field.api(
                    module,
                    push=field.push,
                    can_push=field.can_push,
                    measure=field.measure,
                ),
                patch.object(module, "_stratum_multi", side_effect=worker),
            ):
                self.assertTrue(module.farm_multi(8))
            self.assertGreaterEqual(field.stock["Mushroom"], 8)
            self.assertTrue(field.pushes)
            self.assertEqual(field.spawned, field.joined)

    def test_mushroom_refused_pushes_are_bounded_and_join_every_child(self):
        module, field = importlib.import_module("farm_mushroom"), MushroomField()
        with field.api(
            module, push=lambda _: False, can_push=field.can_push, measure=field.measure
        ):
            self.assertFalse(module.farm_multi(100))
        self.assertTrue(field.spawned)
        self.assertEqual(field.spawned, field.joined)
        self.assertEqual(field.worlds, 8)

    def test_dynamite_solves_with_shared_parent_deductions_and_finite_workers(self):
        module = importlib.import_module("mine_dynamite")
        for capacity in (1, 2, 4, 32):
            field = DynamiteField(capacity=capacity)
            original = module._deduce_incremental

            def deduce(clues, flags, state, changed):
                self.assertFalse(field.in_worker)
                self.assertFalse(field.pending)
                return original(clues, flags, state, changed)

            with (
                self.subTest(capacity=capacity),
                field.api(module, measure=field.measure),
                patch.object(module, "_deduce_incremental", side_effect=deduce),
            ):
                self.assertTrue(module.produce_multi(1000))
            self.assertTrue(field.solved)
            self.assertFalse(field.exploded)
            self.assertEqual(len(field.revealed), 35)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)
            self.assertEqual(field.worlds, 1)
            if capacity > 1:
                self.assertTrue(field.spawned)

    def test_dynamite_parent_block_still_merges_and_joins_copied_worker_results(self):
        module, field = (
            importlib.import_module("mine_dynamite"),
            DynamiteField(capacity=4),
        )
        clues = {}

        def reveal(pos, depth, ws, local_clues):
            if pos == 3:
                return "blocked"
            local_clues[pos] = 0
            return None

        with (
            field.api(module),
            patch.object(module, "_reveal_single", side_effect=reveal),
        ):
            self.assertEqual(
                module._reveal_batch_multi([0, 1, 2, 3], 1000, -2, 6, clues), "blocked"
            )
        self.assertEqual(clues, {0: 0, 1: 0, 2: 0})
        self.assertEqual(len(field.joined), 3)
        self.assertEqual(field.spawned, field.joined)

    def test_dynamite_guesses_are_never_concurrent(self):
        module = importlib.import_module("mine_dynamite")
        field = DynamiteField(ws=4, capacity=4, mines=((1, 1),))
        original = module._guess_single

        def guess(clues, flags, constraints, ws):
            self.assertFalse(field.pending)
            self.assertFalse(field.in_worker)
            return original(clues, flags, constraints, ws)

        with (
            field.api(module, measure=field.measure),
            patch.object(module, "_guess_single", side_effect=guess) as guesses,
        ):
            self.assertTrue(module.produce_multi(1000))
        self.assertGreater(guesses.call_count, 0)
        self.assertEqual(field.spawned, field.joined)

    def test_dynamite_joins_before_regenerating_for_another_puzzle(self):
        module = importlib.import_module("mine_dynamite")
        field = DynamiteField(ws=6, capacity=4, mines=())
        with field.api(module, measure=field.measure):
            self.assertTrue(module.farm_multi(40))
        self.assertGreaterEqual(field.stock["Dynamite"], 40)
        self.assertEqual(field.worlds, 2)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_manager_selects_multi_for_all_underground_producers(self):
        for name, item in [
            ("mine_coal", "Coal"),
            ("mine_iron", "Iron"),
            ("mine_quartz", "Quartz"),
            ("mine_block", "Block"),
            ("mine_dynamite", "Dynamite"),
            ("farm_mushroom", "Mushroom"),
            ("farm_rice", "Rice"),
            ("farm_bamboo", "Bamboo"),
        ]:
            module = importlib.import_module(name)
            for parallel in (False, True):
                stock = {item: 0}

                def produce(target):
                    stock[item] = target
                    return True

                with (
                    self.subTest(item=item, parallel=parallel),
                    patch.multiple(
                        manager,
                        Items=Symbols(),
                        Unlocks=Symbols(),
                        num_items=lambda key: stock.get(key, 0),
                        num_unlocked=lambda _: 1,
                        create=True,
                    ),
                    patch.object(module, "requirements", return_value={}),
                    patch.object(module, "produce_multi", side_effect=produce) as multi,
                    patch.object(
                        module, "produce_single", side_effect=produce
                    ) as single,
                ):
                    self.assertTrue(manager.farm(item, 10, parallel, False, True))
                    self.assertEqual(multi.call_count, int(parallel))
                    self.assertEqual(single.call_count, int(not parallel))


if __name__ == "__main__":
    unittest.main()
