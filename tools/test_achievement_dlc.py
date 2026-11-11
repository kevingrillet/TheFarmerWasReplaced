"""Achievement action/geometry fixtures, without Steam writes or native timing."""

import importlib
import random
import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import Mock, patch

from test_mining_multi import MiningField
from test_producer_contract import Symbols

achievements = importlib.import_module("ZZAchievementDLC")
infinite = importlib.import_module("story_infinite")


class PyramidField:
    """Limestone base with native sand support and completion geometry."""

    def __init__(self, width=5):
        self.width = width
        self.x = self.y = 0
        self.columns = {(x, y): [] for x in range(width) for y in range(width)}
        self.complete = self.harvested = False
        self.layers = []
        self.auto_clear = False
        self.dug = 0

    def go_to(self, x, y):
        self.x, self.y = x, y
        return True

    def height(self):
        return len(self.columns[self.x, self.y])

    def place(self, ground):
        height = self.height()
        if ground == "Sand" and height:
            for x in range(self.x - 1, self.x + 2):
                for y in range(self.y - 1, self.y + 2):
                    if len(self.columns.get((x, y), [])) < height:
                        raise AssertionError("sand placed without its 3x3 support")
        self.columns[self.x, self.y].append(ground)
        self.layers.append(height)
        allowed = {block for column in self.columns.values() for block in column}
        shape = all(
            len(column) == 1 + min(x, y, self.width - 1 - x, self.width - 1 - y)
            for (x, y), column in self.columns.items()
        )
        if shape and (allowed == {"Sand"} or allowed <= {"Block_Red", "Block_Blue"}):
            self.complete = True
            if self.auto_clear:
                for column in self.columns.values():
                    column.clear()
        return True

    def dig(self):
        self.columns[self.x, self.y].pop()
        self.dug += 1

    def harvest(self):
        if not self.complete or (self.x, self.y) != (self.width // 2,) * 2:
            raise AssertionError("pyramid reward harvested before completion")
        self.harvested = True
        return True

    @contextmanager
    def api(self):
        with (
            patch.object(achievements.utils_mine, "go_to", self.go_to),
            patch.multiple(
                achievements,
                Grounds=Symbols(),
                Entities=Symbols(),
                Unlocks=Symbols(),
                Hats=Symbols(),
                change_hat=lambda _: None,
                get_pos_z=self.height,
                get_pos_x=lambda: self.x,
                get_pos_y=lambda: self.y,
                get_world_size=lambda: self.width,
                get_ground_type=lambda: "Sand" if self.height() else "Limestone",
                dig=self.dig,
                place=self.place,
                get_entity_type=lambda: "Sunflower" if self.complete else None,
                harvest=self.harvest,
                num_unlocked=lambda _: 0,
                create=True,
            ),
        ):
            yield


class ParallelPyramidField(PyramidField):
    """Queued drone cursors; geometry/joins, not native concurrent timing."""

    def __init__(self, width=7, capacity=4):
        super().__init__(width)
        self.capacity = capacity
        self.pending = {}
        self.spawned, self.joined = [], []
        self.spawn_layers = []
        self.placed_grounds = []
        self.cleared_grounds, self.worker_digs = [], []
        self.in_worker = False
        self.reject_spawn = False
        self.fail_place = self.fail_move = None
        self.auto_clear = True

    def move(self, direction):
        if self.fail_move == (self.x, self.y):
            return False
        dx, dy = {"East": (1, 0), "West": (-1, 0), "North": (0, 1), "South": (0, -1)}[
            direction
        ]
        self.x, self.y = (self.x + dx) % self.width, (self.y + dy) % self.width
        return True

    def dig(self):
        self.cleared_grounds.append(self.columns[self.x, self.y][-1])
        self.worker_digs.append(self.in_worker)
        return super().dig()

    def place(self, ground):
        if self.complete:
            raise AssertionError("placement continued after native completion")
        if self.fail_place == (self.x, self.y):
            return False
        height = self.height()
        if height:
            for x in range(height - 1, self.width - height + 1):
                for y in range(height - 1, self.width - height + 1):
                    if len(self.columns[x, y]) < height:
                        raise AssertionError(
                            "next floor started before previous floor finished"
                        )
        self.placed_grounds.append(ground)
        return super().place(ground)

    def spawn(self, function, *args):
        if self.reject_spawn or len(self.pending) >= self.capacity - 1:
            return None
        if any(task[1][1] != args[1] for task in self.pending.values()):
            raise AssertionError("new floor spawned before all previous workers joined")
        handle = len(self.spawned) + 1
        self.pending[handle] = function, args, (self.x, self.y)
        self.spawned.append(handle)
        self.spawn_layers.append(args[1])
        return handle

    def wait_for(self, handle):
        function, args, origin = self.pending.pop(handle)
        parent, previous = (self.x, self.y), self.in_worker
        self.x, self.y = origin
        self.in_worker = True
        try:
            result = function(*args)
        finally:
            self.x, self.y = parent
            self.in_worker = previous
        self.joined.append(handle)
        return result

    def harvest(self):
        if self.in_worker or self.pending:
            raise AssertionError("reward harvested before parent joined all children")
        return super().harvest()

    @contextmanager
    def api(self, offset=(0, 0), z=0):
        with (
            super().api(),
            patch.multiple(
                achievements,
                num_unlocked=lambda _: 1,
                max_drones=lambda: self.capacity,
                spawn_drone=self.spawn,
                wait_for=self.wait_for,
                move=self.move,
                get_ground_type=lambda: self.columns[self.x, self.y][-1]
                if self.height()
                else "Limestone",
                get_pos_x=lambda: self.x + offset[0],
                get_pos_y=lambda: self.y + offset[1],
                get_pos_z=lambda: z + self.height(),
                get_world_size=lambda: self.width + max(offset),
                North="North",
                South="South",
                East="East",
                West="West",
                create=True,
            ),
            patch.object(
                achievements.utils_farm,
                "can_start_phase",
                side_effect=lambda: not self.pending,
            ),
            patch.multiple(
                achievements.utils_farm, wait_for=self.wait_for, create=True
            ),
            patch.object(
                achievements.utils_mine,
                "go_to",
                side_effect=lambda x, y: self.go_to(x - offset[0], y - offset[1]),
            ),
        ):
            yield


class AchievementTests(unittest.TestCase):
    def test_parallel_clearance_finds_an_offset_buried_footprint(self):
        for capacity in (2, 4, 32):
            field = MiningField(ws=12, capacity=capacity)
            field.layers = {
                (x, y): ["Rock"] * 7 + ["Bedrock"]
                for x in range(field.ws)
                for y in range(field.ws)
            }
            for x in range(2, 7):
                for y in range(3, 8):
                    field.layers[x, y][3] = "Limestone"
            field.layers[3, 4][2] = "Sand"
            field.x, field.y = 4, 5
            field.depths[4, 5] = 3
            with self.subTest(capacity=capacity), field.api(achievements):
                self.assertEqual(achievements._pyramid_base(True), (2, 3, 5, -3))
            self.assertFalse(any(g in ("Sand", "Limestone") for _, g in field.digs))
            self.assertTrue(
                all(
                    field.depths.get((x, y), 0) == (2 if (x, y) == (3, 4) else 3)
                    for x in range(2, 7)
                    for y in range(3, 8)
                )
            )
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_parallel_clearance_removes_rubble_without_digging_preserved_sand(self):
        for capacity in (2, 4, 32):
            field = ParallelPyramidField(width=7, capacity=capacity)
            for (x, y), column in field.columns.items():
                if (x, y) != (0, 0):
                    column += ["Sand"] * min(1, x, y, 6 - x, 6 - y) + ["Rock"] * 2
            sand = sum(c.count("Sand") for c in field.columns.values())
            with self.subTest(capacity=capacity), field.api():
                self.assertEqual(achievements._pyramid_base(True), (0, 0, 7, 0))
            self.assertEqual(sum(c.count("Sand") for c in field.columns.values()), sand)
            self.assertEqual(set(field.cleared_grounds), {"Rock"})
            self.assertTrue(any(field.worker_digs))
            self.assertTrue(field.spawned)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_parallel_clearance_failure_joins_ray_workers(self):
        field = ParallelPyramidField(width=7, capacity=4)
        for pos, column in field.columns.items():
            if pos != (0, 0):
                column += ["Rock"] * 2

        def stuck():
            if (field.x, field.y) != (0, 1):
                field.dig()

        with field.api(), patch.object(achievements, "dig", side_effect=stuck):
            self.assertIsNone(achievements._pyramid_base(True))
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_largest_parallel_pyramid_places_every_block_before_parent_harvest(self):
        field = ParallelPyramidField(width=31, capacity=32)
        with field.api():
            self.assertTrue(achievements._restore_pyramid((0, 0, 31, 0), False))
        self.assertEqual(len(field.layers), 5456)
        self.assertEqual(field.layers, sorted(field.layers))
        self.assertTrue(field.harvested)
        self.assertEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_pyramid_building_uses_joined_parallel_floors(self):
        for capacity in (1, 2, 4, 32):
            for colored in (False, True):
                field = ParallelPyramidField(width=7, capacity=capacity)
                with self.subTest(capacity=capacity, colored=colored), field.api():
                    self.assertTrue(
                        achievements._restore_pyramid((0, 0, 7, 0), colored)
                    )
                self.assertTrue(field.harvested)
                self.assertEqual(field.spawned, field.joined)
                self.assertFalse(field.pending)
                if capacity > 1:
                    self.assertTrue(field.spawned)
                self.assertNotIn(3, field.spawn_layers)  # Apex belongs to the parent.

    def test_parallel_pyramid_reserves_an_existing_apex_until_every_worker_joined(self):
        field = ParallelPyramidField(width=7, capacity=4)
        for (x, y), column in field.columns.items():
            column += ["Sand"] * (1 + min(x, y, 6 - x, 6 - y))
        field.columns[0, 0].clear()
        with field.api():
            self.assertTrue(achievements._restore_pyramid((0, 0, 7, 0), False))
        self.assertTrue(field.harvested)
        self.assertEqual(field.dug, 1)
        self.assertEqual(len(field.layers), 2)  # Missing corner, then reserved apex.
        self.assertEqual(field.spawned, field.joined)

    def test_parallel_pyramid_supports_offset_and_negative_foundation_height(self):
        field = ParallelPyramidField(width=7, capacity=4)
        with field.api(offset=(3, 2), z=-40):
            self.assertTrue(achievements._restore_pyramid((3, 2, 7, -40), False))
        self.assertTrue(field.harvested)
        self.assertEqual(field.spawned, field.joined)

    def test_colored_current_pyramid_strips_sand_before_parallel_construction(self):
        field = ParallelPyramidField(width=7, capacity=4)
        for pos, column in field.columns.items():
            if pos != (0, 0):
                column.append("Sand")
        with field.api():
            result, base = achievements.collect_current_pyramid(True)
        self.assertTrue(result)
        self.assertEqual(base, (0, 0, 7, 0))
        self.assertEqual(field.dug, 48)
        self.assertEqual(set(field.placed_grounds), {"Block_Red"})
        self.assertTrue(field.harvested)
        self.assertEqual(field.spawned, field.joined)

    def test_parallel_pyramid_failures_join_children_before_stopping(self):
        for failure, position in (
            ("place", (0, 0)),
            ("place", (5, 0)),
            ("move", (5, 0)),
        ):
            field = ParallelPyramidField(width=7, capacity=4)
            setattr(field, "fail_" + failure, position)
            with self.subTest(failure=failure, position=position), field.api():
                self.assertFalse(achievements._restore_pyramid((0, 0, 7, 0), False))
            self.assertTrue(field.spawned)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)
            self.assertFalse(field.harvested)
            self.assertEqual(set(field.layers), {0})

    def test_refused_spawns_fall_back_without_omitting_any_rows(self):
        field = ParallelPyramidField(width=7, capacity=4)
        field.reject_spawn = True
        with field.api():
            self.assertTrue(achievements._restore_pyramid((0, 0, 7, 0), False))
        self.assertFalse(field.spawned)
        self.assertTrue(field.harvested)
        self.assertEqual(len(field.layers), 84)

    def test_completed_pyramid_is_harvested_without_another_construction(self):
        field = ParallelPyramidField(width=7, capacity=4)
        field.complete = True
        with field.api():
            self.assertTrue(achievements._restore_pyramid((0, 0, 7, 0), False))
        self.assertTrue(field.harvested)
        self.assertFalse(field.layers)
        self.assertFalse(field.spawned)

    def test_parallel_pyramid_refuses_unowned_workers_before_touching_the_apex(self):
        field = ParallelPyramidField(width=7, capacity=4)
        field.pending[99] = None
        with field.api():
            self.assertFalse(achievements._restore_pyramid((0, 0, 7, 0), False))
        self.assertFalse(field.layers)
        self.assertEqual(field.dug, 0)
        self.assertFalse(field.spawned)

    def test_explicit_single_keeps_the_existing_apex_and_early_completion(self):
        field = ParallelPyramidField(width=7, capacity=4)
        for (x, y), column in field.columns.items():
            column += ["Sand"] * (1 + min(x, y, 6 - x, 6 - y))
        field.columns[0, 0].clear()
        with field.api():
            self.assertTrue(achievements._restore_pyramid((0, 0, 7, 0), False, False))
        self.assertTrue(field.harvested)
        self.assertEqual(field.dug, 0)
        self.assertEqual(len(field.layers), 1)
        self.assertFalse(field.spawned)

    def test_task_sequence_keeps_order_skips_duplicates_and_continues_after_failure(
        self,
    ):
        size = [32]
        visited = []

        def task(name):
            visited.append((name, size[0]))
            if name == "rice_terrace":
                size[0] = 3
            return name != "matchmaker"

        with (
            self.api(
                get_world_size=lambda: size[0],
                set_world_size=lambda n: size.__setitem__(0, n),
            ),
            patch.object(achievements.utils_farm, "can_start_phase", return_value=True),
            patch.object(achievements, "run", side_effect=task),
        ):
            self.assertFalse(
                achievements.run_tasks(
                    ["rice_terrace", "matchmaker", "rice_terrace", "pyramid"]
                )
            )
        self.assertEqual(
            visited, [("rice_terrace", 32), ("matchmaker", 32), ("pyramid", 32)]
        )
        self.assertEqual(size[0], 32)

    def test_task_sequence_restores_field_after_last_task(self):
        size = [32]

        def task(name):
            size[0] = 16
            return True

        with (
            self.api(
                get_world_size=lambda: size[0],
                set_world_size=lambda n: size.__setitem__(0, n),
            ),
            patch.object(achievements.utils_farm, "can_start_phase", return_value=True),
            patch.object(achievements, "run", side_effect=task),
        ):
            self.assertTrue(achievements.run_tasks(["matchmaker"]))
        self.assertEqual(size[0], 32)

    def test_empty_sequence_does_no_game_work(self):
        with self.api(), patch.object(achievements, "run") as run:
            self.assertTrue(achievements.run_tasks([]))
        run.assert_not_called()

    def test_retired_ordinary_tasks_do_not_start_any_game_actions(self):
        for task in (
            "quick",
            "not_muchroom",
            "petrified_pumpkins",
            "professor_pumpkin",
            "dynamite_disposal",
            "resource_grind",
        ):
            with (
                self.subTest(task=task),
                self.api(),
                patch.object(achievements, "_prepare") as prepare,
            ):
                self.assertFalse(achievements.run(task))
            prepare.assert_not_called()

    def test_workers_prevent_start_and_last_unjoined_worker_prevents_success(self):
        for idle in ([False], [True, False]):
            with (
                self.api(),
                patch.object(
                    achievements.utils_farm, "can_start_phase", side_effect=idle
                ),
                patch.object(achievements, "run", return_value=True) as run,
            ):
                self.assertFalse(achievements.run_tasks(["pyramid"]))
            self.assertEqual(run.call_count, len(idle) - 1)

    def test_no_argument_run_uses_sequence_and_manual_task_stays_available(self):
        with (
            self.api(),
            patch.object(achievements, "run_tasks", return_value=True) as run,
        ):
            self.assertTrue(achievements.run())
        run.assert_called_once_with()
        with (
            self.api(),
            patch.object(achievements, "broken_hoe_unsafe", return_value=True) as hoe,
        ):
            self.assertTrue(achievements.run("broken_hoe"))
        hoe.assert_called_once_with()

    def test_default_sequence_is_manually_filtered_and_finite(self):
        already_done = {
            "petrified_pumpkins",
            "professor_pumpkin",
            "dynamite_disposal",
            "broken_hoe",
            "rice_terrace",
            "picasso",
            "skyscraper",
            "prospector",
            "explosive_drill",
            "miner_master",
            "dynamite_specialist",
        }
        self.assertFalse(already_done.intersection(achievements.TASKS))
        self.assertNotIn("quick", achievements.TASKS)
        self.assertNotIn("resource_grind", achievements.TASKS)
        self.assertEqual(len(achievements.TASKS), len(set(achievements.TASKS)))

    def test_pyramid_preserves_existing_sand_and_accepts_early_native_completion(self):
        field = PyramidField()
        for (x, y), column in field.columns.items():
            column += ["Sand"] * (1 + min(x, y, 4 - x, 4 - y))
        field.columns[0, 0].clear()
        field.auto_clear = True
        with field.api():
            base = achievements._pyramid_base(True)
            self.assertEqual(base, (0, 0, 5, 0))
            self.assertEqual(field.dug, 0)
            self.assertTrue(achievements._restore_pyramid(base, False))
        self.assertTrue(field.harvested)
        self.assertEqual(len(field.layers), 1)

    def test_colored_pyramid_strips_all_old_sand(self):
        field = PyramidField()
        for pos, column in field.columns.items():
            if pos != (0, 0):
                column += ["Sand"]
        with field.api():
            base = achievements._pyramid_base(False)
            self.assertEqual(field.dug, 24)
            self.assertTrue(achievements._restore_pyramid(base, True))
        self.assertTrue(field.harvested)
        self.assertEqual({b for c in field.columns.values() for b in c}, {"Block_Red"})

    def test_miner_master_measures_added_blocks_and_restores_hat(self):
        for gain, duration, expected in (
            (400000, 2, True),
            (0, 2, False),
            (1000000, 61, False),
        ):
            with self.subTest(gain=gain, duration=duration):
                stocks = {"Block": 5000000, "Dynamite": 3}
                now = [0]
                hats = []

                def dig():
                    now[0] += duration
                    stocks["Dynamite"] -= 1
                    stocks["Block"] += gain
                    return True

                with (
                    self.api(
                        num_items=lambda i: stocks.get(i, 0),
                        get_time=lambda: now[0],
                        change_hat=hats.append,
                    ),
                    patch.object(achievements, "_fund", return_value=True) as fund,
                    patch.object(achievements, "_prepare", return_value=True),
                    patch.object(achievements, "_dig_once", dig),
                ):
                    self.assertIs(achievements.miner_master(60, 3), expected)
                fund.assert_called_once_with("Dynamite", 3)
                self.assertEqual(hats, ["Explosive_Drill", "Straw_Hat"])

    def test_matchmaker_six_kinds_with_caveins_keeps_strict_threshold(self):
        from test_mushroom import StrataField

        for seed in range(3):
            with self.subTest(seed=seed):
                field = StrataField(ws=16, capacity=1, height=8, seed=seed)
                with (
                    field.api(
                        achievements,
                        push=field.push,
                        measure=field.measure,
                        random=field.random.random,
                    ),
                    patch.object(achievements, "_prepare", return_value=True),
                ):
                    self.assertTrue(achievements.matchmaker(10000, 16))
                self.assertGreater(200 * field.stock["Mushroom"], 95 * 256 * 8)
                self.assertGreater(field.losses, 0)

    def test_mushroom_compaction_routes_a_pair_without_drilling_mushrooms(self):
        from test_mushroom import StrataField

        for budget, expected in ((1, False), (30, True)):
            with self.subTest(budget=budget):
                field = StrataField(ws=3, capacity=1, top=2, height=1)
                field.depths = {(x, y): 3 for x in range(3) for y in range(3)}
                for pos in ((0, 0), (2, 2)):
                    field.depths[pos] = 2
                    field.kinds[*pos, 2] = 4
                surface = {
                    pos: (-d, field.block(pos, d)[1]) for pos, d in field.depths.items()
                }
                with field.api(achievements, push=field.push, measure=field.measure):
                    self.assertIs(
                        achievements._compact_mushrooms(surface, -3, 1, budget, 3),
                        expected,
                    )
                self.assertEqual(field.stock["Mushroom"], int(expected))
                self.assertFalse(any(g == "Mushroom" for _, g in field.digs))
                self.assertLessEqual(len(field.pushes), budget)

    def api(self, **overrides):
        bindings = dict(
            Items=Symbols(),
            Grounds=Symbols(),
            Unlocks=Symbols(),
            Hats=Symbols(),
            Entities=Symbols(),
            num_unlocked=lambda _: 1,
            max_drones=lambda: 1,
            num_items=lambda _: 10000,
            get_world_size=lambda: 8,
            get_pos_x=lambda: 0,
            get_pos_y=lambda: 0,
            get_pos_z=lambda: 0,
            change_hat=Mock(),
            clear=Mock(),
            jump=Mock(),
            quick_print=Mock(),
            set_world_size=Mock(),
        )
        bindings.update(overrides)
        return patch.multiple(achievements, **bindings, create=True)

    def test_clear_does_not_renew_jump_allowance(self):
        jump = Mock()
        with (
            self.api(jump=jump),
            patch.object(achievements, "_jump_used", False),
            patch.object(achievements.utils_farm, "can_start_phase", return_value=True),
        ):
            self.assertTrue(achievements._prepare("Rice"))
            self.assertTrue(achievements._prepare("Mushrooms"))
        jump.assert_called_once_with("Rice")

    def test_workers_or_locked_skill_prevent_clear(self):
        for unlocked, idle in [(0, True), (1, False)]:
            clear = Mock()
            with (
                self.subTest(unlocked=unlocked, idle=idle),
                self.api(num_unlocked=lambda _: unlocked, clear=clear),
                patch.object(
                    achievements.utils_farm, "can_start_phase", return_value=idle
                ),
            ):
                self.assertFalse(achievements._prepare("Rice"))
                clear.assert_not_called()

    def test_treasure_route_removes_closed_loops_in_three_dimensions(self):
        with self.api(get_world_size=lambda: 4):
            self.assertEqual(achievements._treasure_route("DENSWNE"), list("DNE"))
            self.assertEqual(achievements._treasure_route("DENDWS"), list("DENDWS"))
            self.assertEqual(achievements._treasure_route("DEEEEEN"), list("DEN"))
            self.assertIsNone(achievements._treasure_route("DX"))

    def test_treasure_map_first_down_is_not_dug_twice(self):
        actions = []
        with (
            self.api(
                North="N",
                East="E",
                South="S",
                West="W",
                measure=Mock(return_value="DEN"),
                get_ground_type=lambda: "Treasure_Map",
                move=lambda direction: actions.append(direction) or True,
                get_entity_type=lambda: "Underground_Treasure",
                harvest=lambda: actions.append("harvest") or True,
            ),
            patch.object(achievements.utils_farm, "can_start_phase", return_value=True),
            patch.object(achievements.utils_mine, "go_to", return_value=True),
            patch.object(
                achievements,
                "_dig_once",
                side_effect=lambda: actions.append("D") or True,
            ),
        ):
            self.assertTrue(achievements.collect_current_treasure())
        self.assertEqual(actions, ["D", "E", "N", "harvest"])

    def test_pyramids_require_complete_supported_shape_and_harvest(self):
        for colored in (False, True):
            with self.subTest(colored=colored):
                field = PyramidField()
                with field.api():
                    self.assertTrue(
                        achievements._restore_pyramid((0, 0, 5, 0), colored)
                    )
                self.assertTrue(field.harvested)
                self.assertEqual(field.layers, sorted(field.layers))

    def test_pyramid_base_ignores_deeper_terrain_outside_foundation(self):
        cursor = [0, 0]

        def go_to(x, y):
            cursor[:] = [x, y]
            return True

        def on_base():
            return cursor[0] < 5 and cursor[1] < 5

        with (
            self.api(
                get_world_size=lambda: 6,
                get_pos_z=lambda: 0 if on_base() else -1,
                get_ground_type=lambda: "Limestone" if on_base() else "Dirt",
            ),
            patch.object(achievements.utils_mine, "go_to", go_to),
        ):
            self.assertEqual(achievements._pyramid_base(), (0, 0, 5, 0))

    def test_prospect_none_still_counts_when_paid(self):
        stock = [3]

        def probe():
            stock[0] -= 1
            return None

        with (
            self.api(num_items=lambda _: stock[0], prospect_iron=probe),
            patch.object(achievements, "_fund", return_value=True) as fund,
            patch.object(achievements, "_prepare", return_value=True),
        ):
            self.assertTrue(achievements.prospector(3))
        fund.assert_called_once_with("Coal", 3)
        self.assertEqual(stock[0], 0)

    def test_unpaid_prospect_does_not_report_success(self):
        with (
            self.api(prospect_iron=lambda: None),
            patch.object(achievements, "_fund", return_value=True),
            patch.object(achievements, "_prepare", return_value=True),
        ):
            self.assertFalse(achievements.prospector(1))

    def test_dynamite_attempts_require_solved_puzzle_not_partial_stock(self):
        puzzle = importlib.import_module("mine_dynamite")
        with (
            self.api(num_items=lambda _: 50000000),
            patch.object(achievements, "_prepare", return_value=True),
            patch.object(achievements, "_dig_to", return_value=True) as descend,
            patch.object(puzzle, "_puzzle_single", side_effect=[False, True]) as solve,
        ):
            self.assertTrue(achievements.dynamite_specialist(2))
        self.assertEqual(solve.call_count, 2)
        self.assertTrue(all(call.args[0] > 50000000 for call in solve.call_args_list))
        self.assertEqual(descend.call_args.args[0], -600)

    def test_failed_dynamite_attempts_are_bounded(self):
        puzzle = importlib.import_module("mine_dynamite")
        with (
            self.api(),
            patch.object(achievements, "_prepare", return_value=True),
            patch.object(achievements, "_dig_to", return_value=True),
            patch.object(puzzle, "_puzzle_single", return_value=False) as solve,
        ):
            self.assertFalse(achievements.dynamite_specialist(attempts=2))
        self.assertEqual(solve.call_count, 2)

    def test_rice_terrace_keeps_all_plants(self):
        planted = []
        with (
            self.api(plant=lambda entity: planted.append(entity) or True),
            patch.object(achievements, "_prepare", return_value=True),
            patch.object(achievements, "_seek", return_value=True),
            patch.object(achievements.utils_mine, "go_to", return_value=True) as go,
        ):
            self.assertTrue(achievements.rice_terrace())
        self.assertEqual(len(planted), 9)
        self.assertEqual(
            {call.args for call in go.call_args_list},
            {(x, y) for x in range(3) for y in range(3)},
        )

    def test_funding_failure_prevents_construction(self):
        with (
            self.api(),
            patch.object(achievements, "_fund", return_value=False),
            patch.object(achievements, "_prepare") as prepare,
        ):
            self.assertFalse(achievements.builder())
            self.assertFalse(achievements.skyscraper())
        prepare.assert_not_called()

    def test_unknown_task_has_no_game_actions(self):
        with self.api(), patch.object(achievements, "_prepare") as prepare:
            self.assertFalse(achievements.run("unknown"))
        prepare.assert_not_called()

    def test_matchmaker_pushes_over_95_percent_without_mining_the_rest(self):
        # One four-layer stratum, deterministic colors; native cave-ins are omitted.
        columns = {(x, y): [0, 1, 0, 1] for x in range(8) for y in range(8)}
        depths = {pos: 0 for pos in columns}
        cursor, stock, dug = [0, 0], [0], [0]
        rng = random.Random(4)

        def pos():
            return tuple(cursor)

        def go_to(x, y):
            cursor[:] = [x, y]
            return True

        def dig():
            columns[pos()].pop(0)
            depths[pos()] += 1
            dug[0] += 1

        def push(direction):
            x, y = pos()
            dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[direction]
            target = ((x + dx) % 8, (y + dy) % 8)
            if depths[target] <= depths[pos()]:
                return False
            kind = columns[pos()].pop(0)
            depths[pos()] += 1
            if columns[target] and columns[target][0] == kind:
                columns[target].pop(0)
                depths[target] += 1
                stock[0] += 1
            else:
                columns[target].insert(0, kind)
                depths[target] -= 1
            return True

        def move(direction):
            dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[direction]
            cursor[:] = [(cursor[0] + dx) % 8, (cursor[1] + dy) % 8]
            return True

        with (
            self.api(
                North="N",
                East="E",
                South="S",
                West="W",
                get_pos_z=lambda: -depths[pos()],
                get_ground_type=lambda: "Mushroom" if columns[pos()] else "Rock",
                measure=lambda: columns[pos()][0],
                dig=dig,
                push=push,
                move=move,
                random=rng.random,
                num_items=lambda _: stock[0],
            ),
            patch.object(achievements, "_prepare", return_value=True),
            patch.object(achievements, "_seek", return_value=True),
            patch.object(achievements.utils_mine, "go_to", go_to),
        ):
            self.assertTrue(achievements.matchmaker(20000, 8))
        self.assertEqual(dug[0], 4)
        self.assertGreater(2 * stock[0] / 256, 0.95)


