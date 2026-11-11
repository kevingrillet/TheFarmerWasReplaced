"""Launcher routing and native simulation parameters; no live game actions."""

import ast
import importlib
import sys
import unittest
from enum import Enum
from pathlib import Path
from unittest.mock import Mock, patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE))

SCENARIOS = [
    ("carrot", False, "candidate", "leaderboard_carrot_polyculture", "Carrots"),
    (
        "carrot",
        True,
        "candidate",
        "leaderboard_carrot_single_polyculture",
        "Carrots_Single",
    ),
    ("wood", False, "candidate", "leaderboard_wood_polyculture", "Wood"),
    ("wood", True, "candidate", "leaderboard_wood_single_polyculture", "Wood_Single"),
    (
        "pumpkin",
        True,
        "candidate",
        "leaderboard_pumpkin_single_pipeline",
        "Pumpkins_Single",
    ),
    ("power", False, "candidate", "leaderboard_power_global", "Sunflowers"),
    ("hay", False, "default", "leaderboard_hay", "Hay"),
    ("hay", True, "default", "leaderboard_hay_single", "Hay_Single"),
    ("wood", False, "default", "leaderboard_wood", "Wood"),
    ("wood", True, "default", "leaderboard_wood_single", "Wood_Single"),
    ("carrot", False, "default", "leaderboard_carrot", "Carrots"),
    ("carrot", True, "default", "leaderboard_carrot_single", "Carrots_Single"),
    ("pumpkin", False, "default", "leaderboard_pumpkin", "Pumpkins"),
    ("pumpkin", True, "default", "leaderboard_pumpkin_single", "Pumpkins_Single"),
    ("cactus", False, "default", "leaderboard_cactus", "Cactus"),
    ("cactus", True, "default", "leaderboard_cactus_single", "Cactus_Single"),
    ("power", False, "default", "leaderboard_power", "Sunflowers"),
    ("power", True, "default", "leaderboard_power_single", "Sunflowers_Single"),
    ("gold", False, "default", "leaderboard_gold", "Maze"),
    ("gold", True, "default", "leaderboard_gold_single", "Maze_Single"),
    ("bone", False, "default", "leaderboard_bone", "Dinosaur"),
    ("power", False, "cheese", "leaderboard_power_columns", "Sunflowers"),
    ("gold", False, "cheese", "leaderboard_gold_reuse", "Maze"),
    ("bone", False, "cheese", "leaderboard_bone_hybrid", "Dinosaur"),
    ("fastest_reset", False, "default", "leaderboard_fastest_reset", "Fastest_Reset"),
    (
        "fastest_underground_reset",
        False,
        "default",
        "leaderboard_fastest_underground_reset",
        "Fastest_Underground_Reset",
    ),
]

CATEGORIES = Enum(
    "Leaderboards", list(dict.fromkeys(row[4] for row in SCENARIOS)) + ["Rice"]
)
with patch("builtins.Leaderboards", CATEGORIES, create=True):
    launcher = importlib.import_module("leaderboards")

# Starting stocks from the installed LeaderboardSO extracts, not all-item funding.
STOCKS = {
    "hay": {"Power": 1000000000},
    "wood": {"Power": 1000000000},
    "carrot": {"Power": 1000000000, "Hay": 1000000000, "Wood": 1000000000},
    "pumpkin": {"Power": 1000000000, "Carrot": 1000000000},
    "cactus": {"Power": 1000000000, "Pumpkin": 1000000000},
    "power": {"Carrot": 1000000000},
    "gold": {"Power": 1000000000, "Weird_Substance": 1000000000},
    "bone": {"Power": 1000000000, "Cactus": 1000000000},
    "fastest_reset": {},
    "fastest_underground_reset": {},
}


class Symbols:
    def __getattr__(self, name):
        return name


def api(**overrides):
    bindings = dict(
        Items=Symbols(),
        Unlocks=Symbols(),
        Leaderboards=CATEGORIES,
        num_unlocked=Mock(return_value=1),
        quick_print=Mock(),
        simulate=Mock(return_value=12.5),
        leaderboard_run=Mock(),
    )
    bindings.update(overrides)
    return patch.multiple(launcher, **bindings, create=True)


