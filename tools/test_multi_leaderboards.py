"""Isolated multi benchmark contracts; no game physics or timing emulation."""

import ast
import importlib.util
import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
TARGETS = {
    "leaderboard_hay": ("Hay", 2000000000),
    "leaderboard_wood": ("Wood", 10000000000),
    "leaderboard_carrot": ("Carrot", 2000000000),
    "leaderboard_pumpkin": ("Pumpkin", 200000000),
    "leaderboard_cactus": ("Cactus", 33554432),
    "leaderboard_power": ("Power", 100000),
    "leaderboard_gold": ("Gold", 9863168),
    "leaderboard_bone": ("Bone", 33488928),
}


def symbols(names):
    return SimpleNamespace(**{name: name for name in names.split()})


ITEMS = symbols(
    "Hay Wood Carrot Pumpkin Cactus Power Gold Bone Water Fertilizer Weird_Substance"
)
ENTITIES = symbols(
    "Grass Tree Bush Carrot Pumpkin Dead_Pumpkin Cactus Sunflower Treasure"
)
DIRECTIONS = dict(North="North", East="East", South="South", West="West")


def load(name):
    spec = importlib.util.spec_from_file_location(name, SAVE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Field:
    """Immediate-growth field; queued workers restore their spawn coordinates.

    Workers run at join time, rather than in parallel. This checks ownership,
    cursor restoration and fallback control flow, without claiming concurrency.
    """

    def __init__(self, ws=3, capacity=2, seed=0):
        self.ws, self.capacity = ws, capacity
        self.x = self.y = 0
        self.entities, self.grounds, self.values = {}, {}, {}
        self.stock = {"Water": 10000, "Fertilizer": 10000}
        self.pending, self.spawned, self.joined = {}, [], []
        self.plants, self.harvests, self.events = [], [], []
        self.random = random.Random(seed)
        self.calls = 0
        self.limit = 50000
        self.fail_plant = None
        self.kill_pumpkin = False
        self.plant_counts = {}
        self.unripe = {}

    def budget(self):
        self.calls += 1
        if self.calls > self.limit:
            raise AssertionError("benchmark did not terminate in the contract fixture")

    def pos(self):
        return self.x, self.y

    def entity(self):
        return self.entities.get(self.pos(), "Grass")

    def move(self, direction):
        self.budget()
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        self.x = (self.x + dx) % self.ws
        self.y = (self.y + dy) % self.ws
        return True

    def clear(self):
        self.assert_no_workers()
        self.entities.clear()
        self.grounds.clear()
        self.values.clear()
        self.x = self.y = 0

    def assert_no_workers(self):
        if self.pending:
            raise AssertionError("world cleared before owned workers were joined")

    def plant(self, entity):
        self.budget()
        if self.fail_plant == self.pos():
            return False
        pos = self.pos()
        self.plants.append((pos, entity))
        self.plant_counts[pos] = self.plant_counts.get(pos, 0) + 1
        self.entities[pos] = entity
        if entity == "Cactus":
            self.values[pos] = self.random.randrange(10)
        elif entity == "Sunflower":
            self.values[pos] = [7, 15, 10][self.y % 3]
        elif entity == "Pumpkin" and self.kill_pumpkin and self.plant_counts[pos] == 1:
            self.entities[pos] = "Dead_Pumpkin"
        return True

    def can_harvest(self):
        self.budget()
        if self.unripe.get(self.pos(), 0):
            self.unripe[self.pos()] -= 1
            return False
        return self.entity() != "Dead_Pumpkin"

    def harvest(self):
        self.budget()
        entity, pos = self.entity(), self.pos()
        self.harvests.append((pos, entity, self.values.get(pos)))
        self.events.append(("harvest", entity))
        item = {
            "Grass": "Hay",
            "Tree": "Wood",
            "Bush": "Wood",
            "Sunflower": "Power",
            "Treasure": "Gold",
        }.get(entity, entity)
        gain = 1
        if entity in ("Cactus", "Pumpkin"):
            if self.pending:
                raise AssertionError("final harvest before every worker completed")
            positions = [(x, y) for x in range(self.ws) for y in range(self.ws)]
            if not all(self.entities.get(p) == entity for p in positions):
                raise AssertionError("incomplete field harvested")
            if entity == "Cactus":
                for x, y in positions:
                    if x and self.values[(x - 1, y)] > self.values[(x, y)]:
                        raise AssertionError("row not sorted before harvest")
                    if y and self.values[(x, y - 1)] > self.values[(x, y)]:
                        raise AssertionError("column not sorted before harvest")
            gain = len(positions) ** 2
            self.entities.clear()
            self.values.clear()
        else:
            self.entities.pop(pos, None)
            self.values.pop(pos, None)
        self.stock[item] = self.stock.get(item, 0) + gain
        return True

    def till(self):
        self.grounds[self.pos()] = "Soil"

    def measure(self, direction=None):
        self.budget()
        x, y = self.pos()
        if direction == "North":
            y = (y + 1) % self.ws
        elif direction == "South":
            y = (y - 1) % self.ws
        elif direction == "East":
            x = (x + 1) % self.ws
        elif direction == "West":
            x = (x - 1) % self.ws
        return self.values[(x, y)]

    def swap(self, direction):
        pos = self.pos()
        self.move(direction)
        other = self.pos()
        self.x, self.y = pos
        self.values[pos], self.values[other] = self.values[other], self.values[pos]

    def use_item(self, item, amount=1):
        if item == "Weird_Substance":
            if amount != 32:
                raise AssertionError(
                    "one-tile maze amount must follow the upgrade level"
                )
            self.entities[self.pos()] = "Treasure"
        return True

    def num_drones(self):
        self.budget()
        return 1 + len(self.pending)

    def spawn(self, function, *args):
        if len(self.pending) >= self.capacity - 1:
            return None
        handle = len(self.spawned) + 1
        self.pending[handle] = function, args, self.pos()
        self.spawned.append(handle)
        self.events.append(("spawn", handle))
        return handle

    def wait_for(self, handle):
        function, args, origin = self.pending.pop(handle)
        parent = self.pos()
        self.x, self.y = origin
        try:
            result = function(*args)
        finally:
            self.x, self.y = parent
        self.joined.append(handle)
        self.events.append(("join", handle))
        return result

    def api(self, module, **overrides):
        bindings = dict(
            Items=ITEMS,
            Entities=ENTITIES,
            Grounds=symbols("Soil Grassland"),
            Unlocks=symbols("Mazes"),
            num_unlocked=lambda _: 6,
            get_world_size=lambda: self.ws,
            get_pos_x=lambda: self.x,
            get_pos_y=lambda: self.y,
            get_entity_type=self.entity,
            get_ground_type=lambda: self.grounds.get(self.pos(), "Grassland"),
            get_water=lambda: 1,
            num_items=lambda item: self.stock.get(item, 0),
            can_harvest=self.can_harvest,
            move=self.move,
            plant=self.plant,
            harvest=self.harvest,
            till=self.till,
            measure=self.measure,
            swap=self.swap,
            use_item=self.use_item,
            spawn_drone=self.spawn,
            wait_for=self.wait_for,
            num_drones=self.num_drones,
            clear=self.clear,
            quick_print=lambda *args: None,
            **DIRECTIONS,
        )
        bindings.update(overrides)
        return patch.multiple(module, **bindings, create=True)


class MultiLeaderboardTests(unittest.TestCase):
    def test_all_resource_categories_are_standalone_inert_and_have_official_targets(
        self,
    ):
        for name, (_, target) in TARGETS.items():
            with self.subTest(name=name):
                tree = ast.parse((SAVE / (name + ".py")).read_text(encoding="utf-8"))
                self.assertFalse(
                    any(
                        isinstance(n, (ast.Import, ast.ImportFrom))
                        for n in ast.walk(tree)
                    )
                )
                self.assertEqual(load(name).TARGET, target)

    def test_satisfied_targets_skip_every_action(self):
        for name in TARGETS:
            module = load(name)
            with (
                self.subTest(name=name),
                patch.multiple(
                    module, Items=ITEMS, num_items=lambda _: 12, create=True
                ),
            ):
                self.assertTrue(module.run(10))

    def test_finite_resource_runs_finish_and_join_owned_workers_at_different_capacities(
        self,
    ):
        for name in TARGETS:
            if name == "leaderboard_bone":
                continue
            for capacity in (1, 2, 4, 32):
                module, field = load(name), Field(capacity=capacity)
                item = TARGETS[name][0]
                with self.subTest(name=name, capacity=capacity), field.api(module):
                    self.assertTrue(module.run(13))
                self.assertGreaterEqual(field.stock[item], 13)
                self.assertEqual(field.pending, {})
                self.assertCountEqual(field.spawned, field.joined)
                if capacity > 1:
                    self.assertTrue(field.spawned)
                if name == "leaderboard_wood":
                    for (x, y), entity in field.plants:
                        self.assertEqual(entity, "Tree" if (x + y) % 2 == 0 else "Bush")

    def test_cactus_sorts_both_axes_before_harvest(self):
        for size in (1, 2, 3, 4, 5):
            for seed in range(8):
                module, field = (
                    load("leaderboard_cactus"),
                    Field(ws=size, capacity=2, seed=seed),
                )
                with self.subTest(size=size, seed=seed), field.api(module):
                    self.assertTrue(module.run(1))
                self.assertTrue(
                    any(entity == "Cactus" for _, entity, _ in field.harvests)
                )

    def test_full_32_by_32_field_joins_all_31_spawned_workers(self):
        for name in TARGETS:
            if name == "leaderboard_bone":
                continue
            module, field = load(name), Field(ws=32, capacity=32)
            field.limit = 500000
            with self.subTest(name=name), field.api(module):
                self.assertTrue(module.run(13))
            self.assertGreaterEqual(len(field.spawned), 31)
            self.assertEqual(len(field.spawned) % 31, 0)
            self.assertCountEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_cactus_and_pumpkin_join_columns_before_harvest_and_repair_dead_plants(
        self,
    ):
        for name in ("leaderboard_cactus", "leaderboard_pumpkin"):
            module, field = load(name), Field(capacity=4)
            field.kill_pumpkin = True
            with self.subTest(name=name), field.api(module):
                self.assertTrue(module.run(1))
            if name == "leaderboard_pumpkin":
                self.assertTrue(all(n == 2 for n in field.plant_counts.values()))

    def test_power_keeps_unripe_plants_and_consumes_buckets_without_skipping(self):
        module, field = load("leaderboard_power"), Field(ws=6, capacity=1)
        field.unripe[(0, 1)] = 3
        with field.api(module):
            self.assertTrue(module._column(6, True))
        petals = [value for _, entity, value in field.harvests if entity == "Sunflower"]
        self.assertEqual(petals, [15, 15, 10, 10, 7, 7])
        self.assertNotIn("Sunflower", field.entities.values())

    def test_parent_failure_still_joins_every_already_owned_worker(self):
        for name in (
            "leaderboard_cactus",
            "leaderboard_pumpkin",
            "leaderboard_power",
            "leaderboard_gold",
        ):
            module, field = load(name), Field(capacity=2)
            field.fail_plant = (1, 0)
            with self.subTest(name=name), field.api(module):
                self.assertFalse(module.run(100000))
            self.assertEqual(field.pending, {})
            self.assertCountEqual(field.spawned, field.joined)

    def test_join_failure_is_not_reported_as_success(self):
        module = load("leaderboard_hay")
        joined = []
        with patch.object(
            module,
            "wait_for",
            side_effect=lambda h: joined.append(h) or h != 2,
            create=True,
        ):
            self.assertFalse(module._join([1, 2, 3]))
        self.assertEqual(joined, [1, 2, 3])

    def test_maze_creation_failure_does_not_harvest_a_bush(self):
        module, field = load("leaderboard_gold"), Field(capacity=1)
        with field.api(module, use_item=lambda *args: False):
            self.assertFalse(module.run(1))
        self.assertFalse(field.harvests)

    def test_dinosaur_covers_an_even_field_and_restores_the_hat(self):
        for size in (2, 4, 6, 32):
            module = load("leaderboard_bone")
            position, visited, hats = [0, 0], set(), []
            stock = [0]

            def move(direction):
                dx, dy = {
                    "North": (0, 1),
                    "East": (1, 0),
                    "South": (0, -1),
                    "West": (-1, 0),
                }[direction]
                nxt = position[0] + dx, position[1] + dy
                self.assertTrue(0 <= nxt[0] < size and 0 <= nxt[1] < size, nxt)
                if nxt in visited:
                    return False
                position[:] = nxt
                visited.add(nxt)
                return True

            def hat(value):
                hats.append(value)
                if value == "Dinosaur":
                    visited.add(tuple(position))
                else:
                    stock[0] += (len(visited) - 1) ** 2

            with (
                self.subTest(size=size),
                patch.multiple(
                    module,
                    Items=ITEMS,
                    Hats=symbols("Dinosaur_Hat Straw_Hat"),
                    num_items=lambda _: stock[0],
                    get_world_size=lambda: size,
                    get_pos_x=lambda: position[0],
                    get_pos_y=lambda: position[1],
                    change_hat=lambda value: hat(
                        "Dinosaur" if value == "Dinosaur_Hat" else "Straw"
                    ),
                    move=move,
                    quick_print=lambda *args: None,
                    **DIRECTIONS,
                    create=True,
                ),
            ):
                self.assertTrue(module.run(1))
            self.assertEqual(len(visited), size * size)
            self.assertEqual(hats, ["Dinosaur", "Straw"])


if __name__ == "__main__":
    unittest.main()