class InfiniteTests(unittest.TestCase):
    @contextmanager
    def api(self, unlocked=lambda _: 1, stock=lambda _: 0):
        with ExitStack() as stack:
            stack.enter_context(
                patch.multiple(
                    infinite,
                    Items=Symbols(),
                    Unlocks=Symbols(),
                    num_unlocked=unlocked,
                    num_items=stock,
                    create=True,
                )
            )
            stack.enter_context(
                patch.object(infinite.utils_farm, "can_start_phase", return_value=True)
            )
            yield

    def test_defaults_add_all_eight_dlc_resources_only_when_unlocked(self):
        with self.api():
            items = infinite.default_items()
        self.assertEqual(
            set(items[-8:]),
            set("Block Coal Rice Bamboo Iron Quartz Mushroom Dynamite".split()),
        )
        self.assertEqual(len(items), len(set(items)))
        with self.api(unlocked=lambda _: 0):
            self.assertEqual(len(infinite.default_items()), 7)

    def test_loop_funds_dlc_and_recharges_power_then_stops_on_failure(self):
        calls = []

        def farm(item, goal, *args):
            calls.append((item, goal))
            return len(calls) < 5

        with (
            self.api(),
            patch.object(infinite.resource_manager, "farm", side_effect=farm),
        ):
            self.assertFalse(infinite.run(["Coal", "Dynamite"], "individual"))
        self.assertEqual(
            calls,
            [
                ("Coal", 1),
                ("Dynamite", 1),
                ("Power", 10000),
                ("Coal", 2),
                ("Dynamite", 2),
            ],
        )

    def test_empty_selection_does_not_spin_forever(self):
        with self.api(), patch.object(infinite.resource_manager, "farm") as farm:
            self.assertFalse(infinite.run([]))
        farm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
