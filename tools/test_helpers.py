"""Helper state/action contracts with fake native APIs, not game physics."""

import importlib
import sys
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import Mock, call, patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE))
farm = importlib.import_module("utils_farm")
movement = importlib.import_module("utils_move")
mining = importlib.import_module("utils_mine")
debug = importlib.import_module("utils_debug")


class Symbols:
    def __getattr__(self, name):
        return name


class Board:
    def __init__(self, size=3):
        self.size = size
        self.pos = (1 % size, 1 % size)
        self.grounds = {}
        self.events = []
        self.blocked = None
        self.drones = 1

    def ground(self):
        return self.grounds.get(self.pos, "Grassland")

    def till(self):
        self.events.append(("till", self.pos))
        self.grounds[self.pos] = "Grassland" if self.ground() == "Soil" else "Soil"
        # Native till returns None, not a success flag.

    def move(self, direction):
        self.events.append(("move", direction))
        if direction == self.blocked:
            return False
        dx, dy = {"East": (1, 0), "West": (-1, 0), "North": (0, 1), "South": (0, -1)}[
            direction
        ]
        x, y = self.pos
        self.pos = ((x + dx) % self.size, (y + dy) % self.size)
        return True

    def clear(self):
        self.events.append(("clear", None))
        self.grounds.clear()
        self.pos = (0, 0)

    @contextmanager
    def api(self):
        bindings = dict(
            Grounds=Symbols(),
            Unlocks=Symbols(),
            East="East",
            West="West",
            North="North",
            South="South",
            get_ground_type=self.ground,
            till=self.till,
            move=self.move,
            get_world_size=lambda: self.size,
            get_pos_x=lambda: self.pos[0],
            get_pos_y=lambda: self.pos[1],
            num_unlocked=lambda _: 1,
            num_drones=lambda: self.drones,
            clear=self.clear,
            quick_print=Mock(),
        )
        with ExitStack() as stack:
            for module in (farm, movement, mining):
                stack.enter_context(patch.multiple(module, **bindings, create=True))
            yield


class GroundTests(unittest.TestCase):
    def test_preparation_is_idempotent_and_uses_the_observed_ground(self):
        for function, start, expected in (
            (farm.q_till, "Grassland", "Soil"),
            (farm.q_till_grass, "Soil", "Grassland"),
        ):
            board = Board()
            board.grounds[board.pos] = start
            with self.subTest(function=function.__name__), board.api():
                self.assertIs(function(), True)
                self.assertEqual(board.ground(), expected)
                self.assertIs(function(), True)
            self.assertEqual([e[0] for e in board.events], ["till"])

    def test_preparation_refuses_special_ground_without_tilling_it(self):
        for function in (farm.q_till, farm.q_till_grass):
            for ground in ("Clay", "Rice_Terrace", "Loam", "Rock"):
                board = Board()
                board.grounds[board.pos] = ground
                with (
                    self.subTest(function=function.__name__, ground=ground),
                    board.api(),
                ):
                    self.assertIs(function(), False)
                self.assertEqual(board.ground(), ground)
                self.assertFalse(board.events)

    def test_a_refused_or_ineffective_till_does_not_report_success(self):
        for function, ground in (
            (farm.q_till, "Grassland"),
            (farm.q_till_grass, "Soil"),
        ):
            board = Board()
            board.grounds[board.pos] = ground
            with (
                self.subTest(function=function.__name__),
                board.api(),
                patch.object(farm, "till", return_value=None) as action,
            ):
                self.assertIs(function(), False)
            action.assert_called_once()

    def test_till_all_covers_the_field_and_returns_to_its_start(self):
        for size in (1, 3, 8):
            board = Board(size)
            origin = board.pos
            with self.subTest(size=size), board.api():
                self.assertIs(farm.till_all(size), True)
                self.assertEqual(len(board.grounds), size * size)
                self.assertTrue(all(g == "Soil" for g in board.grounds.values()))
                self.assertEqual(board.pos, origin)
                self.assertIs(farm.till_all(size), True)
            self.assertEqual(
                sum(kind == "till" for kind, _ in board.events), size * size
            )

    def test_till_all_stops_at_a_blocked_move_or_unpreparable_tile(self):
        board = Board()
        board.blocked = "East"
        with board.api():
            self.assertIs(farm.till_all(3), False)
        self.assertEqual(board.events, [("move", "East")])
        board = Board()
        board.grounds[(2, 1)] = "Clay"
        with board.api():
            self.assertIs(farm.till_all(3), False)
        self.assertEqual(board.events, [("move", "East")])

    def test_invalid_size_and_unowned_workers_prevent_field_preparation(self):
        for size, drones in ((0, 1), (2, 1), (3, 2)):
            board = Board()
            board.drones = drones
            with self.subTest(size=size, drones=drones), board.api():
                self.assertIs(farm.till_all(size), False)
                self.assertIs(movement.init(size, True), False)
            self.assertFalse(board.events)


