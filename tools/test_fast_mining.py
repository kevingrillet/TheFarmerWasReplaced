"""Concurrent shaft ownership fixtures, not native physics or a speed benchmark."""

import copy
import importlib
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from test_producer_contract import Symbols

fast = importlib.import_module("story_mining_infinite_fast")
backend = fast.story_mining_infinite_explosive


class Shaft:
    """Dig changes shared terrain before its simulated action wait, as native does."""

    def __init__(self, capacity=4, bottom=20000, delay=0):
        self.capacity, self.bottom, self.delay = capacity, bottom, delay
        self.local = threading.local()
        self.depths, self.specials, self.items = (
            {},
            {},
            {"Block": 1000000, "Power": 1000000, "Dynamite": 0},
        )
        self.pool = ThreadPoolExecutor(max_workers=max(1, capacity - 1))
        self.lock = threading.Lock()
        self.pending, self.spawned, self.joined, self.digs, self.hats = (
            {},
            [],
            [],
            [],
            [],
        )
        self.inflight = self.peak = self.worlds = 0
        self.reject, self.fail_depth = set(), None
        self.overlap = threading.Event()
        self.reveal_neighbors = False

    def pos(self):
        return getattr(self.local, "pos", (0, 0))

    def z(self, direction=None):
        x, y = self.pos()
        if direction:
            dx, dy = {
                "North": (0, 1),
                "East": (1, 0),
                "South": (0, -1),
                "West": (-1, 0),
            }[direction]
            x, y = (x + dx) % 8, (y + dy) % 8
        with self.lock:
            result = -self.depths.get((x, y), 0)
        if self.capacity > 1:
            time.sleep(0)  # Force observations/dig calls to interleave in tests.
        return result

    def ground(self, direction=None):
        x, y = self.pos()
        if direction:
            dx, dy = {
                "North": (0, 1),
                "East": (1, 0),
                "South": (0, -1),
                "West": (-1, 0),
            }[direction]
            x, y = (x + dx) % 8, (y + dy) % 8
        depth = self.depths.get((x, y), 0)
        if depth >= self.bottom:
            return "Bedrock"
        return self.specials.get((x, y, depth), "Rock")

    def move(self, direction):
        x, y = self.pos()
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        self.local.pos = (x + dx) % 8, (y + dy) % 8
        return True

    def dig(self):
        with self.lock:
            depth = self.depths.get(self.pos(), 0)
            if depth == self.fail_depth:
                return
            if depth >= self.bottom:
                raise AssertionError("dug Bedrock")
            self.digs.append((self.pos(), depth, self.ground()))
            self.depths[self.pos()] = depth + 1
            if self.reveal_neighbors:
                self.depths[1, 0] = depth
            self.inflight += 1
            self.peak = max(self.peak, self.inflight)
            if self.inflight >= 2:
                self.overlap.set()
        if self.delay:
            self.overlap.wait(1)
            time.sleep(self.delay)
        with self.lock:
            self.inflight -= 1

    def spawn(self, function, *args):
        owned = args[0]
        if next(iter(owned)) in self.reject:
            return None
        origin = self.pos()
        arguments = copy.deepcopy(args)

        def task():
            self.local.pos = origin
            return function(*arguments)

        handle = len(self.spawned) + 1
        self.spawned.append(handle)
        self.pending[handle] = self.pool.submit(task)
        return handle

    def wait(self, handle):
        result = self.pending.pop(handle).result(timeout=5)
        self.joined.append(handle)
        return result

    def clear(self):
        if self.pending or self.inflight:
            raise AssertionError("world cleared with active drillers")
        self.worlds += 1
        self.depths.clear()

    def fund(self, item, target):
        if self.worlds or self.pending or self.digs:
            raise AssertionError("funding during descent")
        self.items[item] = max(self.items.get(item, 0), target)
        return True

    @contextmanager
    def api(self):
        symbols = Symbols()
        bindings = dict(
            Items=symbols,
            Grounds=symbols,
            Hats=symbols,
            Unlocks=symbols,
            num_unlocked=lambda _: 1,
            get_world_size=lambda: 8,
            get_pos_x=lambda: self.pos()[0],
            get_pos_y=lambda: self.pos()[1],
            get_pos_z=self.z,
            get_ground_type=self.ground,
            get_time=time.monotonic,
            max_drones=lambda: self.capacity,
            num_drones=lambda: 1 + len(self.pending),
            num_items=lambda item: self.items.get(item, 0),
            spawn_drone=self.spawn,
            wait_for=self.wait,
            dig=self.dig,
            clear=self.clear,
            move=self.move,
            change_hat=self.hats.append,
            quick_print=lambda *_: None,
            North="North",
            East="East",
            South="South",
            West="West",
        )
        try:
            with ExitStack() as stack:
                for module in (
                    fast,
                    backend,
                    fast.utils_mine,
                    fast.utils_mine.utils_move,
                    fast.utils_farm,
                ):
                    stack.enter_context(patch.multiple(module, **bindings, create=True))
                stack.enter_context(patch.object(fast, "WORKER_TIMEOUT", 0.2))
                yield
        finally:
            self.pool.shutdown(wait=True)


