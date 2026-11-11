"""Production contracts and funding dependencies, with fake native actions."""

import ast
import importlib
import sys
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

from test_multi_leaderboards import Field

SAVE = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE))
carrot = importlib.import_module("farm_carrot")
hay = importlib.import_module("farm_hay")
wood = importlib.import_module("farm_wood")
manager = importlib.import_module("resource_manager")
farm_utils = importlib.import_module("utils_farm")
movement = importlib.import_module("utils_move")
story_farm = importlib.import_module("story_farm")
story_mining = importlib.import_module("story_mining")


class Symbols:
    def __getattr__(self, name):
        return name


class ContractField(Field):
    def __init__(self, ws=3, capacity=2, level=1):
        super().__init__(ws, capacity)
        self.level = level
        self.seconds = 0
        self.seed_cost = {"Hay": 1, "Wood": 1}

    def budget(self):
        super().budget()
        self.seconds += 1

    def clear(self):
        self.events.append(("clear", None))
        super().clear()

    def plant(self, entity):
        if entity == "Carrot":
            if self.entity() == "Carrot":
                raise AssertionError("immature carrots must not be replanted")
            if any(
                self.stock.get(item, 0) < cost for item, cost in self.seed_cost.items()
            ):
                return False
        if not super().plant(entity):
            return False
        if entity == "Carrot":
            for item, cost in self.seed_cost.items():
                self.stock[item] -= cost
        self.events.append(("plant", entity))
        return True

    def harvest(self):
        entity = self.entity()
        result = super().harvest()
        if entity == "Carrot":
            self.stock["Carrot"] += 2 ** (self.level - 1) - 1
        return result


@contextmanager
def native(field, *modules, **overrides):
    defaults = dict(
        Items=Symbols(),
        Entities=Symbols(),
        Grounds=Symbols(),
        Unlocks=Symbols(),
        get_time=lambda: field.seconds,
        max_drones=lambda: field.capacity,
        num_unlocked=lambda skill: field.level if skill == "Carrots" else 1,
        get_cost=lambda _: field.seed_cost,
    )
    defaults.update(overrides)
    with ExitStack() as stack:
        for module in set(modules) | {movement, farm_utils}:
            stack.enter_context(field.api(module, **defaults))
        yield


