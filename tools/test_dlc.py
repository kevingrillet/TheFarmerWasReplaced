"""Targeted DLC contracts with fake APIs, not a TFWR physics/timing emulator."""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE))
farm_mushroom = importlib.import_module("farm_mushroom")
farm_rice = importlib.import_module("farm_rice")
mine_coal = importlib.import_module("mine_coal")
mine_dynamite = importlib.import_module("mine_dynamite")
resource_manager = importlib.import_module("resource_manager")
story_mining = importlib.import_module("story_mining")
utils_mine = importlib.import_module("utils_mine")


def symbols(names):
    return SimpleNamespace(**{name: name for name in names.split()})


ITEMS = symbols(
    "Block Coal Rice Bamboo Iron Quartz Mushroom Dynamite Hay Wood Carrot Pumpkin Cactus Bone Gold Power Weird_Substance"
)
UNLOCKS = symbols(
    "Mining Underground_Senses Coal Rice Bamboo Iron Quartz Mushrooms Dynamite Ore_Boost Prospecting Megafarm Polyculture Trees Jump Debug_Place Special_Soils Petrified_Pumpkins Pyramid Treasure_Map Explosive_Drill Underground_Leaderboard"
)


class ManagerTests(unittest.TestCase):
    def test_locked_resource_does_not_start_a_producer(self):
        with (
            patch.multiple(
                resource_manager,
                Items=ITEMS,
                Unlocks=UNLOCKS,
                num_items=lambda item: 0,
                num_unlocked=lambda unlock: 0,
                create=True,
            ),
            patch.object(mine_coal, "farm_single") as farm,
        ):
            self.assertFalse(resource_manager.farm("Coal", 10, True, True, True))
            farm.assert_not_called()

    def test_already_satisfied_dlc_target_does_no_work(self):
        with (
            patch.multiple(
                resource_manager, Items=ITEMS, num_items=lambda item: 10, create=True
            ),
            patch.object(farm_rice, "farm_multi") as farm,
        ):
            self.assertTrue(resource_manager.farm("Rice", 10, True, True, True))
            farm.assert_not_called()

    def test_multi_rice_dispatch_propagates_failure(self):
        with (
            patch.multiple(
                resource_manager,
                Items=ITEMS,
                Unlocks=UNLOCKS,
                num_items=lambda item: 0,
                num_unlocked=lambda unlock: 1,
                create=True,
            ),
            patch.object(farm_rice, "requirements", return_value={}),
            patch.object(farm_rice, "produce_multi", return_value=False) as farm,
            patch.object(resource_manager, "quick_print", Mock(), create=True),
        ):
            self.assertFalse(resource_manager.farm("Rice", 100, True, True, True))
            farm.assert_called_once_with(100)

    def skill_api(self, get_cost, unlock, level):
        return patch.multiple(
            resource_manager,
            get_time=lambda: 0,
            num_unlocked=lambda skill: level[0],
            num_items=lambda item: 10**20,
            get_cost=get_cost,
            unlock=unlock,
            quick_print=lambda *args: None,
            create=True,
        )

    def test_upgrade_rereads_cost_after_each_level(self):
        level = [0]
        costs = Mock(side_effect=[{"Coal": 2}, {"Rice": 3}])

        def unlock(skill):
            level[0] += 1
            return True

        with (
            self.skill_api(costs, unlock, level),
            patch.object(resource_manager, "farm", return_value=True) as farm,
            patch.object(resource_manager.utils_debug, "print_storage"),
        ):
            self.assertTrue(
                resource_manager.get_skill(0, False, False, False, 2, "Mining")
            )
        self.assertEqual(costs.call_count, 2)
        self.assertEqual(
            [c.args[:2] for c in farm.call_args_list], [("Coal", 2), ("Rice", 3)]
        )

    def test_unavailable_level_or_funding_failure_stops(self):
        level = [0]
        unlock = Mock(return_value=True)
        for cost, funded in [({}, True), ({"Coal": 2}, False)]:
            with (
                self.subTest(cost=cost),
                self.skill_api(lambda skill: cost, unlock, level),
                patch.object(resource_manager, "farm", return_value=funded),
            ):
                self.assertFalse(
                    resource_manager.get_skill(0, False, False, False, 1, "Mining")
                )
        unlock.assert_not_called()

    def test_refused_upgrade_does_not_loop(self):
        level = [0]
        unlock = Mock(return_value=False)
        with (
            self.skill_api(lambda skill: {"Coal": 1}, unlock, level),
            patch.object(resource_manager, "farm", return_value=True),
        ):
            self.assertFalse(
                resource_manager.get_skill(0, False, False, False, 1, "Mining")
            )
        unlock.assert_called_once()

    def test_consumed_ingredient_is_replenished_before_upgrade(self):
        level, stock = [0], {"Rice": 0, "Bamboo": 0}

        def farm(item, qty, *args):
            if stock[item] < qty:
                if item == "Bamboo":
                    stock["Rice"] -= 8
                stock[item] = qty
            return True

        def unlock(skill):
            self.assertGreaterEqual(stock["Rice"], 800)
            self.assertGreaterEqual(stock["Bamboo"], 1000)
            level[0] += 1
            return True

        with (
            self.skill_api(lambda skill: {"Rice": 800, "Bamboo": 1000}, unlock, level),
            patch.object(
                resource_manager, "num_items", side_effect=lambda item: stock[item]
            ),
            patch.object(resource_manager, "farm", side_effect=farm) as fund,
            patch.object(resource_manager.utils_debug, "print_storage"),
        ):
            self.assertTrue(
                resource_manager.get_skill(0, True, True, True, 1, "Special_Soils")
            )
        self.assertEqual(fund.call_count, 4)

    def test_funding_without_retained_stock_is_bounded(self):
        level, unlock = [0], Mock()
        with (
            self.skill_api(lambda skill: {"Coal": 2}, unlock, level),
            patch.object(resource_manager, "num_items", return_value=0),
            patch.object(resource_manager, "farm", return_value=True) as fund,
        ):
            self.assertFalse(
                resource_manager.get_skill(0, False, False, False, 1, "Mining")
            )
        self.assertEqual(fund.call_count, 8)
        unlock.assert_not_called()


