"""Funded phases and ownership. Fixtures do not emulate game timing/concurrency."""

import ast
import importlib
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from test_multi_leaderboards import Field
from test_producer_contract import ContractField, Symbols, native
from test_resource_layout import PAIRED, SINGLE_ONLY

farm_utils = importlib.import_module("utils_farm")
mine_utils = importlib.import_module("utils_mine")
manager = importlib.import_module("resource_manager")
SAVE = Path(__file__).resolve().parents[1] / "Save0"


class CropField(ContractField):
    costs = {
        "Carrot": {"Hay": 1, "Wood": 1},
        "Pumpkin": {"Carrot": 2},
        "Cactus": {"Pumpkin": 1},
        "Sunflower": {"Carrot": 1},
        "Apple": {"Cactus": 2},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infected = set()
        self.companions = []

    def clear(self):
        super().clear()
        self.infected.clear()

    def plant(self, entity):
        needs = self.costs.get(entity, {})
        if any(self.stock.get(item, 0) < amount for item, amount in needs.items()):
            return False
        if not Field.plant(self, entity):
            return False
        for item, amount in needs.items():
            self.stock[item] -= amount
        self.events.append(("plant", entity))
        return True

    def swap(self, direction):
        super().swap(direction)
        return True

    def use_item(self, item, amount=1):
        if item not in ("Weird_Substance", "Fertilizer"):
            return True
        if self.stock.get(item, 0) < amount:
            return False
        self.assert_no_workers()
        self.stock[item] -= amount
        self.events.append(("infect", item))
        cells = [self.pos()]
        if item == "Weird_Substance":
            x, y = self.pos()
            cells += [
                ((x + 1) % self.ws, y),
                ((x - 1) % self.ws, y),
                (x, (y + 1) % self.ws),
                (x, (y - 1) % self.ws),
            ]
        for cell in cells:
            if cell in self.infected:
                self.infected.remove(cell)
            else:
                self.infected.add(cell)
        return True

    def harvest(self):
        if self.entity() == "Pumpkin":
            gain = int(len(self.infected) * min(self.ws, 6) / 2)
            self.stock["Weird_Substance"] = self.stock.get("Weird_Substance", 0) + gain
            self.infected.clear()
        return super().harvest()


def crop_native(field, *modules, **overrides):
    defaults = dict(
        Hats=Symbols(),
        get_cost=lambda entity: field.costs.get(entity, {}),
        get_companion=lambda: ("Bush", ((field.x + 1) % field.ws, field.y)),
    )
    defaults.update(overrides)
    return native(field, *modules, mine_utils, **defaults)


class PhaseContractTests(unittest.TestCase):
    def test_all_satisfied_goal_modes_and_batches_are_inert(self):
        for name in PAIRED + SINGLE_ONLY:
            module = importlib.import_module(name)
            with patch.multiple(
                module,
                Items=Symbols(),
                Entities=Symbols(),
                num_items=lambda _: 10,
                create=True,
            ):
                for attr in (
                    "farm_single",
                    "farm_multi",
                    "produce_single",
                    "produce_multi",
                    "farm_goo_single",
                    "farm_goo_multi",
                    "produce_goo_single",
                    "produce_goo_multi",
                ):
                    if not hasattr(module, attr):
                        continue
                    args = ("Grass", 10) if name == "farm_polyculture" else (10,)
                    with self.subTest(module=name, entry=attr):
                        self.assertIs(getattr(module, attr)(*args), True)

    def test_producers_and_mining_helpers_have_no_hidden_funding_imports(self):
        for name in PAIRED + SINGLE_ONLY + ("utils_mine",):
            tree = ast.parse((SAVE / f"{name}.py").read_text(encoding="utf-8"))
            imports = [
                a.name
                for n in ast.walk(tree)
                if isinstance(n, ast.Import)
                for a in n.names
            ]
            with self.subTest(module=name):
                self.assertTrue(all(n.startswith("utils_") for n in imports), imports)
                self.assertTrue(
                    hasattr(importlib.import_module(name), "requirements")
                    or name == "utils_mine"
                )

    def test_locked_producers_fail_before_actions(self):
        for name in PAIRED + SINGLE_ONLY:
            if name == "farm_hay":
                continue
            module = importlib.import_module(name)
            field = CropField()
            with (
                self.subTest(module=name),
                crop_native(field, module, num_unlocked=lambda _: 0),
            ):
                args = ("Carrot", 10) if name == "farm_polyculture" else (10,)
                self.assertIs(module.farm_single(*args), False)
            self.assertFalse(field.events)

    def test_locked_multi_and_unowned_workers_never_clear_a_world(self):
        for name in PAIRED:
            module = importlib.import_module(name)
            for unavailable in ("Megafarm", "ownership"):
                field = CropField()
                field.stock.update(
                    Hay=10**9,
                    Wood=10**9,
                    Carrot=10**9,
                    Pumpkin=10**9,
                    Rice=10**9,
                    Weird_Substance=10**9,
                )
                # Force the requested output below target, keeping dependencies funded.
                item = {
                    "farm_carrot": "Carrot",
                    "farm_pumpkin": "Pumpkin",
                    "farm_bamboo": "Bamboo",
                    "farm_haywood": "Wood",
                    "farm_rice": "Rice",
                }.get(name)
                if item:
                    field.stock[item] = 0
                if name == "farm_polyculture":
                    field.stock["Hay"] = 0
                if name == "farm_hay":
                    field.stock["Hay"] = 0
                if name == "farm_wood":
                    field.stock["Wood"] = 0
                with (
                    self.subTest(module=name, unavailable=unavailable),
                    crop_native(
                        field,
                        module,
                        num_unlocked=lambda skill: 0
                        if unavailable == "Megafarm" and skill == "Megafarm"
                        else 1,
                        num_drones=lambda: 2 if unavailable == "ownership" else 1,
                    ),
                ):
                    args = ("Grass", 10) if name == "farm_polyculture" else (10,)
                    self.assertIs(module.farm_multi(*args), False)
                self.assertFalse(field.events)

    def test_crop_phases_work_at_arbitrary_drone_capacities_and_join(self):
        for name, item in (
            ("farm_power", "Power"),
            ("farm_pumpkin", "Pumpkin"),
            ("farm_cactus", "Cactus"),
            ("farm_haywood", "Hay"),
        ):
            module = importlib.import_module(name)
            for capacity in (1, 2, 4, 32):
                field = CropField(capacity=capacity)
                field.stock.update(Carrot=10000, Pumpkin=10000)
                if name == "farm_pumpkin":
                    field.stock["Pumpkin"] = 0
                with (
                    self.subTest(module=name, capacity=capacity),
                    crop_native(field, module),
                ):
                    self.assertIs(module.farm_multi(13), True)
                self.assertGreaterEqual(field.stock[item], 13)
                if name == "farm_haywood":
                    self.assertGreaterEqual(field.stock["Wood"], 13)
                self.assertCountEqual(field.spawned, field.joined)
                self.assertFalse(field.pending)

    def test_parent_failure_still_joins_every_owned_worker(self):
        for name in ("farm_power", "farm_pumpkin", "farm_cactus", "farm_haywood"):
            module = importlib.import_module(name)
            field = CropField(capacity=2)
            field.stock.update(Carrot=10000, Pumpkin=10000)
            if name == "farm_pumpkin":
                field.stock["Pumpkin"] = 0
            field.fail_plant = (1, 0)
            with self.subTest(module=name), crop_native(field, module):
                self.assertIs(module.farm_multi(13), False)
            self.assertTrue(field.spawned)
            self.assertCountEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_goo_bootstraps_then_spends_only_profitable_nonoverlapping_charges(self):
        pumpkin = importlib.import_module("farm_pumpkin")
        for size in (3, 8, 32):
            field = CropField(ws=size)
            field.limit = 200000
            field.stock["Carrot"] = 100000
            with self.subTest(size=size), crop_native(field, pumpkin):
                self.assertEqual(pumpkin.goo_requirements(1)["Fertilizer"], 1)
                self.assertIs(pumpkin.produce_goo_multi(1), True)
                self.assertGreater(field.stock["Weird_Substance"], 0)
                initial = field.stock["Weird_Substance"]
                self.assertNotIn("Fertilizer", pumpkin.goo_requirements(initial + 1))
                self.assertIs(pumpkin.produce_goo_multi(initial + 1), True)
            self.assertGreater(field.stock["Weird_Substance"], initial)
            first_infection = field.events.index(("infect", "Fertilizer"))
            self.assertTrue(
                all(
                    e[0] != "join"
                    for e in field.events[
                        first_infection : field.events.index(("harvest", "Pumpkin"))
                    ]
                )
            )
            self.assertCountEqual(field.spawned, field.joined)

    def test_polyculture_funds_paid_roots_and_never_uses_other_producers(self):
        poly = importlib.import_module("farm_polyculture")
        for entity, item in (("Grass", "Hay"), ("Tree", "Wood"), ("Carrot", "Carrot")):
            field = CropField(ws=8, capacity=2)
            field.stock.update(Hay=100, Wood=100)
            with self.subTest(entity=entity), crop_native(field, poly):
                target = field.stock.get(item, 0) + 5
                # Non-carrot roots need no paid seed even when they request carrots first.
                self.assertIs(poly.farm_multi(entity, target), True)
            self.assertGreaterEqual(field.stock[item], target)
            self.assertFalse(field.pending)

    def test_ore_refuels_between_joined_worlds_in_the_manager(self):
        iron = importlib.import_module("mine_iron")
        coal = importlib.import_module("mine_coal")
        stock, events = {"Iron": 0, "Coal": 0}, []

        def coal_phase(qty):
            events.append("Coal")
            stock["Coal"] = qty
            return True

        def iron_phase(qty):
            events.append("Iron")
            self.assertEqual(stock["Coal"], 64)
            stock["Coal"] = 0
            stock["Iron"] += 1
            return True

        with (
            patch.multiple(
                manager,
                Items=Symbols(),
                Unlocks=Symbols(),
                num_items=lambda item: stock.get(item, 0),
                num_unlocked=lambda _: 1,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(iron, "requirements", side_effect=lambda _: {"Coal": 64}),
            patch.object(coal, "requirements", return_value={}),
            patch.object(iron, "produce_multi", side_effect=iron_phase),
            patch.object(coal, "produce_multi", side_effect=coal_phase),
        ):
            self.assertIs(manager.farm("Iron", 2, True, True, True), True)
        self.assertEqual(events, ["Coal", "Iron", "Coal", "Iron"])

    def test_manager_replenishes_seeds_only_between_completed_pumpkin_fields(self):
        modules = [
            importlib.import_module(n)
            for n in ("farm_pumpkin", "farm_carrot", "farm_hay", "farm_wood")
        ]
        field = CropField(capacity=2)
        with crop_native(field, manager, *modules):
            self.assertIs(manager.farm("Pumpkin", 150, True, False, True), True)
        self.assertGreaterEqual(field.stock["Pumpkin"], 150)
        self.assertFalse(field.pending)
        self.assertCountEqual(field.spawned, field.joined)
        # No seed-financing farm is allowed to clear a partially grown field.
        growing = False
        for kind, value in field.events:
            if kind == "plant" and value == "Pumpkin":
                growing = True
            elif kind == "harvest" and value == "Pumpkin":
                growing = False
            elif kind == "clear":
                self.assertFalse(growing)

    def test_polyculture_rerolls_paid_companions_and_rejects_unknown_entities(self):
        poly = importlib.import_module("farm_polyculture")
        field = CropField()
        with crop_native(
            field,
            poly,
            get_companion=Mock(side_effect=[("Carrot", (1, 0)), ("Bush", (1, 0))]),
        ):
            self.assertIs(poly.farm_single("Grass", 1), True)
            self.assertIs(poly.farm_single("Pumpkin", 1), False)
        self.assertNotIn("Carrot", [entity for _, entity in field.plants])

    def test_small_haywood_field_can_produce_both_outputs(self):
        combined = importlib.import_module("farm_haywood")
        field = CropField(ws=1)
        with crop_native(field, combined):
            self.assertIs(combined.farm_multi(3), True)
        self.assertGreaterEqual(field.stock["Hay"], 3)
        self.assertGreaterEqual(field.stock["Wood"], 3)

    def test_wood_plants_empty_soil_and_preserves_immature_matching_plants(self):
        wood = importlib.import_module("farm_wood")
        field = CropField()
        field.entities = {(x, y): None for x in range(3) for y in range(3)}
        with crop_native(field, wood, can_harvest=lambda: field.entity() is not None):
            self.assertIs(wood.farm_single(3), True)
        self.assertGreaterEqual(field.stock["Wood"], 3)
        field = CropField(ws=1)
        field.entities[(0, 0)] = "Bush"
        with crop_native(field, wood, can_harvest=lambda: False):
            self.assertIs(wood._column(1, False), True)
        self.assertFalse(field.plants)

    def test_bone_budget_uses_scaled_apple_cost_once_and_restores_hat_on_failure(self):
        bone = importlib.import_module("farm_bone")
        field = CropField(ws=3, level=6)
        field.stock["Cactus"] = 256
        with crop_native(field, bone, get_cost=lambda _: {"Cactus": 64}):
            self.assertEqual(bone.requirements(1), {"Cactus": 256})
        hats = Mock()
        with (
            crop_native(field, bone, change_hat=hats, set_world_size=Mock()),
            patch.object(bone, "_fill_even", return_value=False),
        ):
            self.assertIs(bone.produce_single(1), False)
        self.assertEqual(
            [call.args for call in hats.call_args_list],
            [("Dinosaur_Hat",), ("Straw_Hat",)],
        )

    def test_dynamite_propagates_navigation_failure_but_accepts_an_exploded_attempt(
        self,
    ):
        dynamite = importlib.import_module("mine_dynamite")
        field = CropField()
        with (
            crop_native(field, dynamite),
            patch.object(mine_utils, "prepare", return_value=True),
            patch.object(dynamite, "_puzzle_single", return_value="blocked"),
        ):
            self.assertIs(dynamite.produce_single(1), False)
        with (
            crop_native(field, dynamite),
            patch.object(mine_utils, "prepare", return_value=True),
            patch.object(dynamite, "_puzzle_single", return_value=False),
        ):
            self.assertIs(dynamite.produce_single(1), True)

    def test_none_results_and_funding_cycles_fail_without_recursive_overflow(self):
        hay = importlib.import_module("farm_hay")
        wood = importlib.import_module("farm_wood")
        with (
            patch.multiple(
                manager,
                Items=Symbols(),
                num_items=lambda _: 0,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(hay, "requirements", return_value={}),
            patch.object(hay, "farm_single", return_value=None) as produce,
        ):
            self.assertIs(manager.farm("Hay", 10, False, False, False), False)
            produce.assert_called_once()
        with (
            patch.multiple(
                manager,
                Items=Symbols(),
                num_items=lambda _: 0,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(hay, "requirements", return_value={"Wood": 1}),
            patch.object(wood, "requirements", return_value={"Hay": 1}),
            patch.object(hay, "farm_single") as produce,
        ):
            self.assertIs(manager.farm("Hay", 10, False, False, False), False)
            produce.assert_not_called()

    def test_failed_mining_batch_and_mushroom_movement_are_propagated(self):
        mushroom = importlib.import_module("farm_mushroom")
        with (
            patch.multiple(
                mine_utils, num_items=lambda _: 0, get_world_size=lambda: 3, create=True
            ),
            patch.object(mine_utils, "prepare", return_value=True),
            patch.object(mine_utils, "run_columns", return_value=False) as run,
        ):
            self.assertIs(mine_utils.farm_columns(Mock(), "Rice", 10, True), False)
            run.assert_called_once()
        field = CropField()
        with (
            crop_native(field, mushroom),
            patch.object(mine_utils, "prepare", return_value=True),
            patch.object(mushroom, "_stratum_single", return_value=False) as work,
        ):
            self.assertIs(mushroom.farm_single(10), False)
            work.assert_called_once()

    def test_passive_fertilizer_is_waited_for_without_clearing(self):
        with patch.multiple(
            manager,
            Items=Symbols(),
            Unlocks=Symbols(),
            num_items=Mock(side_effect=[0, 0, 0, 1, 1, 1, 1]),
            num_unlocked=lambda _: 1,
            get_time=lambda: 0,
            quick_print=Mock(),
            create=True,
        ):
            self.assertIs(manager.farm("Fertilizer", 1, False, False, False), True)


class PowerColumnProductionTests(unittest.TestCase):
    def setUp(self):
        self.power = importlib.import_module("farm_power")

    def test_stock_checks_do_not_restart_the_workers_after_sixteen_rounds(self):
        field = CropField(ws=4, capacity=4)
        field.stock["Carrot"] = 5000
        with (
            crop_native(field, self.power, manager),
            patch.object(
                self.power.utils_farm,
                "is_funded",
                wraps=self.power.utils_farm.is_funded,
            ) as checks,
        ):
            self.assertTrue(manager.farm("Power", 1300, True, False, False))
        self.assertEqual(sum(e[0] == "clear" for e in field.events), 1)
        self.assertEqual(len(field.spawned), 3)
        self.assertEqual(field.spawned, field.joined)
        self.assertGreaterEqual(field.stock["Power"], 1300)
        self.assertGreater(
            sum(
                call.args[0] == {"Carrot": 4 * self.power.CHECK_EVERY_ROUNDS}
                for call in checks.call_args_list
            ),
            1,
        )

    def test_available_stock_is_partitioned_using_the_limiting_ingredient(self):
        field = CropField(ws=4, capacity=4)
        field.costs = dict(field.costs)
        field.costs["Sunflower"] = {"Carrot": 2, "Hay": 3}
        field.stock.update(Carrot=5001, Hay=1538)
        with crop_native(
            field, self.power, get_entity_type=lambda: field.entities.get(field.pos())
        ):
            self.assertEqual(
                self.power.requirements(10**6, True), {"Carrot": 1024, "Hay": 1536}
            )
            self.assertTrue(self.power.produce_multi(10**6))
        self.assertEqual(len(field.plants), 512)
        self.assertEqual(field.stock["Carrot"], 5001 - 1024)
        self.assertEqual(field.stock["Hay"], 2)
        self.assertEqual(field.spawned, field.joined)

    def test_checkpoint_shortage_drains_paid_plants_without_another_planting(self):
        field = CropField(ws=4, capacity=1)
        chunk = 4 * self.power.CHECK_EVERY_ROUNDS
        field.stock["Carrot"] = 2 * chunk
        plant = field.plant

        def spend_remaining_inputs(entity):
            result = plant(entity)
            if len(field.plants) == chunk:
                field.stock["Carrot"] = 0
            return result

        with crop_native(
            field,
            self.power,
            plant=spend_remaining_inputs,
            get_entity_type=lambda: field.entities.get(field.pos()),
        ):
            self.assertTrue(self.power._column_continuous(4, 10**6, 2 * chunk))
        self.assertEqual(len(field.plants), chunk)
        self.assertEqual(field.stock["Power"], chunk)
        self.assertFalse(field.entities)

    def test_productive_columns_still_stop_if_power_stock_never_increases(self):
        field = CropField(ws=4, capacity=4)
        field.stock["Carrot"] = 10000
        harvest = field.harvest

        def consume_gain():
            result = harvest()
            field.stock["Power"] = 0
            return result

        with (
            crop_native(field, self.power, harvest=consume_gain),
            patch.object(self.power, "MAX_IDLE_SWEEPS", 3),
        ):
            self.assertFalse(self.power.produce_multi(100))
        self.assertTrue(field.harvests)
        self.assertEqual(field.spawned, field.joined)

    def test_free_seeds_and_invalid_checkpoint_configuration(self):
        field = CropField(ws=4, capacity=4)
        field.costs = dict(field.costs)
        field.costs["Sunflower"] = {}
        with crop_native(field, self.power):
            self.assertEqual(self.power.requirements(20, True), {})
            self.assertTrue(self.power.produce_multi(20))
        self.assertEqual(field.spawned, field.joined)
        for interval in (0, 1.5):
            field = CropField(ws=4, capacity=4)
            field.stock["Carrot"] = 10000
            with (
                self.subTest(interval=interval),
                crop_native(field, self.power),
                patch.object(self.power, "CHECK_EVERY_ROUNDS", interval),
            ):
                self.assertFalse(self.power.produce_multi(20))
            self.assertFalse(field.events)

    def test_finite_phase_uses_exactly_its_funded_seed_budget_and_joins(self):
        for capacity in (1, 2, 4, 32):
            field = CropField(ws=4, capacity=capacity)
            with self.subTest(capacity=capacity), crop_native(field, self.power):
                needs = self.power.requirements(10**9, True)
                expected = min(4, capacity) * 4 * self.power.CHECK_EVERY_ROUNDS
                self.assertEqual(needs, {"Carrot": expected})
                field.stock.update(needs)
                self.assertTrue(self.power.produce_multi(10**9))
            self.assertEqual(len(field.plants), expected)
            self.assertEqual(
                sum(e == "Sunflower" for _, e, _ in field.harvests), expected
            )
            self.assertEqual(field.stock["Carrot"], 0)
            self.assertLess(field.stock["Power"], 10**9)
            self.assertEqual(sum(e[0] == "clear" for e in field.events), 1)
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_missing_one_seed_fails_before_clearing_or_spawning(self):
        field = CropField(ws=4, capacity=4)
        with crop_native(field, self.power):
            needs = self.power.requirements(100, True)
            field.stock["Carrot"] = needs["Carrot"] - 1
            self.assertFalse(self.power.produce_multi(100))
        self.assertFalse(field.events)

    def test_immature_flowers_are_kept_and_other_tiles_are_visited(self):
        field = CropField(ws=4, capacity=1)
        field.entities[0, 0] = "Sunflower"
        field.grounds[0, 0] = "Soil"
        field.values[0, 0] = 7
        field.unripe[0, 0] = 3
        with crop_native(field, self.power):
            self.assertTrue(self.power._column_continuous(4, 1000, 0))
        self.assertFalse(field.plants)
        self.assertEqual(field.stock["Power"], 1)
        self.assertGreater(len(field.harvests), 1)

    def test_multi_path_does_not_measure_petals_or_use_targeted_travel(self):
        field = CropField(ws=4, capacity=4)
        field.stock["Carrot"] = 10000
        with (
            crop_native(
                field,
                self.power,
                measure=Mock(side_effect=AssertionError("petal measurement")),
            ),
            patch.object(
                self.power.utils_move,
                "go_to",
                side_effect=AssertionError("targeted travel"),
            ),
        ):
            self.assertTrue(self.power.farm_multi(20))
        self.assertGreaterEqual(field.stock["Power"], 20)
        self.assertEqual(field.spawned, field.joined)

    def test_no_water_is_optional(self):
        field = CropField(ws=4, capacity=4)
        field.stock.update(Carrot=10000, Water=0)
        with crop_native(
            field,
            self.power,
            get_water=lambda: 0,
            use_item=Mock(side_effect=AssertionError("unfunded water")),
        ):
            self.assertTrue(self.power.farm_multi(20))
        self.assertEqual(field.spawned, field.joined)

    def test_no_growth_stops_with_and_without_timing_and_joins(self):
        for timed in (False, True):
            field = CropField(ws=4, capacity=4)
            field.stock["Carrot"] = 10000
            plant = field.plant

            def never_ripe(entity):
                result = plant(entity)
                field.unripe[field.pos()] = 10**9
                return result

            with (
                self.subTest(timed=timed),
                crop_native(
                    field,
                    self.power,
                    plant=never_ripe,
                    num_unlocked=lambda skill: int(timed) if skill == "Timing" else 1,
                    get_time=lambda: field.calls * 100,
                ),
                patch.object(self.power, "MAX_IDLE_SWEEPS", 3),
            ):
                self.assertFalse(self.power.produce_multi(1000))
            self.assertEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_manager_funds_multi_budget_before_the_power_world_is_prepared(self):
        field = CropField(ws=4, capacity=4)
        needs = []

        def fund(requirements, *args):
            self.assertFalse(any(e[0] == "clear" for e in field.events))
            needs.append(requirements)
            field.stock.update(requirements)
            return True

        with (
            crop_native(field, self.power, manager),
            patch.object(manager, "_fund_requirements", side_effect=fund),
        ):
            self.assertTrue(manager.farm("Power", 20, True, False, False))
        self.assertEqual(needs, [{"Carrot": 4 * 4 * self.power.CHECK_EVERY_ROUNDS}])
        self.assertEqual(field.spawned, field.joined)


if __name__ == "__main__":
    unittest.main()