class FastMiningTests(unittest.TestCase):
    def test_ordinary_drill_actions_overlap_and_every_depth_is_owned_once(self):
        field = Shaft(delay=0.002)
        with field.api():
            self.assertTrue(fast._pipeline(-40, [], set()))
        self.assertGreaterEqual(field.peak, 2)
        self.assertEqual(sorted(d for _, d, _ in field.digs), list(range(40)))
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_all_drillers_stop_on_selected_ground_despite_interleaved_reads(self):
        for capacity in (1, 2, 4, 32):
            field = Shaft(capacity)
            field.specials[0, 0, 6] = "Mushroom"
            with self.subTest(capacity=capacity), field.api():
                self.assertTrue(fast._pipeline(-24, ["Mushroom"], set()))
            self.assertEqual(field.depths[0, 0], 6)
            self.assertTrue(all(g != "Mushroom" for _, _, g in field.digs))
            self.assertEqual(field.spawned, field.joined)

    def test_spawn_refusals_become_parent_slots_without_a_deadlock(self):
        for rejected in ({0, 2}, {0, 1, 2}):
            field = Shaft()
            field.reject = rejected
            with field.api():
                self.assertTrue(fast._pipeline(-20, [], set()))
            self.assertEqual(field.depths[0, 0], 20)
            self.assertEqual(field.spawned, field.joined)

    def test_stops_when_a_special_neighbor_is_exposed_between_checkpoints(self):
        field = Shaft()
        field.reveal_neighbors = True
        field.specials[1, 0, 6] = "Sand"
        with field.api():
            self.assertTrue(fast._pipeline(-24, ["Sand"], set()))
        self.assertEqual(field.depths[0, 0], 7)
        self.assertEqual(field.spawned, field.joined)
        self.assertEqual(field.pos(), (0, 0))

    def test_ignored_neighbor_does_not_cause_repeated_stops(self):
        field = Shaft()
        field.specials[1, 0, 0] = "Basalt"
        with field.api():
            self.assertTrue(fast._pipeline(-8, ["Basalt"], {(1, 0, 0, "Basalt")}))
        self.assertEqual(field.depths[0, 0], 8)
        self.assertEqual(field.spawned, field.joined)

    def test_failed_slot_times_out_followers_and_joins_everyone(self):
        field = Shaft()
        field.fail_depth = 3
        with field.api(), patch.object(fast, "WORKER_TIMEOUT", 0.03):
            self.assertFalse(fast._pipeline(-20, [], set()))
        self.assertEqual(field.depths[0, 0], 3)
        self.assertEqual(field.spawned, field.joined)

    def test_descent_continues_beyond_10000_without_fuel_or_world_renewal(self):
        field = Shaft(capacity=1)
        with field.api(), patch.object(fast.resource_manager, "farm_current") as fund:
            self.assertNotIn("Dynamite", fast.requirements([]))
            self.assertTrue(fast.run(10002, []))
        self.assertEqual(field.depths[0, 0], 10002)
        self.assertEqual(field.worlds, 0)
        self.assertNotIn("Explosive_Drill", field.hats)
        fund.assert_not_called()

    def test_collectors_only_run_after_pipeline_children_join(self):
        field = Shaft()
        field.specials[0, 0, 6] = "Dynamite"

        def collect(hit, parallel, ignored):
            self.assertFalse(field.pending or field.inflight)
            self.assertEqual(hit, (0, 0, -6, "Dynamite"))
            field.specials.pop((0, 0, 6))
            return True

        with (
            field.api(),
            patch.object(backend, "collect_activity", side_effect=collect) as activity,
        ):
            self.assertTrue(fast.run(20, ["minesweeper"]))
        activity.assert_called_once()
        self.assertEqual(field.depths[0, 0], 20)
        self.assertEqual(field.spawned, field.joined)

    def test_consumed_stratum_marker_does_not_stop_the_pipeline(self):
        field = Shaft()
        field.specials[0, 0, 0] = "Basalt"
        with field.api():
            self.assertTrue(fast._pipeline(-8, ["Basalt"], {(-1, -1, 0, "Basalt")}))
        self.assertEqual(field.depths[0, 0], 8)

    def test_fresh_world_funding_precedes_all_drilling(self):
        field = Shaft()
        with (
            field.api(),
            patch.object(
                fast.resource_manager, "farm_current", side_effect=field.fund
            ) as fund,
        ):
            self.assertTrue(fast.produce_world(12, [], True))
        self.assertEqual(field.worlds, 1)
        self.assertTrue(all(call.args[0] != "Dynamite" for call in fund.call_args_list))
        self.assertEqual(field.depths[0, 0], 12)

    def test_bad_settings_fail_before_reset_or_spawns(self):
        field = Shaft()
        with field.api():
            self.assertFalse(fast.run(0))
            self.assertFalse(fast.run(20, ["typo"]))
            with patch.object(fast, "DRONE_LIMIT", 0):
                self.assertFalse(fast.run(20))
        self.assertFalse(field.worlds or field.spawned or field.digs)
