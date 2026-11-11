"""Layer barriers and scenario ownership fixtures, not native physics/timing."""

import importlib
import unittest
from unittest.mock import patch

from test_mining_multi import DynamiteField, MiningField
from test_mushroom import StrataField

mining = importlib.import_module("utils_mine")
achievements = importlib.import_module("ZZAchievementDLC")
campaign = importlib.import_module("story_mining_infinite")
infinite = importlib.import_module("story_infinite")


class RiceField(MiningField):
    def __init__(self, **kwargs):
        super().__init__(resource="Rice", **kwargs)
        self.layers = {
            (x, y): ["Grassland", "Clay", "Clay", "Rock", "Bedrock"]
            for x in range(self.ws)
            for y in range(self.ws)
        }
        self.dry = set()

    def ground(self, direction=None):
        if self.entities.get(self.pos()) == "Rice":
            return "Rice_Terrace"
        if (self.pos(), -self.z()) in self.dry:
            return "Dry_Rice_Terrace"
        return super().ground(direction)

    def plant(self, entity):
        if entity != "Rice" or self.ground() != "Clay":
            return False
        self.entities[self.pos()] = entity
        return True

    def harvest(self):
        if self.entities.pop(self.pos(), None) != "Rice":
            return False
        self.stock["Rice"] += 1
        self.dry.add((self.pos(), -self.z()))
        return True

    def dig(self):
        if self.entities.get(self.pos()) == "Rice":
            raise AssertionError("Live Rice was dug instead of harvested")
        return super().dig()


class TreasureField(MiningField):
    """Basalt retains map coordinates even after that map was consumed."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.maps = []
        self.active_map = None
        self.layers = {
            (x, y): ["Rock", "Basalt"]
            + ["Rock"] * 6
            + ["Basalt"]
            + ["Rock"] * 7
            + ["Bedrock"]
            for x in range(self.ws)
            for y in range(self.ws)
        }
        for depth in (2, 9):
            self.layers[1, 1][depth] = "Treasure_Map"

    def measure(self):
        if self.ground() == "Basalt":
            # Mirrors native lookup of stored ground metadata, not block presence.
            return 1, 1
        if self.ground() == "Treasure_Map":
            return "DD"
        return None

    def dig(self):
        if self.ground() == "Treasure_Map":
            self.active_map = -self.z()
            self.layers[1, 1][self.active_map + 1] = "Treasure_Path"
            self.layers[1, 1][self.active_map + 2] = "Treasure_Goal"
        result = super().dig()
        if self.ground() == "Treasure_Goal" and self.active_map is not None:
            self.entities[self.pos()] = "Underground_Treasure"
        return result

    def harvest(self):
        if self.entities.pop(self.pos(), None) != "Underground_Treasure":
            return False
        self.maps.append(self.active_map)
        self.active_map = None
        return True


class StabilityField(MiningField):
    """Small stability propagation model, including buried fragile blocks.

    This deliberately checks eight neighbors. It does not reproduce all native
    controller effects or concurrent scheduling; no timing claim follows.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collapsed = []

    def dig(self):
        result = super().dig()
        changed = True
        while changed:
            changed = False
            for (x, y), layers in self.layers.items():
                top = self.depths.get((x, y), 0)
                deepest = max(
                    self.depths.get((nx, ny), 0)
                    for nx in range(max(0, x - 1), min(self.ws, x + 2))
                    for ny in range(max(0, y - 1), min(self.ws, y + 2))
                )
                for depth in range(deepest - 1, top - 1, -1):
                    ground = layers[depth] if depth < len(layers) else "Bedrock"
                    stability = {
                        "Rock": 3,
                        "Mushroom": 3,
                        "Sand": 2,
                        "Limestone": 3,
                        "Clay": 3,
                        "Iron": 3,
                        "Quartz": 5,
                    }.get(ground, 1)
                    if ground != "Bedrock" and stability < deepest - depth:
                        self.depths[x, y] = depth + 1
                        self.collapsed.append(((x, y), ground, depth))
                        changed = True
                        break
        return result


