"""Bamboo occupancy/fruit regression fixture, not native scheduling or timing."""

import importlib
import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from test_producer_contract import Symbols

bamboo = importlib.import_module("farm_bamboo")
mining = importlib.import_module("utils_mine")


class BambooField:
    """Queued children retain the waiting parent's position and hover height.

    Growth advances only during _wait(), using the installed Bamboo controller's
    occupancy, fruit-stop and cutting rules. Action durations are not emulated.
    """

    def __init__(self, capacity=4, ws=4):
        self.capacity = capacity
        self.ws = ws
        self.active = 0
        self.drones = {0: [0, 0, 1]}
        self.pending = {}
        self.spawned, self.joined, self.final_cuts = [], [], []
        self.stems = {}
        self.stock = 0
        self.rice = 1000000
        self.fruits = (3, 6, 9)
        self.time = 0
        self.wait_sizes = []
        self.planted = []

    def pos(self):
        return tuple(self.drones[self.active][:2])

    def plant(self, entity):
        if self.pos() in self.stems or self.rice < 50:
            return False
        self.rice -= 50
        self.drones[self.active][2] = 1
        self.stems[self.pos()] = [1, 0]
        self.planted.append(self.pos())
        return True

    def advance(self, seconds):
        self.wait_sizes.append(len(self.stems))
        self.time += seconds
        for _ in range(int(seconds)):
            for (x, y), stem in self.stems.items():
                blocked = any(
                    drone[:2] == [x, y] and drone[2] <= stem[0]
                    for drone in self.drones.values()
                )
                if not blocked and stem[0] < self.fruits[stem[1]]:
                    stem[0] += 1

    def hover(self, height):
        stem = self.stems.get(self.pos())
        if not 0 <= height <= 18 or (stem and height < stem[0]):
            return False
        self.drones[self.active][2] = height
        return True

    def move(self, direction):
        drone = self.drones[self.active]
        dx, dy = {
            "North": (0, 1),
            "East": (1, 0),
            "South": (0, -1),
            "West": (-1, 0),
        }[direction]
        drone[0], drone[1] = (drone[0] + dx) % self.ws, (drone[1] + dy) % self.ws
        stem = self.stems.get(self.pos())
        height = drone[2]
        if stem and height < stem[0]:
            self.stock += (stem[0] - height) ** 2
            if height == 0:
                self.final_cuts.append(stem[0])
                del self.stems[self.pos()]
            else:
                if height >= self.fruits[stem[1]] - 1:
                    stem[1] = min(stem[1] + 1, 2)
                else:
                    stem[1] = 0
                    while stem[1] < 2 and height >= self.fruits[stem[1]]:
                        stem[1] += 1
                stem[0] = height
        return True

    def spawn(self, worker, *args):
        if len(self.drones) >= self.capacity:
            return None
        handle = len(self.spawned) + 1
        self.spawned.append(handle)
        self.drones[handle] = self.drones[self.active].copy()
        self.pending[handle] = worker, args
        return handle

    def wait_for(self, handle):
        worker, args = self.pending.pop(handle)
        parent, self.active = self.active, handle
        try:
            return worker(*args)
        finally:
            self.joined.append(handle)
            del self.drones[handle]
            self.active = parent

    @contextmanager
    def api(self):
        bindings = dict(
            Items=Symbols(),
            Grounds=Symbols(),
            Entities=Symbols(),
            Unlocks=Symbols(),
            num_unlocked=lambda _: 1,
            North="North",
            East="East",
            South="South",
            West="West",
            num_items=lambda item: self.stock if item == "Bamboo" else self.rice,
            get_cost=lambda _: {"Rice": 50},
            num_drones=lambda: len(self.drones),
            quick_print=lambda *_: None,
            get_time=lambda: self.time,
            get_world_size=lambda: self.ws,
            get_pos_x=lambda: self.pos()[0],
            get_pos_y=lambda: self.pos()[1],
            get_ground_type=lambda: "Soil",
            plant=self.plant,
            measure=lambda: self.fruits[self.stems[self.pos()][1]] - 1,
            hover=self.hover,
            move=self.move,
            spawn_drone=self.spawn,
            wait_for=self.wait_for,
        )
        with ExitStack() as stack:
            for module in (bamboo, mining, mining.utils_move, mining.utils_farm):
                stack.enter_context(patch.multiple(module, **bindings, create=True))
            stack.enter_context(patch.object(bamboo, "_wait", self.advance))
            yield


