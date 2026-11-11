"""Candidate strategy checks; fixture physics do not establish native timings."""

import ast
import random
import unittest
from unittest.mock import Mock, patch

from test_multi_leaderboards import DIRECTIONS, ITEMS, SAVE, load, symbols
from test_multi_leaderboards import Field as ResourceField

CANDIDATES = {
    "leaderboard_power_columns": ("Power", 100000),
    "leaderboard_gold_reuse": ("Gold", 9863168),
    "leaderboard_bone_hybrid": ("Bone", 33488928),
}


class Field(ResourceField):
    def api(self, module, **overrides):
        overrides.setdefault("Unlocks", symbols("Mazes Timing"))
        return super().api(module, **overrides)


class MazeField(Field):
    """Queued workers check placement and ownership, not parallel scheduling."""

    def __init__(self, capacity=32):
        super().__init__(ws=8, capacity=capacity)
        self.doses = []
        self.created = []

    def resize(self, size):
        if size < 3:
            raise AssertionError("native set_world_size does not support 1x1 or 2x2")
        self.assert_no_workers()
        self.ws = size
        self.clear()

    def use_item(self, item, amount=1):
        self.doses.append(amount)
        self.created.append(self.pos())
        if amount != self.ws * 32:
            raise AssertionError("maze dose calculated before resize")
        return True


class Snake:
    """Moving tail, apples on departure and non-wrapping movement.

    Reproduces the contracts relevant to route safety, not growth ticks, native
    RNG order, surface discovery or exact last-apple selection.
    """

    def __init__(self, size, seed):
        self.size = size
        self.random = random.Random(seed)
        self.position = (0, 0)
        self.tail = []
        self.apple = self.next_apple = None
        self.stock = 0
        self.hats = []
        self.moves = 0
        self.collisions = []
        self.force_failure = False

    def free(self, exclude=()):
        occupied = set(self.tail) | {self.position, self.apple} | set(exclude)
        return [
            (x, y)
            for x in range(self.size)
            for y in range(self.size)
            if (x, y) not in occupied
        ]

    def choose(self, exclude=()):
        free = self.free(exclude)
        return self.random.choice(free) if free else None

    def clear(self):
        if self.tail:
            raise AssertionError("tail cleared before restoring Straw")
        self.position = (0, 0)
        self.apple = self.next_apple = None

    def hat(self, value):
        self.hats.append(value)
        if value == "Dinosaur_Hat":
            self.apple = self.position
            self.next_apple = self.choose()
        else:
            self.stock += len(self.tail) ** 2
            self.tail = []
            self.apple = self.next_apple = None

    def measure(self):
        if self.position != self.apple:
            raise AssertionError("measured away from the current apple")
        return self.next_apple

    def move(self, direction):
        self.moves += 1
        if self.moves > self.size**4 * 4:
            raise AssertionError("route did not terminate")
        if self.force_failure:
            return False
        dx, dy = {"North": (0, 1), "South": (0, -1), "East": (1, 0), "West": (-1, 0)}[
            direction
        ]
        old = self.position
        nxt = old[0] + dx, old[1] + dy
        growing = old == self.apple
        if not (0 <= nxt[0] < self.size and 0 <= nxt[1] < self.size):
            self.collisions.append("edge")
            return False
        if nxt in self.tail:
            # The last tail tile becomes traversable when it will move away.
            if growing or nxt != self.tail[-1] or len(self.tail) >= self.size**2 - 1:
                self.collisions.append("tail")
                return False
        self.position = nxt
        if growing:
            self.apple = self.next_apple
            self.next_apple = self.choose()
            self.tail.insert(0, old)
        elif self.tail:
            self.tail.pop()
            self.tail.insert(0, old)
        if self.next_apple == old:
            self.next_apple = self.choose()
        # Native measure substitutes the last free tile near a complete tail.
        if self.apple == nxt and self.next_apple in self.tail:
            self.next_apple = self.choose()
        return True

    def api(self, module):
        return patch.multiple(
            module,
            Items=ITEMS,
            Hats=symbols("Dinosaur_Hat Straw_Hat"),
            num_items=lambda _: self.stock,
            num_drones=lambda: 1,
            get_world_size=lambda: self.size,
            get_pos_x=lambda: self.position[0],
            get_pos_y=lambda: self.position[1],
            clear=self.clear,
            move=self.move,
            measure=self.measure,
            change_hat=self.hat,
            quick_print=lambda *args: None,
            **DIRECTIONS,
            create=True,
        )