class LayerTests(unittest.TestCase):
    def test_legacy_layer_contract_does_not_pay_for_stability_observations(self):
        f = MiningField(ws=3, capacity=1)
        with f.api(get_stability=lambda: self.fail("legacy survey added")):
            self.assertEqual(len(mining.excavate_layer(-1, [])), 4)

    def test_band_survey_takes_the_weakest_worker_and_detects_uneven_terrain(self):
        for capacity in (1, 2, 4, 32):
            f = MiningField(ws=6, capacity=capacity)
            f.layers = {(x, y): ["Rock"] * 4 for x in range(6) for y in range(6)}
            f.layers[0, 0][0] = "Coal"
            with self.subTest(capacity=capacity), f.api():
                self.assertEqual(mining.excavate_band(0, [])[4], 1)
                f.layers[0, 0][0] = "Rock"
                self.assertEqual(mining.excavate_band(0, [])[4], 2)
                f.depths[0, 0] = 1
                self.assertEqual(mining.excavate_band(0, [])[4], 0)
            self.assertEqual(f.spawned, f.joined)

    def test_two_layer_band_preserves_specials_and_buried_fragile_ores(self):
        f = StabilityField(ws=6, capacity=4)
        f.layers = {
            (x, y): ["Rock"] * 5 + ["Bedrock"] for x in range(6) for y in range(6)
        }
        protected = [
            "Clay",
            "Mushroom",
            "Dynamite",
            "Basalt",
            "Treasure_Map",
            "Sand",
            "Limestone",
        ]
        for x, ground in enumerate(protected[:6]):
            f.layers[x, 0][1] = ground
        f.layers[0, 1][1] = "Limestone"
        f.layers[2, 2][1] = "Coal"
        with f.api():
            self.assertEqual(mining.excavate_band(0, protected)[4], 2)
            result, hits, active, kinds, stability = mining.excavate_band(-2, protected)
        self.assertTrue(result)
        self.assertEqual({h[3] for h in hits}, set(protected))
        self.assertFalse(any(g in protected for _, g in f.digs))
        self.assertFalse(f.collapsed)
        self.assertEqual(f.stock["Coal"], 1)
        self.assertEqual(f.spawned, f.joined)

    def test_three_layers_can_destroy_a_hidden_fragile_block(self):
        f = StabilityField(ws=3, capacity=1)
        f.layers = {(x, y): ["Rock"] * 5 for x in range(3) for y in range(3)}
        f.layers[1, 0][1] = "Dynamite"
        with f.api():
            self.assertEqual(mining.excavate_band(0, ["Dynamite"])[4], 2)
            mining.excavate_band(-3, ["Dynamite"])  # Caller bypasses the two-layer cap.
        self.assertIn(((1, 0), "Dynamite", 1), f.collapsed)

    def test_each_height_finishes_before_next_and_checks_every_cell(self):
        for capacity in (1, 2, 4, 32):
            f = MiningField(ws=6, capacity=capacity)
            with self.subTest(capacity=capacity), f.api():
                for depth in range(6):
                    result, hits, active, kinds = mining.excavate_layer(
                        -depth, [], True
                    )
                    self.assertTrue(result)
                    self.assertFalse(hits)
                    self.assertFalse(f.pending)
                    self.assertTrue(
                        all(
                            f.depths.get((x, y), 0) == depth
                            for x in range(6)
                            for y in range(6)
                        )
                    )
            self.assertEqual(f.spawned, f.joined)
            self.assertEqual(len(f.digs), 36 * 5)

    def test_protected_blocks_are_reported_without_being_dug(self):
        f = MiningField(ws=6, capacity=4)
        f.layers = {
            (x, y): ["Grassland", "Dirt", "Sand", "Limestone"]
            for x in range(6)
            for y in range(6)
        }
        with f.api():
            result, hits, active, kinds = mining.excavate_layer(
                -2, ["Sand", "Limestone"]
            )
        self.assertTrue(result)
        self.assertEqual(len(hits), 36)
        self.assertEqual({h[3] for h in hits}, {"Sand"})
        self.assertFalse(any(g in ("Sand", "Limestone") for _, g in f.digs))
        self.assertEqual(f.spawned, f.joined)

    def test_future_deeper_specials_wait_for_the_coordinator_height(self):
        f = MiningField(ws=3, capacity=1)
        f.layers = {
            (x, y): ["Rock", "Rock", "Clay", "Bedrock"]
            for x in range(3)
            for y in range(3)
        }
        f.depths = {(x, y): 2 for x in range(3) for y in range(3)}
        with f.api():
            self.assertEqual(mining.excavate_layer(-1, ["Clay"])[1], [])
            self.assertEqual(len(mining.excavate_layer(-2, ["Clay"])[1]), 9)
        self.assertFalse(f.digs)

    def test_pyramid_search_finds_structure_after_joining_every_worker(self):
        for capacity in (1, 2, 4):
            f = MiningField(ws=6, capacity=capacity)
            f.layers = {
                (x, y): ["Grassland", "Rock", "Sand", "Limestone", "Bedrock"]
                for x in range(6)
                for y in range(6)
            }
            dig = f.dig

            def guarded():
                if f.ground() == "Sand":
                    self.assertFalse(f.pending)
                    self.assertFalse(f.in_worker)
                dig()

            with self.subTest(capacity=capacity), f.api(achievements, dig=guarded):
                self.assertTrue(achievements._find_pyramid(5))
            self.assertEqual(f.ground(), "Limestone")
            self.assertEqual(f.spawned, f.joined)

    def test_failed_excavation_joins_owned_children(self):
        f = MiningField(ws=6, capacity=4)
        with f.api(dig=lambda: None):
            self.assertFalse(mining.excavate_layer(-1, [])[0])
        self.assertTrue(f.spawned)
        self.assertEqual(f.spawned, f.joined)
        self.assertFalse(f.pending)