class ProducerContractTests(unittest.TestCase):
    def test_satisfied_targets_do_not_read_configuration_or_modify_the_world(self):
        for module in (carrot, hay, wood):
            for mode in ("farm_single", "farm_multi"):
                with (
                    self.subTest(module=module.__name__, mode=mode),
                    patch.multiple(
                        module, Items=Symbols(), num_items=lambda _: 10, create=True
                    ),
                ):
                    self.assertIs(getattr(module, mode)(10), True)

    def test_requirements_are_absolute_and_cover_yield_fractional_targets_and_field_seeds(
        self,
    ):
        for level in (1, 2, 6, 10):
            field = ContractField(level=level)
            field.stock["Carrot"] = 5
            with self.subTest(level=level), native(field, carrot):
                needs = carrot.requirements(6.5)
                minimum_plants = 2 if level == 1 else 1
                self.assertEqual(
                    needs, {"Hay": minimum_plants + 18, "Wood": minimum_plants + 18}
                )
                self.assertEqual(carrot.requirements(5), {})

    def test_locked_and_unfunded_carrot_production_returns_false_before_moving(self):
        for level in (0, 1):
            field = ContractField(level=level)
            with self.subTest(level=level), native(field, carrot):
                self.assertIs(carrot.farm_single(10), False)
            self.assertFalse(field.plants)
            self.assertFalse(field.events)
            self.assertEqual(field.pos(), (0, 0))

    def test_funded_single_and_multi_finish_with_owned_workers_joined(self):
        for module in (carrot, hay, wood):
            for mode in ("farm_single", "farm_multi"):
                for capacity in (1, 2, 4, 32):
                    field = ContractField(capacity=capacity)
                    if module == carrot:
                        field.stock.update(Hay=100, Wood=100)
                    item = {carrot: "Carrot", hay: "Hay", wood: "Wood"}[module]
                    with (
                        self.subTest(
                            module=module.__name__, mode=mode, capacity=capacity
                        ),
                        native(field, module),
                    ):
                        self.assertIs(
                            getattr(module, mode)(113 if module != carrot else 13), True
                        )
                    self.assertGreaterEqual(
                        field.stock[item], 113 if module != carrot else 13
                    )
                    self.assertCountEqual(field.spawned, field.joined)
                    self.assertFalse(field.pending)
                    self.assertEqual(field.pos(), (0, 0))

    def test_declared_carrot_budget_is_sufficient_without_other_funding(self):
        for size in (1, 3, 8):
            for level in (1, 2, 6, 10):
                for mode in ("farm_single", "farm_multi"):
                    field = ContractField(ws=size, level=level)
                    with (
                        self.subTest(size=size, level=level, mode=mode),
                        native(field, carrot),
                    ):
                        needs = carrot.requirements(50.5)
                        field.stock.update(needs)
                        self.assertIs(getattr(carrot, mode)(50.5), True)
                    self.assertGreaterEqual(field.stock["Carrot"], 50.5)
                    self.assertGreaterEqual(field.stock["Hay"], 0)
                    self.assertGreaterEqual(field.stock["Wood"], 0)
                    self.assertNotIn(("clear", None), field.events)
                    self.assertFalse(field.pending)

    def test_preexisting_immature_carrots_are_preserved_until_they_can_be_harvested(
        self,
    ):
        field = ContractField()
        field.stock.update(Hay=100, Wood=100)
        for x in range(3):
            for y in range(3):
                field.entities[(x, y)] = "Carrot"
                field.grounds[(x, y)] = "Soil"
                field.unripe[(x, y)] = 2
        with native(field, carrot):
            self.assertIs(carrot.farm_multi(13), True)
        self.assertGreaterEqual(field.stock["Carrot"], 13)
        self.assertFalse(field.pending)

    def test_legacy_wood_size_override_is_rejected_before_work_when_inconsistent(self):
        field = ContractField(ws=3)
        with native(field, wood):
            self.assertIs(wood.farm_multi(10, 2), False)
        self.assertFalse(field.events)

    def test_manager_funds_carrot_before_growth_and_never_clears_it_mid_phase(self):
        for multi in (False, True):
            field = ContractField(capacity=2)
            with self.subTest(multi=multi), native(field, manager, carrot, hay, wood):
                self.assertIs(manager.farm("Carrot", 13, multi, False, True), True)
            self.assertGreaterEqual(field.stock["Carrot"], 13)
            first_carrot = field.events.index(("plant", "Carrot"))
            self.assertNotIn(("clear", None), field.events[first_carrot:])
            self.assertCountEqual(field.spawned, field.joined)
            self.assertFalse(field.pending)

    def test_parent_plant_failure_joins_previously_spawned_workers(self):
        field = ContractField(capacity=2)
        field.stock.update(Hay=100, Wood=100)
        field.fail_plant = (1, 0)
        with native(field, carrot):
            self.assertIs(carrot.farm_multi(10), False)
        self.assertTrue(field.spawned)
        self.assertCountEqual(field.spawned, field.joined)
        self.assertFalse(field.pending)

    def test_unowned_previous_workers_prevent_world_changes(self):
        for module in (hay, wood, carrot):
            field = ContractField()
            if module == carrot:
                field.stock.update(Hay=100, Wood=100)
            with (
                self.subTest(module=module.__name__),
                native(field, module, num_drones=lambda: 2),
            ):
                self.assertIs(module.farm_multi(10), False)
            self.assertFalse(field.events)
            self.assertFalse(field.plants)

    def test_locked_multi_mode_fails_before_world_changes_or_spawn(self):
        for module in (hay, wood, carrot):
            field = ContractField()
            if module == carrot:
                field.stock.update(Hay=100, Wood=100)
            with (
                self.subTest(module=module.__name__),
                native(
                    field,
                    module,
                    num_unlocked=lambda skill: 0 if skill == "Megafarm" else 1,
                    spawn_drone=Mock(side_effect=AssertionError("Megafarm is locked")),
                ),
            ):
                self.assertIs(module.farm_multi(10), False)
            self.assertFalse(field.events)

    def test_no_progress_is_bounded_in_parent_and_workers(self):
        for module in (hay, wood, carrot):
            field = ContractField()
            if module == carrot:
                field.stock.update(Hay=100, Wood=100)
            with (
                self.subTest(module=module.__name__),
                native(field, module, can_harvest=lambda: False),
            ):
                self.assertIs(module.farm_multi(10), False)
            self.assertFalse(field.pending)
            self.assertCountEqual(field.spawned, field.joined)
            self.assertLess(field.calls, field.limit)

    def test_missing_timing_unlock_uses_pass_limit_without_calling_time_api(self):
        for module in (hay, wood, carrot):
            field = ContractField()
            if module == carrot:
                field.stock.update(Hay=100, Wood=100)
            with (
                self.subTest(module=module.__name__),
                native(
                    field,
                    module,
                    can_harvest=lambda: False,
                    num_unlocked=lambda skill: 0 if skill == "Timing" else 1,
                    get_time=Mock(side_effect=AssertionError("Timing is locked")),
                ),
                patch.object(module, "MAX_IDLE_PASSES", 2),
            ):
                self.assertIs(module.farm_multi(10), False)
            self.assertFalse(field.pending)

    def test_funding_failure_never_enters_carrot_producer(self):
        field = ContractField()
        with (
            native(field, manager, carrot),
            patch.object(hay, "farm_single", return_value=False),
            patch.object(carrot, "farm_single") as produce,
        ):
            self.assertIs(manager.farm("Carrot", 10, False, False, True), False)
        produce.assert_not_called()

    def test_explicit_failure_is_not_hidden_by_a_sufficient_final_stock(self):
        stock = [0]

        def produce(_):
            stock[0] = 10
            return False

        with (
            patch.multiple(
                manager,
                Items=Symbols(),
                num_items=lambda _: stock[0],
                quick_print=Mock(),
                create=True,
            ),
            patch.object(hay, "farm_single", side_effect=produce),
        ):
            self.assertIs(manager.farm("Hay", 10, False, False, False), False)

    def test_requirement_failure_returns_instead_of_retrying_forever(self):
        field = ContractField()
        with (
            native(field, manager),
            patch.object(manager, "farm", return_value=False) as produce,
        ):
            self.assertIs(
                manager._fund_requirements({"Carrot": 100}, False, False, False), False
            )
        produce.assert_called_once()

    def test_migrated_producers_refuse_unfunded_phases(self):
        for name in ("farm_bone", "farm_cactus", "farm_power", "farm_pumpkin"):
            module = importlib.import_module(name)
            modes = (
                ("farm_single",)
                if name == "farm_bone"
                else ("farm_single", "farm_multi")
            )
            for mode in modes:
                field = ContractField()
                with (
                    self.subTest(module=name, mode=mode),
                    native(field, module),
                ):
                    self.assertIs(getattr(module, mode)(10), False)
                self.assertFalse(field.plants)

    def test_carrot_has_no_manager_or_other_producer_imports(self):
        tree = ast.parse((SAVE / "farm_carrot.py").read_text(encoding="utf-8"))
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        self.assertEqual(sorted(imports), ["utils_farm", "utils_move"])