class BambooTests(unittest.TestCase):
    def test_second_wave_waits_for_complete_harvest_and_join_of_first_wave(self):
        field = BambooField(4)
        original = bamboo._batch
        observed = []

        def checked(target, x, steps):
            if x % 2:
                self.assertFalse(any(pos[0] % 2 == 0 for pos in field.stems))
                self.assertTrue(
                    all(args[1] % 2 == 1 for _, args in field.pending.values())
                )
                self.assertEqual(len(field.joined), 1)
            observed.append(x)
            return original(target, x, steps)

        with (
            field.api(),
            patch.object(bamboo.utils_mine, "prepare", return_value=True),
            patch.object(bamboo, "_batch", side_effect=checked),
        ):
            self.assertTrue(bamboo.produce_multi(10000))
        self.assertEqual(observed, [2, 0, 3, 1])
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.stems)

    def test_two_waves_are_funded_before_prepare(self):
        field = BambooField(4)
        field.rice = 400  # Enough for the old half-field, not the two waves.
        with field.api(), patch.object(bamboo.utils_mine, "prepare") as prepare:
            self.assertEqual(bamboo.requirements(10000), {"Rice": 800})
            self.assertFalse(bamboo.produce_multi(10000))
        prepare.assert_not_called()
        self.assertFalse(field.planted or field.spawned)

    def test_goal_reached_in_first_wave_skips_corridor_planting(self):
        field = BambooField(4)
        with field.api(), patch.object(bamboo.utils_mine, "prepare", return_value=True):
            self.assertTrue(bamboo.produce_multi(600))
        self.assertGreaterEqual(field.stock, 600)
        self.assertEqual(set(field.planted), {(x, y) for x in (0, 2) for y in range(4)})
        self.assertEqual(field.spawned, field.joined)

    def test_failed_first_wave_joins_workers_without_starting_second(self):
        field = BambooField(4)
        original = field.plant

        def plant(entity):
            if field.pos()[0] == 2:
                return False
            return original(entity)

        with (
            field.api(),
            patch.object(bamboo, "plant", side_effect=plant),
            patch.object(bamboo.utils_mine, "prepare", return_value=True),
        ):
            self.assertFalse(bamboo.produce_multi(10000))
        self.assertFalse(any(x % 2 for x, y in field.planted))
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_odd_field_uses_only_complete_crop_corridor_pairs(self):
        field = BambooField(4, ws=3)
        with field.api(), patch.object(bamboo.utils_mine, "prepare", return_value=True):
            self.assertEqual(bamboo.requirements(10000), {"Rice": 300})
            self.assertTrue(bamboo.produce_multi(10000))
        self.assertEqual(set(field.planted), {(x, y) for x in (0, 1) for y in range(3)})
        self.assertEqual(field.final_cuts, [9] * 6)
        self.assertFalse(field.stems)

    def test_normal_producer_owns_spaced_columns_and_plants_before_waiting(self):
        for parallel, capacity in ((False, 1), (True, 1), (True, 2), (True, 4)):
            with self.subTest(parallel=parallel, capacity=capacity):
                field = BambooField(capacity)
                with (
                    field.api(),
                    patch.object(bamboo.utils_farm, "preflight", return_value=True),
                    patch.object(bamboo.utils_mine, "prepare", return_value=True),
                    patch.object(bamboo, "requirements", return_value={}),
                ):
                    self.assertTrue(bamboo._produce(10000, parallel))
                self.assertEqual(
                    set(field.planted), {(x, y) for x in range(4) for y in range(4)}
                )
                self.assertGreaterEqual(field.wait_sizes[0], 4)
                self.assertEqual(field.final_cuts, [9] * 16)
                self.assertEqual(field.stock, 83 * 16)
                self.assertEqual(field.spawned, field.joined)
                self.assertFalse(field.pending)

    def test_unadvanced_fruit_fails_finitely_after_retries(self):
        field = BambooField(1)

        def no_growth(seconds):
            field.time += seconds

        with field.api(), patch.object(bamboo, "_wait", no_growth):
            self.assertFalse(bamboo._batch(10000, 0, 2))
        self.assertLess(field.time, 30)
        self.assertEqual(field.pos()[0], 1)

    def test_waiting_parent_blocks_growth_even_after_child_leaves(self):
        field = BambooField()
        field.plant("Bamboo")
        field.active = field.spawn(lambda: True)
        field.move("North")
        field.advance(10)
        self.assertEqual(field.stems[(0, 0)][0], 1)
        field.drones[0][1] = 1
        field.advance(10)
        self.assertEqual(field.stems[(0, 0)][0], 3)

    def test_columns_reach_third_fruit_including_last_column(self):
        for parallel, capacity, columns, steps in (
            (False, 1, 1, 1),
            (True, 4, 1, 1),
            (True, 1, 4, 2),
            (True, 2, 4, 2),
            (True, 4, 4, 2),
            (True, 8, 4, 2),
        ):
            with self.subTest(
                parallel=parallel, capacity=capacity, columns=columns, steps=steps
            ):
                field = BambooField(capacity)
                with field.api():
                    self.assertTrue(
                        mining.run_columns(
                            bamboo._column, 10000, columns, steps, parallel
                        )
                    )
                self.assertEqual(field.final_cuts, [9] * (columns * steps))
                self.assertEqual(field.stock, 83 * columns * steps)
                self.assertEqual(field.joined, field.spawned)
                self.assertEqual(set(field.drones), {0})
                self.assertFalse(field.pending)


if __name__ == "__main__":
    unittest.main()
