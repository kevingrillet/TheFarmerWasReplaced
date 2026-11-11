"""Deep-shaft fixtures, not native blast physics, cave-ins or timing."""

import unittest
from unittest.mock import patch

from test_explosive_mining import BlastField, explosive, mining
from test_layer_mining import TreasureField
from test_mining_multi import MiningField

achievements = explosive.ZZAchievementDLC


class DeepShaftTests(unittest.TestCase):
    def test_local_blasts_pass_10000_without_clearing_the_floor(self):
        field = BlastField(ws=3)
        field.stock["Dynamite"] = 10000
        field.layers = {pos: ["Rock"] * 10020 for pos in field.layers}
        with (
            field.api(),
            patch.object(
                explosive.resource_manager,
                "farm_current",
                side_effect=AssertionError("funded during descent"),
            ),
            patch.object(
                mining,
                "survey_surface",
                side_effect=AssertionError("swept ordinary field"),
            ),
        ):
            self.assertTrue(explosive.run(10002, []))
        self.assertLessEqual(field.z(), -10002)
        self.assertEqual(field.worlds, 0)
        self.assertGreater(len(field.blasts), 128)
        self.assertEqual(set(field.blasts), {(0, 0)})
        self.assertEqual(field.depths.get((2, 2), 0), 0)
        self.assertEqual(field.hat, "Straw_Hat")
        self.assertFalse(field.spawned)

    def test_default_is_unlimited_and_resumes_existing_world(self):
        field = BlastField(ws=3)
        field.stock["Dynamite"] = 10
        field.depths[0, 0] = 4
        field.worlds = 7
        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current") as fund,
        ):
            self.assertIsNone(explosive.TARGET_DEPTH)
            self.assertFalse(explosive.START_NEW_WORLD)
            self.assertTrue(explosive.run(activities=[]))
        fund.assert_not_called()
        self.assertEqual(field.worlds, 7)
        self.assertEqual(len(field.blasts), 4)

    def test_activity_table_selects_only_requested_unlocked_kinds(self):
        field = BlastField(ws=3)
        with field.api():
            self.assertEqual(
                set(
                    explosive._protected(
                        ["treasure", "pyramid", "minesweeper", "mushroom"]
                    )
                ),
                {"Basalt", "Treasure_Map", "Sand", "Limestone", "Dynamite", "Mushroom"},
            )
            self.assertEqual(explosive._protected([]), [])
            self.assertEqual(explosive._protected(["mushroom"]), ["Mushroom"])
            self.assertNotIn("Rice", explosive.requirements([]))
            self.assertNotIn("Block", explosive.requirements([]))
        with field.api(num_unlocked=lambda _: 0):
            self.assertEqual(explosive._protected(explosive.ACTIVITIES), [])

    def test_disabled_mushroom_and_rice_do_not_start_collectors(self):
        field = BlastField(ws=3)
        field.stock["Dynamite"] = 1
        field.layers[0, 0][:2] = ["Mushroom", "Clay"]
        with field.api(), patch.object(explosive, "_activity") as activity:
            self.assertTrue(explosive.produce_world(12, 1, []))
        activity.assert_not_called()

    def test_exhausted_fuel_continues_normally_without_reset(self):
        field = BlastField(ws=3)
        field.stock["Dynamite"] = 1
        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current") as fund,
        ):
            self.assertTrue(explosive.run(12, []))
        self.assertEqual(len(field.blasts), 1)
        self.assertEqual(field.z(), -12)
        self.assertEqual(field.worlds, 0)
        self.assertEqual(field.hat, "Straw_Hat")
        fund.assert_not_called()

    def test_visible_neighbor_and_shallower_collector_return_to_deeper_shaft(self):
        field = BlastField(ws=6)
        field.stock["Dynamite"] = 1
        field.depths[0, 0] = 8
        field.layers[1, 0][0] = "Mushroom"

        def collect(hit, parallel, ignored):
            self.assertEqual(hit, (1, 0, 0, "Mushroom"))
            field.layers[1, 0][0] = "Rock"
            return True

        with field.api(), patch.object(explosive, "_activity", side_effect=collect):
            self.assertTrue(explosive.produce_world(12, 1))
        self.assertEqual(field.blasts, [(0, 0)])
        self.assertEqual(field.z(), -10)

    def test_mushroom_deep_option_and_stale_map_markers(self):
        field = BlastField(ws=6)
        ignored = set()
        with (
            field.api(),
            patch.object(
                explosive.farm_mushroom, "collect_current_layer", return_value=True
            ) as mushroom,
            patch.object(
                achievements, "collect_current_treasure", return_value=None
            ) as treasure,
        ):
            self.assertTrue(
                explosive._activity((0, 0, -6000, "Mushroom"), True, ignored)
            )
            self.assertTrue(explosive._activity((0, 0, -7000, "Basalt"), True, ignored))
            self.assertTrue(explosive._ignored((3, 4, -6000, "Mushroom"), ignored))
            self.assertFalse(explosive._ignored((3, 4, -6001, "Mushroom"), ignored))
            self.assertTrue(explosive._ignored((5, 5, -7000, "Basalt"), ignored))
        mushroom.assert_called_once_with(10**30, True, True)
        treasure.assert_called_once_with()


class DeepCollectorTests(unittest.TestCase):
    def test_minesweeper_can_reach_a_board_below_256(self):
        field = MiningField(ws=3)
        field.layers[0, 0] = ["Rock"] * 300 + ["Dynamite", "Soot", "Bedrock"]
        clues = {}
        with field.api(explosive.mine_dynamite, measure=lambda: 0):
            self.assertIsNone(explosive.mine_dynamite._reveal_single(0, -300, 3, clues))
        self.assertEqual(clues, {0: 0})
        self.assertEqual(field.z(), -301)

    def test_pyramid_probe_can_reach_foundation_below_2048(self):
        field = MiningField(ws=3)
        field.layers[0, 0] = ["Rock"] * 2100 + ["Limestone"]
        with field.api(achievements):
            self.assertEqual(
                achievements._pyramid_probe(0, 0, -2100, True), (True, True)
            )
        self.assertEqual(field.z(), -2100)
        self.assertFalse(any(g == "Limestone" for _, g in field.digs))

    def test_mushroom_deep_preparation_is_opt_in_and_bounded(self):
        for deep in (False, True):
            field = MiningField(ws=3, resource="Mushroom")
            field.layers[0, 0] = ["Rock"] * 1100 + ["Mushroom", "Rock"]
            with field.api(explosive.farm_mushroom):
                result = explosive.farm_mushroom._prepare_sector(
                    10**30, (0, 0, 1, 1), -1100, None, deep
                )
            self.assertEqual(result, deep)
            self.assertEqual(field.z(), -1101 if deep else -1024)

    def test_map_access_reaches_only_the_exact_deep_layer(self):
        field = TreasureField(ws=3)
        field.layers = {
            pos: ["Rock"] * 2100 + ["Basalt", "Rock", "Rock", "Rock", "Bedrock"]
            for pos in field.layers
        }
        field.layers[1, 1][2101] = "Treasure_Map"
        field.depths[0, 0] = 2100
        with field.api(achievements, measure=field.measure, harvest=field.harvest):
            self.assertTrue(achievements.collect_current_treasure())
        self.assertEqual(field.maps, [2101])
        self.assertEqual(field.worlds, 0)