class MovementTests(unittest.TestCase):
    def test_surface_and_mining_entries_follow_the_same_wrapping_path(self):
        for module in (movement, mining):
            board = Board(4)
            board.pos = (0, 0)
            with self.subTest(module=module.__name__), board.api():
                args = (3, 2, 4) if module == movement else (3, 2)
                self.assertIs(module.go_to(*args), True)
            self.assertEqual(board.pos, (3, 2))
            self.assertEqual(
                board.events, [("move", "West"), ("move", "North"), ("move", "North")]
            )

    def test_a_blocked_axis_stops_before_later_steps_or_world_changes(self):
        for module in (movement, mining):
            for blocked in ("East", "North"):
                board = Board(8)
                board.pos = (0, 0)
                board.blocked = blocked
                with self.subTest(module=module.__name__, blocked=blocked), board.api():
                    args = (2, 3, 8) if module == movement else (2, 3)
                    self.assertIs(module.go_to(*args), False)
                expected = [("move", "East")]
                if blocked == "North":
                    expected = [("move", "East"), ("move", "East"), ("move", "North")]
                self.assertEqual(board.events, expected)

    def test_y_first_and_direct_routes_keep_their_existing_semantics(self):
        for function, expected in (
            (movement.go_to_yx, ["North", "North", "West"]),
            (movement.go_to_warpless, ["East", "East", "East", "North", "North"]),
            (movement.go_to_warpless_yx, ["North", "North", "East", "East", "East"]),
        ):
            board = Board(4)
            board.pos = (0, 0)
            with self.subTest(function=function.__name__), board.api():
                args = (3, 2, 4) if function == movement.go_to_yx else (3, 2)
                self.assertIs(function(*args), True)
            self.assertEqual(board.events, [("move", d) for d in expected])

    def test_init_can_clear_or_only_navigate_when_it_is_explicitly_requested(self):
        for do_clear in (False, True):
            board = Board()
            with self.subTest(do_clear=do_clear), board.api():
                self.assertIs(movement.init(3, do_clear), True)
            self.assertEqual(board.pos, (0, 0))
            self.assertEqual(sum(e[0] == "clear" for e in board.events), int(do_clear))


class DiagnosticTests(unittest.TestCase):
    def test_reset_does_not_clear_after_blocked_navigation_or_active_workers(self):
        for can_start in (False, True):
            with (
                patch.object(farm, "can_start_phase", return_value=can_start),
                patch.object(movement, "go_to", return_value=False) as travel,
                patch.multiple(
                    debug,
                    Hats=Symbols(),
                    harvest=Mock(return_value=False),
                    change_hat=Mock(),
                    get_world_size=lambda: 3,
                    clear=Mock(),
                    create=True,
                ),
            ):
                self.assertIs(debug.reset(), False)
                debug.clear.assert_not_called()
                if not can_start:
                    debug.harvest.assert_not_called()
                    debug.change_hat.assert_not_called()
                    travel.assert_not_called()

    def test_reset_can_clear_an_empty_tile_without_resetting_progression(self):
        with (
            patch.object(farm, "can_start_phase", return_value=True),
            patch.object(movement, "go_to", return_value=True),
            patch.multiple(
                debug,
                Hats=Symbols(),
                harvest=Mock(return_value=False),
                change_hat=Mock(),
                get_world_size=lambda: 3,
                clear=Mock(),
                create=True,
            ),
        ):
            self.assertIs(debug.reset(), True)
            debug.clear.assert_called_once()

    def test_print_helpers_also_return_the_snapshot_and_sim_returns_duration(self):
        with patch.multiple(
            debug,
            Items=["Hay", "Coal"],
            Unlocks=["Trees", "Megafarm"],
            num_items=lambda _: 12,
            num_unlocked=lambda _: 2,
            quick_print=Mock(),
            create=True,
        ):
            self.assertEqual(debug.print_storage(), {"Hay": 12, "Coal": 12})
            self.assertEqual(debug.print_unlocks(), {"Trees": 2, "Megafarm": 2})
        with patch.multiple(
            debug,
            Items=Symbols(),
            Unlocks=Symbols(),
            num_unlocked=lambda _: 1,
            simulate=Mock(return_value=0.0),
            quick_print=Mock(),
            create=True,
        ):
            self.assertEqual(debug.sim(), 0.0)
            self.assertEqual(debug.simulate.call_args.args[0], "leaderboard_hay_single")

    def test_all_workers_are_joined_even_after_the_first_failure(self):
        with patch.object(
            farm, "wait_for", Mock(side_effect=[False, True, False]), create=True
        ) as wait:
            self.assertIs(farm.join_workers(["first", "second", "third"]), False)
        self.assertEqual(
            wait.call_args_list, [call("first"), call("second"), call("third")]
        )

    def test_simulation_keeps_explicit_empty_inputs_and_passes_the_selected_setup(self):
        unlocks, items, variables = [], {}, {"target": 12}
        with patch.multiple(
            debug,
            Unlocks=Symbols(),
            num_unlocked=lambda _: 1,
            simulate=Mock(return_value=12.5),
            quick_print=Mock(),
            create=True,
        ):
            self.assertEqual(
                debug.sim("story_mining", unlocks, items, variables, 7, 32), 12.5
            )
            debug.simulate.assert_called_once_with(
                "story_mining", [], {}, {"target": 12}, 7, 32
            )
        self.assertEqual((unlocks, items, variables), ([], {}, {"target": 12}))

    def test_locked_diagnostics_return_before_calling_the_unavailable_api(self):
        manager = importlib.import_module("resource_manager")
        with (
            patch.multiple(
                debug,
                Items=Symbols(),
                Unlocks=Symbols(),
                num_items=lambda _: 0,
                num_unlocked=lambda _: 0,
                simulate=Mock(),
                get_time=Mock(),
                get_tick_count=Mock(),
                quick_print=Mock(),
                create=True,
            ),
            patch.object(manager, "farm") as produce,
        ):
            self.assertIsNone(debug.sim())
            self.assertIs(debug.profile_carrot(10), False)
            debug.simulate.assert_not_called()
            debug.get_time.assert_not_called()
            debug.get_tick_count.assert_not_called()
            produce.assert_not_called()


