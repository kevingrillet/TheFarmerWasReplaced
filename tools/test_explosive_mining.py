"""Blast orchestration fixtures; no native blast physics or timing emulation."""

import importlib
import unittest
from unittest.mock import patch

from test_mining_multi import MiningField

explosive = importlib.import_module("story_mining_infinite_explosive")
campaign = importlib.import_module("story_mining_infinite")
mining = explosive.utils_mine


class BlastField(MiningField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hat = "Straw_Hat"
        self.hats, self.blasts, self.funding, self.observed = [], [], [], []
        self.stuck = False
        self.layers = {
            (x, y): ["Rock"] * 12 + ["Bedrock"]
            for x in range(self.ws)
            for y in range(self.ws)
        }

    def ground(self, direction=None):
        if direction is None:
            self.observed.append(self.pos())
        return super().ground(direction)

    def change_hat(self, hat):
        self.assert_no_workers()
        if self.in_worker:
            raise AssertionError("worker equipped a drill")
        self.hat = hat
        self.hats.append(hat)

    def spawn(self, function, *args):
        if self.hat != "Straw_Hat":
            raise AssertionError("spawn inherited the unique explosive drill")
        return super().spawn(function, *args)

    def fund(self, item, target):
        self.assert_no_workers()
        if self.worlds:
            raise AssertionError("funding destroyed a world already in progress")
        self.funding.append((item, target))
        self.stock[item] = max(target, self.stock.get(item, 0))
        return True

    def dig(self):
        if self.hat != "Explosive_Drill":
            return super().dig()
        self.assert_no_workers()
        if self.in_worker or self.stock.get("Dynamite", 0) < 1:
            raise AssertionError("blast was concurrent or unfunded")
        origin = self.pos()
        self.blasts.append(origin)
        self.events.append(("blast", origin))
        self.stock["Dynamite"] -= 1
        if not self.stuck:
            # Artificial bulk removal tests orchestration, not the game's radius.
            for x in range(max(0, self.x - 1), min(self.ws, self.x + 2)):
                for y in range(max(0, self.y - 1), min(self.ws, self.y + 2)):
                    self.x, self.y = x, y
                    super().dig()
                    super().dig()
        self.x, self.y = origin

    def api(self, **overrides):
        return super().api(
            explosive,
            campaign,
            change_hat=self.change_hat,
            dig=self.dig,
            get_cost=lambda _: {},
            **overrides,
        )


class ExplosiveMiningTests(unittest.TestCase):
    def test_scouts_cover_every_cell_without_digging_and_keep_shallow_candidates(self):
        for capacity in (1, 2, 4, 32):
            field = BlastField(ws=6, capacity=capacity)
            field.layers[1, 1][0] = "Sand"
            field.layers[4, 4][0] = "Mushroom"
            field.depths[0, 0] = 3
            marker = (1, 1, 0, "Sand")
            with self.subTest(capacity=capacity), field.api():
                success, hits, sites, active, kinds = mining.survey_surface(
                    ["Sand", "Mushroom"], True, {marker}
                )
            self.assertTrue(success and active)
            self.assertEqual(hits, [(4, 4, 0, "Mushroom")])
            self.assertIn("Sand", kinds)
            self.assertEqual(max(site[2] for site in sites), 0)
            self.assertEqual(set(field.observed), set(field.layers))
            self.assertFalse(field.digs)
            self.assertEqual(field.spawned, field.joined)

    def test_bulk_collection_has_finite_fuel_and_joined_normal_hat_scouts(self):
        for capacity in (1, 2, 4, 32):
            field = BlastField(ws=6, capacity=capacity)
            with (
                self.subTest(capacity=capacity),
                field.api(),
                patch.object(explosive.resource_manager, "farm_current", field.fund),
                patch.object(explosive, "DYNAMITE_RESERVE", 3),
            ):
                self.assertTrue(explosive.produce_world(12, 3, start_new_world=True))
            self.assertEqual(len(field.blasts), 3)
            self.assertEqual(field.stock["Dynamite"], 0)
            self.assertGreater(field.stock["Block"], 3)
            self.assertEqual(field.worlds, 1)
            self.assertEqual(field.hat, "Straw_Hat")
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_visible_activities_are_delegated_before_any_blast(self):
        for ground in ("Mushroom", "Dynamite", "Sand", "Basalt"):
            field = BlastField(ws=6, capacity=4)
            field.layers[1, 1][0] = ground
            field.x, field.y = 1, 1
            field.stock["Dynamite"] = 1

            def activity(hit, parallel, ignored):
                self.assertEqual(hit, (1, 1, 0, ground))
                self.assertFalse(field.pending or field.blasts)
                self.assertEqual(field.hat, "Straw_Hat")
                field.layers[1, 1][0] = "Rock"
                field.events.append(("activity", ground))
                return True

            with (
                self.subTest(ground=ground),
                field.api(),
                patch.object(explosive.resource_manager, "farm_current", field.fund),
                patch.object(explosive, "_activity", side_effect=activity),
            ):
                self.assertTrue(
                    explosive.produce_world(
                        12, 1, ["treasure", "pyramid", "minesweeper", "mushroom"]
                    )
                )
            self.assertEqual(
                [e[0] for e in field.events if e[0] not in ("spawn", "join")],
                ["activity", "blast"],
            )
            self.assertEqual(field.spawned, field.joined)

    def test_failed_blast_restores_normal_hat_and_reports_failure(self):
        field = BlastField(ws=3)
        field.stuck = True
        field.stock["Dynamite"] = 2
        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current", field.fund),
        ):
            self.assertFalse(explosive.produce_world(12, 2))
        self.assertEqual(len(field.blasts), 1)
        self.assertEqual(field.hat, "Straw_Hat")
        self.assertEqual(field.spawned, field.joined)

    def test_different_visible_mushroom_heights_are_treated_separately(self):
        field = BlastField(ws=6, capacity=4)
        field.layers[0, 0][0] = "Mushroom"
        field.layers[0, 0][2] = "Mushroom"
        field.stock["Dynamite"] = 2
        visited = []

        def collect(target, parallel, deep=False):
            self.assertFalse(field.pending)
            self.assertEqual(field.hat, "Straw_Hat")
            visited.append(field.z())
            return True  # Leftovers at this height must not restart the phase.

        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current", field.fund),
            patch.object(explosive.utils_mine, "prepare", return_value=True),
            patch.object(
                campaign.farm_mushroom, "collect_current_layer", side_effect=collect
            ),
        ):
            self.assertTrue(explosive.produce_world(12, 2, ["mushroom"]))
        self.assertCountEqual(visited, [0, -2])
        self.assertEqual(field.spawned, field.joined)

    def test_no_fuel_does_not_fall_back_to_ordinary_digging(self):
        field = BlastField(ws=3)
        with field.api():
            self.assertFalse(explosive._blast())
        self.assertFalse(field.digs or field.blasts or field.hats)

    def test_funding_and_unlock_failures_happen_before_world_reset(self):
        for failure in ("fund", "unlock"):
            field = BlastField(ws=3)
            with (
                self.subTest(failure=failure),
                field.api(
                    num_unlocked=lambda name: int(
                        failure != "unlock" or name != "Explosive_Drill"
                    )
                ),
                patch.object(
                    explosive.resource_manager, "farm_current", return_value=False
                ),
            ):
                self.assertFalse(explosive.produce_world(12, 2, start_new_world=True))
            self.assertEqual(field.worlds, 0)
            self.assertFalse(field.blasts)

    def test_unchanged_special_surface_stops_without_blasting(self):
        field = BlastField(ws=6, capacity=4)
        field.layers[1, 1][0] = "Dynamite"
        field.x, field.y = 1, 1
        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current", field.fund),
            patch.object(
                explosive,
                "_activity",
                return_value=True,
            ) as activity,
        ):
            self.assertFalse(explosive.produce_world(12, 2))
        self.assertEqual(activity.call_count, 4)
        self.assertFalse(field.blasts)
        self.assertEqual(field.spawned, field.joined)

    def test_failed_activity_returns_to_caller_without_blasting(self):
        field = BlastField(ws=6, capacity=4)
        field.layers[1, 1][0] = "Sand"
        field.x, field.y = 1, 1
        with (
            field.api(),
            patch.object(explosive.resource_manager, "farm_current", field.fund),
            patch.object(
                explosive,
                "_activity",
                return_value=False,
            ),
        ):
            self.assertFalse(explosive.produce_world(12, 2))
        self.assertFalse(field.blasts)
        self.assertEqual(field.spawned, field.joined)


if __name__ == "__main__":
    unittest.main()