class FailurePropagationTests(unittest.TestCase):
    def test_profile_uses_migrated_carrot_instead_of_the_isolated_benchmark(self):
        debug = importlib.import_module("utils_debug")
        with (
            patch.multiple(
                debug,
                Items=Symbols(),
                Unlocks=Symbols(),
                num_items=lambda _: 0,
                num_unlocked=lambda _: 1,
                get_time=Mock(side_effect=[10, 12]),
                get_tick_count=Mock(side_effect=[100, 400]),
                quick_print=Mock(),
                create=True,
            ),
            patch.object(manager, "farm", return_value=True) as produce,
        ):
            self.assertIs(debug.profile_carrot(100, True), True)
            produce.assert_called_once_with("Carrot", 100, True, False, True)
            debug.quick_print.assert_called_once_with(
                "Carrot profile", True, "seconds", 2, "ticks", 300
            )

    def test_main_and_underground_reset_do_not_enter_dlc_after_base_failure(self):
        main = importlib.import_module("main")
        reset = importlib.import_module("leaderboard_fastest_underground_reset")
        with (
            patch.object(story_farm, "run", return_value=False),
            patch.object(story_mining, "run") as dlc,
        ):
            self.assertIs(main.run(), False)
            dlc.assert_not_called()
        with (
            patch.object(reset.leaderboard_fastest_reset, "run", return_value=False),
            patch.object(story_mining, "run") as dlc,
        ):
            self.assertIs(reset.run(), False)
            dlc.assert_not_called()

    def test_base_story_propagates_upgrade_and_power_failures(self):
        for sunflowers in (0, 1):
            with (
                self.subTest(sunflowers=sunflowers),
                patch.multiple(
                    story_farm,
                    Unlocks=Symbols(),
                    Items=Symbols(),
                    num_unlocked=lambda skill: sunflowers
                    if skill == "Sunflowers"
                    else 0,
                    get_time=lambda: 0,
                    quick_print=Mock(),
                    create=True,
                ),
                patch.object(manager, "get_skill", return_value=False) as buy,
                patch.object(manager, "farm", return_value=False) as farm,
            ):
                self.assertIs(story_farm.run(), False)
            if sunflowers:
                buy.assert_not_called()
                farm.assert_called_once()
            else:
                buy.assert_called_once()
                farm.assert_not_called()

    def test_completed_base_story_returns_true_without_production(self):
        with (
            patch.multiple(
                story_farm,
                Unlocks=Symbols(),
                num_unlocked=lambda _: 100,
                get_time=lambda: 0,
                create=True,
            ),
            patch.object(manager, "farm") as farm,
        ):
            self.assertIs(story_farm.run(), True)
        farm.assert_not_called()

    def test_acknowledged_upgrade_without_level_increase_is_rejected(self):
        with (
            patch.multiple(
                manager,
                get_time=lambda: 0,
                num_unlocked=lambda _: 0,
                get_cost=lambda _: {"Hay": 1},
                unlock=lambda _: True,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(manager, "_fund_requirements", return_value=True),
        ):
            self.assertIs(manager.get_skill(0, False, False, False, 1, "Skill"), False)

    def test_action_helpers_return_native_refusals_and_navigation_stops_on_block(self):
        with patch.multiple(
            farm_utils,
            Items=Symbols(),
            num_items=lambda _: 100,
            num_drones=lambda: 1,
            get_water=lambda: 0,
            can_harvest=lambda: True,
            harvest=lambda: False,
            use_item=lambda *args: False,
            create=True,
        ):
            self.assertIs(farm_utils.water(), False)
            self.assertIs(farm_utils.fertilizer(), False)
            self.assertIs(farm_utils.q_harvest(), False)
        with patch.multiple(
            movement,
            get_pos_x=lambda: 0,
            get_pos_y=lambda: 0,
            East="E",
            West="W",
            North="N",
            South="S",
            move=Mock(return_value=False),
            create=True,
        ):
            self.assertIs(movement.go_to(2, 3, 8), False)
            movement.move.assert_called_once_with("E")


if __name__ == "__main__":
    unittest.main()