class CheeseLeaderboardTests(unittest.TestCase):
    def test_candidates_are_standalone_inert_and_use_official_targets(self):
        for name, (_, target) in CANDIDATES.items():
            with self.subTest(name=name):
                tree = ast.parse((SAVE / (name + ".py")).read_text(encoding="utf-8"))
                self.assertFalse(
                    any(
                        isinstance(n, (ast.Import, ast.ImportFrom))
                        for n in ast.walk(tree)
                    )
                )
                self.assertEqual(load(name).TARGET, target)

    def test_satisfied_targets_do_not_touch_the_field(self):
        for name in CANDIDATES:
            module = load(name)
            with patch.multiple(
                module, Items=ITEMS, num_items=lambda _: 100, create=True
            ):
                self.assertTrue(module.run(10))

    def test_power_reaches_goal_and_joins_at_different_capacities(self):
        for capacity in (1, 2, 4, 32):
            field, module = (
                Field(ws=4, capacity=capacity),
                load("leaderboard_power_columns"),
            )
            with field.api(module, get_time=lambda: field.calls / 100):
                self.assertTrue(module.run(8))
            self.assertGreaterEqual(field.stock["Power"], 9)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_power_preserves_immature_sunflowers(self):
        field, module = Field(), load("leaderboard_power_columns")
        field.entities[(0, 0)] = "Sunflower"
        field.unripe[(0, 0)] = 100
        with field.api(module, get_time=lambda: field.calls / 100):
            self.assertTrue(module._column(3, 1))
        self.assertEqual(field.entities[(0, 0)], "Sunflower")
        self.assertFalse(any(pos == (0, 0) for pos, _ in field.plants))

    def test_power_parent_failure_still_joins_workers(self):
        field, module = Field(ws=4, capacity=2), load("leaderboard_power_columns")
        field.fail_plant = (1, 0)
        with field.api(module, get_time=lambda: field.calls / 100):
            self.assertFalse(module.run(8))
        self.assertEqual(field.spawned, field.joined)
        self.assertEqual(len(field.joined), 1)

    def test_power_stalled_growth_is_bounded(self):
        field, module = Field(), load("leaderboard_power_columns")
        for y in range(3):
            field.entities[(0, y)] = "Sunflower"
            field.unripe[(0, y)] = 10000
        with field.api(module, get_time=lambda: field.calls * 10):
            self.assertFalse(module._column(3, 10))
        self.assertLess(field.calls, 100)

    def test_maze_places_exactly_one_drone_per_tile_and_uses_resized_dose(self):
        for capacity, size in ((9, 3), (16, 4), (25, 5), (32, 5)):
            field, module = MazeField(capacity), load("leaderboard_gold_reuse")
            watched = []

            def watch(dose, target):
                watched.append(field.pos())
                self.assertEqual(dose, size * 32)
                field.stock["Gold"] = target
                return True

            with (
                field.api(
                    module,
                    max_drones=lambda: capacity,
                    set_world_size=field.resize,
                    get_time=lambda: field.calls / 100,
                ),
                patch.object(module, "_watch", side_effect=watch),
            ):
                self.assertTrue(module.run(100))
            self.assertEqual(field.ws, size)
            self.assertEqual(field.doses, [size * 32])
            self.assertEqual(len(field.spawned), size * size - 1)
            self.assertEqual(len(set(watched)), size * size)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_maze_rejects_insufficient_capacity_before_clearing_or_resizing(self):
        for capacity in (1, 2, 4, 8):
            module = load("leaderboard_gold_reuse")
            field = MazeField(capacity)
            resize, clear = Mock(), Mock()
            with field.api(
                module,
                max_drones=lambda: capacity,
                set_world_size=resize,
                clear=clear,
            ):
                self.assertFalse(module.run(1))
            resize.assert_not_called()
            clear.assert_not_called()

    def test_maze_creation_failure_still_joins_every_worker(self):
        module, field = load("leaderboard_gold_reuse"), MazeField(9)
        with (
            field.api(
                module,
                max_drones=lambda: 9,
                set_world_size=field.resize,
                use_item=lambda *args: False,
            ),
            patch.object(module, "_watch", return_value=False),
        ):
            self.assertFalse(module.run(10))
        self.assertEqual(len(field.joined), 8)
        self.assertEqual(field.spawned, field.joined)

    def test_maze_recycles_300_times_then_harvests_and_recreates(self):
        module = load("leaderboard_gold_reuse")
        state = dict(stock=0, reuses=0, harvests=0, creations=0, entity="Treasure")

        def use(item, amount):
            self.assertEqual((item, amount), ("Weird_Substance", 160))
            if state["entity"] == "Bush":
                state["entity"] = "Treasure"
                state["creations"] += 1
                return True
            if state["reuses"] == 300:
                return False
            state["reuses"] += 1
            state["stock"] += 25
            return True

        def harvest():
            self.assertEqual(state["reuses"], 300)
            state.update(reuses=0, entity=None)
            state["harvests"] += 1
            state["stock"] += 25
            return True

        def plant(entity):
            state["entity"] = entity
            return True

        with patch.multiple(
            module,
            Items=ITEMS,
            Entities=symbols("Treasure Bush"),
            num_items=lambda item: state["stock"] if item == "Gold" else 1000000,
            get_time=lambda: 0,
            get_entity_type=lambda: state["entity"],
            can_harvest=lambda: True,
            use_item=use,
            harvest=harvest,
            plant=plant,
            create=True,
        ):
            self.assertTrue(module._watch(160, 302 * 25))
        self.assertEqual(state["harvests"], 1)
        self.assertEqual(state["creations"], 1)
        self.assertEqual(state["stock"], 302 * 25)

    def test_maze_waits_for_relocation_and_stops_if_no_drone_makes_progress(self):
        module, clock = load("leaderboard_gold_reuse"), iter(range(0, 1000, 61))
        use = Mock()
        with patch.multiple(
            module,
            Items=ITEMS,
            Entities=symbols("Treasure"),
            num_items=lambda item: 1000 if item == "Weird_Substance" else 0,
            get_time=lambda: next(clock),
            get_entity_type=lambda: "Treasure",
            can_harvest=lambda: False,
            use_item=use,
            create=True,
        ):
            self.assertFalse(module._watch(160, 1))
        use.assert_not_called()

    def test_dinosaur_hybrid_handles_seeded_moving_tails(self):
        for size in (4, 6, 8):
            for seed in range(12):
                with self.subTest(size=size, seed=seed):
                    module, snake = load("leaderboard_bone_hybrid"), Snake(size, seed)
                    with snake.api(module):
                        self.assertTrue(module.run(1))
                    self.assertEqual(snake.hats, ["Dinosaur_Hat", "Straw_Hat"])
                    self.assertEqual(snake.stock, (size * size - 1) ** 2)
                    self.assertFalse(snake.tail)
                    self.assertNotIn("edge", snake.collisions)

    def test_dinosaur_hybrid_fills_the_official_32_by_32_field(self):
        module, snake = load("leaderboard_bone_hybrid"), Snake(32, 0)
        with snake.api(module):
            self.assertTrue(module.run(1))
        self.assertEqual(snake.stock * 32, module.TARGET)
        self.assertEqual(snake.collisions, ["tail"])

    def test_dinosaur_restores_straw_after_a_failed_move_or_missing_apple(self):
        for missing_apple in (False, True):
            module, snake = load("leaderboard_bone_hybrid"), Snake(8, 0)
            snake.force_failure = not missing_apple
            with (
                snake.api(module),
                patch.object(
                    module,
                    "measure",
                    return_value=None if missing_apple else (1, 1),
                ),
            ):
                self.assertFalse(module.run(1))
            self.assertEqual(snake.hats, ["Dinosaur_Hat", "Straw_Hat"])


if __name__ == "__main__":
    unittest.main()