class LauncherTests(unittest.TestCase):
    def test_official_runs_start_the_selected_standalone_file_directly(self):
        for resource, single, strategy, filename, category in SCENARIOS:
            with self.subTest(filename=filename):
                board, simulation = Mock(), Mock()
                with api(leaderboard_run=board, simulate=simulation):
                    self.assertTrue(
                        launcher.run(
                            CATEGORIES[category],
                            mode="leaderboard",
                            strategy=strategy,
                            speedup=256,
                        )
                    )
                board.assert_called_once_with(CATEGORIES[category], filename, 256)
                simulation.assert_not_called()

    def test_each_simulation_uses_its_funding_and_never_supplies_the_goal(self):
        for resource, single, strategy, filename, category in SCENARIOS:
            with self.subTest(filename=filename):
                simulation, board = Mock(return_value=3.125), Mock()
                with api(simulate=simulation, leaderboard_run=board):
                    self.assertEqual(
                        launcher.run(
                            CATEGORIES[category], "simulation", strategy, 7, 64
                        ),
                        3.125,
                    )
                args = simulation.call_args.args
                self.assertEqual(args[0], filename)
                self.assertEqual(args[2], STOCKS[resource])
                self.assertEqual(args[3:], ({}, 7, 64))
                board.assert_not_called()
                if resource.startswith("fastest_"):
                    self.assertEqual(args[1], {})
                else:
                    # Every benchmark except Bone owns its default stock target.
                    collected = resource.capitalize()
                    self.assertEqual(args[2].get(collected, 0), 0)

    def test_single_category_deduces_eight_by_eight_and_one_drone(self):
        for _, single, strategy, filename, category in SCENARIOS:
            if not single:
                continue
            with self.subTest(filename=filename), api():
                launcher.run(CATEGORIES[category], mode="simulation", strategy=strategy)
                unlocks = launcher.simulate.call_args.args[1]
                self.assertEqual(unlocks["Expand"], 5)
                self.assertEqual(unlocks["Megafarm"], 0)
                self.assertEqual(unlocks["Timing"], -1)
                self.assertNotIn("Mining", unlocks)

    def test_catalog_uses_native_categories_and_has_no_duplicate_single_selector(self):
        self.assertTrue(all(isinstance(key, CATEGORIES) for key in launcher.SCRIPTS))
        self.assertFalse(hasattr(launcher, "SINGLE"))
        self.assertFalse(hasattr(launcher, "RESOURCE"))
        for category in ("Dinosaur", "Fastest_Reset", "Fastest_Underground_Reset"):
            self.assertFalse(launcher.SCRIPTS[CATEGORIES[category]][2])

    def test_multi_simulations_keep_maximum_expansion_and_drone_upgrades(self):
        for resource in ("hay", "power", "gold", "bone"):
            with self.subTest(resource=resource), api():
                unlocks, _ = launcher._simulation_setup(resource, False)
                self.assertEqual(unlocks["Expand"], -1)
                self.assertEqual(unlocks["Megafarm"], -1)

    def test_invalid_choices_do_not_start_any_execution(self):
        cases = [
            dict(leaderboard="hay"),
            dict(leaderboard="Hay"),
            dict(leaderboard=CATEGORIES.Rice),
            dict(leaderboard=CATEGORIES.Hay, strategy="missing"),
            dict(leaderboard=CATEGORIES.Hay, strategy="cheese"),
            dict(leaderboard=CATEGORIES.Maze_Single, strategy="cheese"),
            dict(leaderboard=CATEGORIES.Sunflowers_Single, strategy="cheese"),
            dict(leaderboard=CATEGORIES.Hay, mode="missing"),
            dict(leaderboard=CATEGORIES.Hay, mode="manual"),
            dict(leaderboard=CATEGORIES.Hay, speedup=0),
            dict(leaderboard=CATEGORIES.Hay, speedup=-1),
        ]
        for kwargs in cases:
            kwargs.setdefault("mode", "simulation")
            with (
                self.subTest(kwargs=kwargs),
                api(),
            ):
                self.assertFalse(launcher.run(**kwargs))
                launcher.simulate.assert_not_called()
                launcher.leaderboard_run.assert_not_called()

    def test_locks_are_checked_against_the_selected_mode_and_game(self):
        for category, mode, required in (
            (CATEGORIES.Hay, "simulation", "Simulation"),
            (CATEGORIES.Hay, "leaderboard", "Leaderboard"),
            (
                CATEGORIES.Fastest_Underground_Reset,
                "leaderboard",
                "Underground_Leaderboard",
            ),
        ):
            with (
                self.subTest(mode=mode, category=category),
                api(num_unlocked=Mock(return_value=0)),
            ):
                self.assertFalse(launcher.run(category, mode=mode))
                launcher.num_unlocked.assert_called_once_with(required)
                launcher.simulate.assert_not_called()
                launcher.leaderboard_run.assert_not_called()

    def test_no_argument_run_reads_the_header_settings_and_preserves_explicit_zero(
        self,
    ):
        with (
            api(),
            patch.multiple(
                launcher,
                LEADERBOARD=CATEGORIES.Sunflowers,
                MODE="simulation",
                STRATEGY="cheese",
                SEED=19,
                SPEEDUP=64,
            ),
        ):
            self.assertEqual(launcher.run(seed=0), 12.5)
            self.assertEqual(
                launcher.simulate.call_args.args[0], "leaderboard_power_columns"
            )
            self.assertEqual(launcher.simulate.call_args.args[4:], (0, 64))

    def test_zero_duration_is_a_valid_simulation_result_and_negative_seed_is_forwarded(
        self,
    ):
        with api(simulate=Mock(return_value=0)):
            self.assertEqual(
                launcher.run(CATEGORIES.Hay, mode="simulation", seed=-1), 0
            )
            self.assertEqual(launcher.simulate.call_args.args[4], -1)

    def test_launcher_does_not_import_or_execute_benchmarks(self):
        tree = ast.parse((SAVE / "leaderboards.py").read_text(encoding="utf-8"))
        self.assertFalse(
            any(
                isinstance(node, (ast.Import, ast.ImportFrom))
                for node in ast.walk(tree)
            )
        )
        self.assertFalse(
            any(
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                for node in tree.body
            )
        )


if __name__ == "__main__":
    unittest.main()