class EmptyWorkTests(unittest.TestCase):
    def test_zero_seeds_need_no_cost_lookup_and_negative_counts_are_rejected(self):
        with patch.object(farm, "get_cost", Mock(), create=True) as cost:
            self.assertEqual(farm.seed_requirements("Carrot", 0), {})
            self.assertIsNone(farm.seed_requirements("Carrot", -1))
            cost.assert_not_called()

    def test_ripe_plants_and_nonpositive_wait_budgets_need_no_clock_or_watering(self):
        for ripe, seconds, expected in (
            (True, 180, True),
            (True, 0, True),
            (False, 0, False),
            (False, -1, False),
        ):
            with (
                self.subTest(ripe=ripe, seconds=seconds),
                patch.multiple(
                    farm,
                    can_harvest=Mock(return_value=ripe),
                    num_unlocked=Mock(),
                    get_time=Mock(),
                    create=True,
                ),
                patch.object(farm, "water") as water,
            ):
                self.assertIs(farm.wait_ripe(seconds), expected)
                farm.can_harvest.assert_called_once()
                farm.num_unlocked.assert_not_called()
                farm.get_time.assert_not_called()
                water.assert_not_called()

    def test_failed_optional_watering_does_not_fail_a_plant_that_matures(self):
        with (
            patch.multiple(
                farm,
                Unlocks=Symbols(),
                num_unlocked=lambda _: 0,
                can_harvest=Mock(side_effect=[False, False, True]),
                get_time=Mock(),
                create=True,
            ),
            patch.object(farm, "water", return_value=False) as water,
        ):
            self.assertIs(farm.wait_ripe(), True)
            farm.get_time.assert_not_called()
            water.assert_called_once()

    def test_empty_or_negative_column_batches_do_not_move_or_spawn_workers(self):
        for columns, steps, expected in (
            (0, 8, True),
            (3, 0, True),
            (0, 0, True),
            (-1, 8, False),
            (3, -1, False),
            (0, -1, False),
        ):
            worker = Mock()
            with (
                self.subTest(columns=columns, steps=steps),
                patch.object(mining, "go_to") as travel,
                patch.object(mining, "spawn_drone", Mock(), create=True) as spawn,
            ):
                self.assertIs(
                    mining.run_columns(worker, 10, columns, steps, True), expected
                )
                travel.assert_not_called()
                spawn.assert_not_called()
                worker.assert_not_called()

    def test_completed_or_invalid_column_plans_do_not_request_a_world_size(self):
        for stock, target, minimum in (
            (10, 10, 1),
            (11, 10, 1),
            (0, 10, 0),
            (0, 10, -1),
        ):
            with (
                self.subTest(stock=stock, target=target, minimum=minimum),
                patch.multiple(
                    mining,
                    num_items=lambda _: stock,
                    get_world_size=Mock(),
                    create=True,
                ),
            ):
                self.assertEqual(mining.column_plan("Rice", target, minimum), (0, 0))
                mining.get_world_size.assert_not_called()

    def test_column_plans_round_fractional_targets_and_cap_the_funded_batch(self):
        for stock, target, minimum, expected in (
            (3, 3.5, 1, (1, 1)),
            (0, 7.3, 2, (3, 2)),
            (0, 1000, 1, (3, 3)),
        ):
            with (
                self.subTest(stock=stock, target=target, minimum=minimum),
                patch.multiple(
                    mining,
                    num_items=lambda _: stock,
                    get_world_size=lambda: 3,
                    create=True,
                ),
            ):
                self.assertEqual(mining.column_plan("Rice", target, minimum), expected)

    def test_invalid_column_plan_fails_before_world_preparation(self):
        with (
            patch.multiple(
                mining,
                num_items=lambda _: 0,
                get_world_size=lambda: 3,
                create=True,
            ),
            patch.object(mining, "prepare") as prepare,
            patch.object(mining, "run_columns") as run,
        ):
            self.assertIs(mining.produce_columns(Mock(), "Rice", 10, True, 0), False)
            prepare.assert_not_called()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