class WorkerTests(unittest.TestCase):
    def test_coal_search_collects_across_finite_worlds(self):
        stock, depth = [0], [0]

        def prepare():
            depth[0] = 0
            return True

        def ground(direction=None):
            if direction is not None:
                return "Dirt"
            return "Dirt" if depth[0] < 3 else "Coal" if depth[0] == 3 else "Bedrock"

        def dig():
            if depth[0] == 3:
                stock[0] += 1
            depth[0] += 1

        with (
            patch.object(utils_mine, "prepare", side_effect=prepare) as reset,
            patch.multiple(
                utils_mine,
                Items=ITEMS,
                Grounds=symbols("Dirt Coal Bedrock"),
                North="N",
                East="E",
                South="S",
                West="W",
                num_items=lambda item: stock[0],
                get_ground_type=ground,
                dig=dig,
                create=True,
            ),
        ):
            self.assertTrue(utils_mine.farm_ore("Coal", "Coal", 2))
        self.assertEqual(stock[0], 2)
        self.assertEqual(reset.call_count, 2)

    def test_bamboo_plucks_two_fruits_then_enters_at_height_zero(self):
        bamboo = importlib.import_module("farm_bamboo")
        heights, hovering, stock, y = iter([2, 5, 8]), [1], [0], [0]

        def fly(height):
            hovering[0] = height
            return True

        def move(direction):
            y[0] += 1 if direction == "N" else -1
            if y[0] == 0 and hovering[0] == 0:
                stock[0] += 81
            return True

        with (
            patch.multiple(
                bamboo,
                Items=ITEMS,
                Grounds=symbols("Soil"),
                Entities=symbols("Bamboo"),
                North="N",
                South="S",
                num_items=lambda item: stock[0],
                get_ground_type=lambda: "Soil",
                plant=lambda entity: True,
                measure=lambda: next(heights),
                hover=Mock(side_effect=fly),
                move=move,
                create=True,
            ),
            patch.object(bamboo, "_wait"),
        ):
            self.assertTrue(bamboo._column(50, 2))
            self.assertEqual(
                [c.args[0] for c in bamboo.hover.call_args_list], [2, 5, 0]
            )
        self.assertEqual(stock[0], 81)

    def test_rice_wait_timeout_returns_to_parent(self):
        rice = importlib.import_module("farm_rice")
        clock = iter([0, 31])
        with (
            patch.object(utils_mine, "seek", return_value=True),
            patch.multiple(
                rice,
                Items=ITEMS,
                Grounds=symbols("Clay"),
                Entities=symbols("Rice"),
                num_items=lambda item: 0,
                plant=lambda entity: True,
                create=True,
            ),
            patch.multiple(
                rice.utils_farm,
                Unlocks=symbols("Timing"),
                num_unlocked=lambda _: 1,
                get_time=lambda: next(clock),
                can_harvest=lambda: False,
                quick_print=Mock(),
                create=True,
            ),
        ):
            self.assertFalse(rice._column(1, 1))

    def test_joins_owned_worker_after_navigation_failure(self):
        waiter = Mock(return_value=True)
        with (
            patch.object(utils_mine, "go_to", side_effect=[True, False]),
            patch.multiple(
                utils_mine,
                spawn_drone=lambda *args: "owned",
                create=True,
            ),
            patch.object(utils_mine.utils_farm, "wait_for", waiter, create=True),
        ):
            self.assertFalse(utils_mine.run_columns(Mock(), 100, 2, 3, True))
        waiter.assert_called_once_with("owned")

    def test_capacity_failure_runs_task_on_parent_and_joins_others(self):
        worker = Mock(return_value=True)
        waiter = Mock(return_value=False)
        with (
            patch.object(utils_mine, "go_to", return_value=True),
            patch.multiple(
                utils_mine,
                spawn_drone=Mock(side_effect=["owned", None]),
                create=True,
            ),
            patch.object(utils_mine.utils_farm, "wait_for", waiter, create=True),
        ):
            self.assertFalse(utils_mine.run_columns(worker, 100, 3, 3, True))
        self.assertEqual(worker.call_count, 2)
        worker.assert_called_with(100, 3)
        waiter.assert_called_once_with("owned")

    def test_bamboo_is_funded_before_world_preparation(self):
        bamboo = importlib.import_module("farm_bamboo")
        with (
            patch.multiple(
                resource_manager,
                Items=ITEMS,
                Unlocks=UNLOCKS,
                num_items=lambda _: 0,
                num_unlocked=lambda _: 1,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(bamboo, "requirements", return_value={"Rice": 8}),
            patch.object(
                resource_manager, "_fund_requirements", return_value=False
            ) as fund,
            patch.object(utils_mine, "prepare") as prepare,
        ):
            self.assertFalse(resource_manager.farm("Bamboo", 100, True, True, True))
        self.assertEqual(fund.call_args.args[0], {"Rice": 8})
        prepare.assert_not_called()

    def test_block_bootstrap_has_no_senses_dependency(self):
        block = importlib.import_module("mine_block")
        stock = [0]

        def dig():
            stock[0] += 1

        with patch.multiple(
            block, Items=ITEMS, num_items=lambda item: stock[0], dig=dig, create=True
        ):
            self.assertTrue(block._column(3, 16))
        self.assertEqual(stock[0], 3)

    def test_stalled_mushroom_search_stops_after_eight_worlds(self):
        with (
            patch.multiple(
                farm_mushroom,
                Items=ITEMS,
                num_items=lambda item: 0,
                quick_print=lambda *args: None,
                create=True,
            ),
            patch.object(utils_mine, "prepare", return_value=True),
            patch.object(farm_mushroom, "requirements", return_value={}),
            patch.object(farm_mushroom.utils_farm, "preflight", return_value=True),
            patch.object(farm_mushroom, "_stratum_single", return_value=True) as search,
        ):
            self.assertFalse(farm_mushroom.farm_single(1))
        self.assertEqual(search.call_count, 8)


class DynamiteTests(unittest.TestCase):
    def test_corner_neighbors_do_not_wrap(self):
        self.assertEqual(set(mine_dynamite._neighbors_single(0, 3)), {1, 3, 4})

    def test_zero_and_full_constraints(self):
        safe, mines, _ = mine_dynamite._deduce_single({0: 0}, set(), 3)
        self.assertEqual(safe, {1, 3, 4})
        self.assertFalse(mines)
        safe, mines, _ = mine_dynamite._deduce_single({0: 3}, set(), 3)
        self.assertEqual(mines, {1, 3, 4})
        self.assertFalse(safe)

    def test_subset_deductions(self):
        safe, _, _ = mine_dynamite._deduce_single({0: 1, 1: 1}, set(), 3)
        self.assertEqual(safe, {2, 5})
        _, mines, _ = mine_dynamite._deduce_single({0: 1, 1: 3}, set(), 3)
        self.assertEqual(mines, {2, 5})

    def test_contradictory_clue_is_rejected(self):
        self.assertIsNone(mine_dynamite._deduce_single({0: 4}, set(), 3))

    def test_complete_small_puzzle_without_revealing_flagged_mine(self):
        revealed = set()
        mines = {8}

        def reveal(pos, depth, ws, clues):
            self.assertNotIn(pos, mines)
            revealed.add(pos)
            if len(revealed) == 8:
                return True
            clues[pos] = len(set(mine_dynamite._neighbors_single(pos, ws)) & mines)
            return None

        with (
            patch.multiple(
                mine_dynamite,
                Items=ITEMS,
                Grounds=symbols("Dynamite"),
                get_pos_z=lambda: -50,
                get_world_size=lambda: 3,
                get_pos_x=lambda: 0,
                get_pos_y=lambda: 0,
                num_items=lambda item: 0,
                create=True,
            ),
            patch.object(utils_mine, "seek", return_value=True),
            patch.object(mine_dynamite, "_reveal_single", side_effect=reveal),
        ):
            self.assertTrue(mine_dynamite._puzzle_single(1000))
        self.assertEqual(revealed, set(range(8)))


class StoryTests(unittest.TestCase):
    # Compact factual fixtures from installed build 26410308 (not game text).
    recipes = {
        "Mining": [
            {"Carrot": 20},
            {"Block": 50},
            {"Rice": 60},
            {"Coal": 30},
            {"Bamboo": 200},
            {"Iron": 70},
            {"Quartz": 90},
            {"Mushroom": 250},
        ],
        "Underground_Senses": [{"Block": 50}],
        "Coal": [
            {"Block": 20},
            {"Rice": 150},
            {"Rice": 1000},
            {"Rice": 4000},
            {"Rice": 16000},
        ],
        "Rice": [{"Coal": 10}]
        + [{"Block": n} for n in [100, 500, 1000, 2000, 4000, 8000, 16000]],
        "Bamboo": [{"Rice": 50}, {"Rice": 400}, {"Rice": 800}]
        + [{"Mushroom": n} for n in [100, 400, 1600, 6400, 25600]],
        "Iron": [
            {"Block": 90},
            {"Coal": 50},
            {"Coal": 150},
            {"Coal": 450},
            {"Bamboo": 10000000},
        ],
        "Quartz": [{"Iron": n} for n in [50, 200, 400, 800]],
        "Mushrooms": [{"Quartz": 60, "Pumpkin": 100}]
        + [{"Gold": n} for n in [600, 3000, 15000, 75000]],
        "Dynamite": [
            {"Mushroom": 80, "Gold": 4000},
            {"Mushroom": 400},
            {"Quartz": 50},
            {"Quartz": 200},
            {"Quartz": 800},
        ],
        "Underground_Leaderboard": [{"Dynamite": 20000, "Bamboo": 200000}],
    }
    resource_unlocks = {
        "Block": "Mining",
        "Coal": "Coal",
        "Rice": "Rice",
        "Bamboo": "Bamboo",
        "Iron": "Iron",
        "Quartz": "Quartz",
        "Mushroom": "Mushrooms",
        "Dynamite": "Dynamite",
    }
    caps = {
        "Mining": 8,
        "Rice": 8,
        "Bamboo": 8,
        "Coal": 5,
        "Iron": 5,
        "Quartz": 4,
        "Mushrooms": 5,
        "Dynamite": 5,
        "Petrified_Pumpkins": 7,
        "Pyramid": 5,
        "Treasure_Map": 5,
        "Megafarm": 5,
    }

    def run_story(self, stop=False, reject=None):
        levels = {"Megafarm": 5, "Polyculture": 5, "Trees": 10}
        visited = []

        def buy(t, multi, poly, trees, target, skill):
            visited.append(skill)
            if skill == reject:
                return False
            self.assertLessEqual(target, self.caps.get(skill, 1))
            for level in range(levels.get(skill, 0), target):
                recipes = self.recipes.get(skill)
                if recipes:
                    for resource in recipes[level]:
                        if resource in self.resource_unlocks:
                            self.assertGreater(
                                levels.get(self.resource_unlocks[resource], 0),
                                0,
                                (skill, level + 1, resource),
                            )
                levels[skill] = level + 1
            return True

        with (
            patch.multiple(
                story_mining,
                Unlocks=UNLOCKS,
                get_time=lambda: 0,
                num_unlocked=lambda skill: levels.get(skill, 0),
                quick_print=lambda *args: None,
                create=True,
            ),
            patch.object(resource_manager, "get_skill", side_effect=buy),
        ):
            result = story_mining.run(stop)
        return result, levels, visited

    def test_all_targets_respect_caps_and_producer_bootstrap_order(self):
        result, levels, _ = self.run_story()
        self.assertTrue(result)
        self.assertEqual(levels["Explosive_Drill"], 1)
        self.assertEqual(levels["Underground_Leaderboard"], 1)
        for skill, cap in self.caps.items():
            self.assertEqual(levels[skill], cap)

    def test_leaderboard_mode_stops_before_optional_upgrade_tail(self):
        result, levels, visited = self.run_story(True)
        self.assertTrue(result)
        self.assertEqual(levels["Underground_Leaderboard"], 1)
        self.assertNotIn("Explosive_Drill", visited)
        self.assertNotIn("Treasure_Map", visited)

    def test_failed_upgrade_stops_story(self):
        result, _, visited = self.run_story(reject="Coal")
        self.assertFalse(result)
        self.assertEqual(visited[-1], "Coal")
        self.assertNotIn("Rice", visited)

    def test_new_game_modules_stay_within_documented_language_subset(self):
        names = [
            "utils_mine",
            "mine_block",
            "mine_block",
            "mine_coal",
            "mine_iron",
            "mine_quartz",
            "farm_rice",
            "farm_rice",
            "farm_bamboo",
            "farm_bamboo",
            "farm_mushroom",
            "mine_dynamite",
            "main",
            "story_farm",
            "story_mining",
            "story_infinite",
            "leaderboard_fastest_underground_reset",
        ]
        forbidden = (
            ast.ClassDef,
            ast.AnnAssign,
            ast.Try,
            ast.Raise,
            ast.With,
            ast.AsyncFunctionDef,
            ast.Lambda,
            ast.ListComp,
            ast.DictComp,
            ast.SetComp,
            ast.GeneratorExp,
            ast.ImportFrom,
        )
        for name in names:
            tree = ast.parse((SAVE / f"{name}.py").read_text(encoding="utf-8"))
            self.assertFalse(
                any(isinstance(n, forbidden) for n in ast.walk(tree)), name
            )


if __name__ == "__main__":
    unittest.main()