class CampaignTests(unittest.TestCase):
    def api(self, field, **overrides):
        return field.api(
            campaign,
            achievements,
            campaign.mine_dynamite,
            campaign.farm_mushroom,
            get_cost=lambda _: {},
            **overrides,
        )

    def test_stable_terrain_uses_fewer_passes_and_respects_the_depth_limit(self):
        passes = []
        for stability in (1, 3):
            f = MiningField(ws=6, capacity=4)
            f.layers = {(x, y): ["Rock"] * 12 for x in range(6) for y in range(6)}
            with (
                self.api(f, get_stability=lambda: stability),
                patch.object(campaign, "_fund", return_value=True),
                patch.object(
                    mining, "excavate_band", wraps=mining.excavate_band
                ) as excavate,
            ):
                self.assertTrue(campaign.produce_world(9))
            self.assertEqual(set(f.depths.values()), {9})
            self.assertEqual(f.spawned, f.joined)
            passes.append([call.args[0] for call in excavate.call_args_list])
        self.assertEqual(passes[0], list(range(0, -10, -1)))
        self.assertEqual(passes[1], [0, -2, -4, -6, -8, -9])

    def test_pyramid_search_also_batches_stable_layers(self):
        f = StabilityField(ws=6, capacity=4)
        f.layers = {
            (x, y): ["Rock"] * 5 + ["Sand", "Limestone", "Bedrock"]
            for x in range(6)
            for y in range(6)
        }
        with (
            f.api(achievements),
            patch.object(
                mining, "excavate_band", wraps=mining.excavate_band
            ) as excavate,
        ):
            self.assertTrue(achievements._find_pyramid(6))
        self.assertEqual(
            [call.args[0] for call in excavate.call_args_list], [0, -2, -4, -6]
        )
        self.assertFalse(f.collapsed)
        self.assertEqual(f.spawned, f.joined)

    def test_ordinary_ores_are_collected_in_one_world(self):
        f = MiningField(ws=3, capacity=4, resource="Block")
        f.layers = {
            (x, y): [
                "Grassland",
                "Dirt",
                "Coal",
                "Iron",
                "Quartz",
                "Petrified_Pumpkin",
                "Bedrock",
            ]
            for x in range(3)
            for y in range(3)
        }
        original = f.dig

        def dig():
            fossil = f.ground() == "Petrified_Pumpkin"
            original()
            if fossil:
                f.stock["Pumpkin"] = f.stock.get("Pumpkin", 0) + 1

        def fund(*args):
            self.assertEqual(f.worlds, 0)
            return True

        with self.api(f, dig=dig), patch.object(campaign, "_fund", side_effect=fund):
            self.assertTrue(campaign.produce_world(8))
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.stock["Pumpkin"], 9)
        for item in ("Coal", "Iron", "Quartz"):
            self.assertGreaterEqual(f.stock[item], 9)
        self.assertEqual(f.spawned, f.joined)

    def test_rice_is_harvested_before_descending_to_the_next_clay(self):
        f = RiceField(ws=3, capacity=4)
        with (
            self.api(f, plant=f.plant, harvest=f.harvest, can_harvest=lambda: True),
            patch.object(campaign, "_fund", return_value=True),
        ):
            self.assertTrue(campaign.produce_world(6))
        self.assertEqual(f.stock["Rice"], 18)
        self.assertFalse(f.entities)
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)

    def test_mushrooms_use_pushes_in_the_existing_world(self):
        f = StrataField(ws=8, capacity=4, height=3)
        with (
            self.api(f, push=f.push, can_push=f.can_push, measure=f.measure),
            patch.object(campaign, "_fund", return_value=True),
        ):
            self.assertTrue(campaign.produce_world(10))
        self.assertGreater(f.stock["Mushroom"], 0)
        self.assertTrue(f.pushes)
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)

    def test_dynamite_is_solved_with_no_world_reset(self):
        f = DynamiteField(ws=4, capacity=4)
        with (
            self.api(f, measure=f.measure),
            patch.object(campaign, "_fund", return_value=True),
        ):
            self.assertTrue(campaign.produce_world(6))
        self.assertTrue(f.solved)
        self.assertFalse(f.exploded)
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)

    def test_retired_foundation_is_not_rebuilt_at_a_lower_layer(self):
        f = MiningField(ws=6, capacity=4)
        f.layers = {
            (x, y): [
                "Grassland",
                "Rock",
                "Sand",
                "Sand",
                "Sand",
                "Limestone",
                "Rock",
                "Bedrock",
            ]
            for x in range(6)
            for y in range(6)
        }
        # A 5x5 foundation; outside it is ordinary rock.
        for pos in f.layers:
            if pos[0] == 5 or pos[1] == 5:
                f.layers[pos] = ["Rock"] * 7 + ["Bedrock"]

        def restore():
            self.assertFalse(f.pending)
            for x in range(5):
                for y in range(5):
                    f.depths[x, y] = 5
            return True, (0, 0, 5, -5)

        with (
            self.api(f),
            patch.object(campaign, "_fund", return_value=True),
            patch.object(
                achievements, "collect_current_pyramid", side_effect=restore
            ) as collect,
        ):
            self.assertTrue(campaign.produce_world(8))
        self.assertEqual(collect.call_count, 1)
        self.assertTrue(any(g == "Limestone" for _, g in f.digs))
        self.assertEqual(f.spawned, f.joined)

    def test_one_map_for_the_whole_observed_basalt_stratum_without_clearing(self):
        f = MiningField(ws=3, capacity=4)
        f.layers = {
            (x, y): ["Rock", "Basalt", "Rock", "Bedrock"]
            for x in range(3)
            for y in range(3)
        }
        with (
            self.api(f),
            patch.object(campaign, "_fund", return_value=True),
            patch.object(
                achievements,
                "collect_current_treasure",
                return_value=True,
            ) as collect,
        ):
            self.assertTrue(campaign.produce_world(4))
        self.assertEqual(collect.call_count, 1)
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)

    def test_collected_map_returns_to_mining_without_seeking_the_next_stratum(self):
        f = TreasureField(ws=3, capacity=4)
        with (
            self.api(f, measure=f.measure, harvest=f.harvest),
            patch.object(campaign, "_fund", return_value=True),
            patch.object(
                achievements,
                "run_tasks",
                side_effect=AssertionError("achievement queue invoked"),
            ),
            patch.object(
                achievements,
                "treasure_maps",
                side_effect=AssertionError("achievement farm invoked"),
            ),
        ):
            self.assertTrue(campaign.produce_world(4))
        self.assertEqual(f.maps, [2])
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)
        self.assertEqual(set(f.depths.values()), {4})

    def test_stale_basalt_cannot_make_the_collector_dig_for_a_deeper_map(self):
        f = TreasureField(ws=3, capacity=1)
        f.depths = {(x, y): 1 for x in range(3) for y in range(3)}
        with self.api(f, measure=f.measure, harvest=f.harvest):
            self.assertTrue(achievements.collect_current_treasure())
            self.assertTrue(mining.go_to(0, 0))
            before = len(f.digs)
            self.assertIsNone(achievements.collect_current_treasure())
        self.assertEqual(len(f.digs), before)
        self.assertEqual(f.maps, [2])

    def test_a_later_map_is_collected_only_when_mining_reaches_its_stratum(self):
        f = TreasureField(ws=3, capacity=4)
        with (
            self.api(f, measure=f.measure, harvest=f.harvest),
            patch.object(campaign, "_fund", return_value=True),
        ):
            self.assertTrue(campaign.produce_world(11))
        self.assertEqual(f.maps, [2, 9])
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)
        self.assertEqual(set(f.depths.values()), {11})

    def test_absent_map_is_skipped_but_a_real_route_failure_stops_mining(self):
        for result, expected in ((None, True), (False, False)):
            f = TreasureField(ws=3, capacity=4)
            with (
                self.subTest(result=result),
                self.api(f),
                patch.object(campaign, "_fund", return_value=True),
                patch.object(
                    achievements, "collect_current_treasure", return_value=result
                ) as collect,
            ):
                self.assertIs(campaign.produce_world(1), expected)
            self.assertEqual(collect.call_count, 1)
            self.assertEqual(f.spawned, f.joined)

    def test_funding_failure_does_not_prepare_the_world(self):
        f = MiningField(ws=6, capacity=4)
        with self.api(f), patch.object(campaign, "_fund", return_value=False):
            self.assertFalse(campaign.produce_world(8))
        self.assertEqual(f.worlds, 0)
        self.assertFalse(f.digs)

    def test_progress_of_one_resource_cannot_hide_another_stalled_target(self):
        f = MiningField(ws=3, capacity=1)
        f.stock["Dynamite"] = 0

        def world():
            f.stock["Block"] = f.stock.get("Block", 0) + 1
            return True

        with (
            f.api(infinite),
            patch.object(campaign, "produce_world", side_effect=world) as mine,
        ):
            self.assertFalse(infinite._mine_group(["Block", "Dynamite"], 100))
        self.assertEqual(mine.call_count, 8)

    def test_blocked_dynamite_stops_after_workers_join_without_resetting(self):
        f = DynamiteField(ws=4, capacity=4)
        with (
            self.api(f, measure=f.measure),
            patch.object(campaign, "_fund", return_value=True),
            patch.object(
                campaign.mine_dynamite, "solve_current_puzzle", return_value="blocked"
            ),
        ):
            self.assertFalse(campaign.produce_world(6))
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)
        self.assertFalse(f.pending)

    def test_rice_world_stops_before_spending_beyond_its_funded_budget(self):
        f = RiceField(ws=3, capacity=4)
        f.layers = {
            (x, y): ["Grassland"] + ["Clay"] * 7 + ["Bedrock"]
            for x in range(3)
            for y in range(3)
        }
        with (
            self.api(f, plant=f.plant, harvest=f.harvest, can_harvest=lambda: True),
            patch.object(campaign, "_fund", return_value=True),
        ):
            self.assertTrue(campaign.produce_world(10))
        self.assertEqual(f.stock["Rice"], 36)
        self.assertEqual(f.worlds, 1)
        self.assertEqual(f.spawned, f.joined)

    def test_infinite_groups_mining_but_keeps_bamboo_with_its_producer(self):
        f = MiningField(ws=6, capacity=4)
        visited = []

        def farm(item, target, *args):
            visited.append(item)
            return item == "Bamboo"  # Stop at the first round's Power refill.

        with (
            f.api(infinite),
            patch.object(infinite, "_mine_group", return_value=True) as grouped,
            patch.object(infinite.resource_manager, "farm", side_effect=farm),
        ):
            f.stock["Bamboo"] = 0
            self.assertFalse(infinite.run(["Coal", "Dynamite", "Bamboo"]))
        grouped.assert_called_once_with(["Coal", "Dynamite"], 1)
        self.assertEqual(visited, ["Bamboo", "Power"])

    def test_infinite_falls_back_to_individual_before_special_unlocks(self):
        f = MiningField(ws=6, capacity=4)
        with (
            f.api(infinite, num_unlocked=lambda skill: int(skill != "Pyramid")),
            patch.object(infinite, "_mine_group") as grouped,
            patch.object(infinite.resource_manager, "farm", return_value=False) as farm,
        ):
            self.assertFalse(infinite.run(["Coal"]))
        grouped.assert_not_called()
        self.assertEqual(farm.call_args.args[0], "Coal")


if __name__ == "__main__":
    unittest.main()
