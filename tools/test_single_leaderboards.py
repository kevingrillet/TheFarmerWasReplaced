"""Standalone benchmark contracts; fake APIs do not model TFWR physics or ticks."""

import ast
import importlib.util
import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
HAY_MODULE = "leaderboard_hay_single"
TARGETS = {
    HAY_MODULE: ("Hay", 100000000),
    "leaderboard_wood_single": ("Wood", 500000000),
    "leaderboard_carrot_single": ("Carrot", 100000000),
    "leaderboard_cactus_single": ("Cactus", 131072),
    "leaderboard_pumpkin_single": ("Pumpkin", 10000000),
    "leaderboard_power_single": ("Power", 10000),
    "leaderboard_gold_single": ("Gold", 616448),
}


def symbols(names):
    return SimpleNamespace(**{name: name for name in names.split()})


ITEMS = symbols(
    "Hay Wood Carrot Cactus Pumpkin Power Gold Water Fertilizer Weird_Substance"
)
ENTITIES = symbols(
    "Grass Bush Tree Carrot Cactus Pumpkin Dead_Pumpkin Sunflower Treasure"
)
GROUNDS = symbols("Grassland Soil")
DIRECTIONS = dict(North="North", East="East", South="South", West="West")


def load(name):
    # Entry actions would fail during import: no game globals are supplied here.
    spec = importlib.util.spec_from_file_location(name, SAVE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Farm:
    """Tiny wrapping field with immediate growth, only for control-flow assertions."""

    def __init__(self, ws=3):
        self.ws, self.x, self.y = ws, 0, 0
        self.entities = {}
        self.grounds = {}
        self.values = {}
        self.stock = {}
        self.harvests = []
        self.plants = []
        self.moves = []
        self.calls = 0

    def pos(self):
        return self.x, self.y

    def entity(self):
        return self.entities.get(self.pos(), ENTITIES.Grass)

    def move(self, direction):
        self.calls += 1
        if self.calls > 10000:
            raise AssertionError("unexpected non-terminating traversal")
        dx, dy = {"North": (0, 1), "East": (1, 0), "South": (0, -1), "West": (-1, 0)}[
            direction
        ]
        self.x = (self.x + dx) % self.ws
        self.y = (self.y + dy) % self.ws
        self.moves.append(direction)
        return True

    def plant(self, entity):
        self.entities[self.pos()] = entity
        self.plants.append((self.pos(), entity))
        return True

    def harvest(self):
        entity = self.entity()
        self.harvests.append((self.pos(), entity))
        item = {"Grass": "Hay", "Bush": "Wood", "Tree": "Wood", "Carrot": "Carrot"}.get(
            entity, entity
        )
        self.stock[item] = self.stock.get(item, 0) + 1
        self.entities.pop(self.pos(), None)
        return True

    def till(self):
        self.grounds[self.pos()] = GROUNDS.Soil
        return True

    def api(self, module, **overrides):
        api = dict(
            Items=ITEMS,
            Entities=ENTITIES,
            Grounds=GROUNDS,
            get_world_size=lambda: self.ws,
            get_pos_x=lambda: self.x,
            get_pos_y=lambda: self.y,
            get_entity_type=self.entity,
            get_ground_type=lambda: self.grounds.get(self.pos(), GROUNDS.Grassland),
            get_water=lambda: 1,
            num_items=lambda item: self.stock.get(item, 0),
            can_harvest=lambda: True,
            move=self.move,
            plant=self.plant,
            harvest=self.harvest,
            till=self.till,
            use_item=Mock(return_value=True),
            **DIRECTIONS,
        )
        api.update(overrides)
        return patch.multiple(module, **api, create=True)


class SingleLeaderboardTests(unittest.TestCase):
    def test_no_import_dependencies_and_exact_official_targets(self):
        for name, (_, target) in TARGETS.items():
            with self.subTest(name=name):
                tree = ast.parse((SAVE / (name + ".py")).read_text(encoding="utf-8"))
                self.assertFalse(
                    any(
                        isinstance(node, (ast.Import, ast.ImportFrom))
                        for node in ast.walk(tree)
                    )
                )
                self.assertEqual(load(name).TARGET, target)

    def test_satisfied_target_needs_no_farm_api(self):
        for name in TARGETS:
            module = load(name)
            with (
                self.subTest(name=name),
                patch.multiple(
                    module, Items=ITEMS, num_items=lambda item: 12, create=True
                ),
            ):
                self.assertTrue(module.run(10))

    def test_local_navigation_wraps_on_shortest_path(self):
        for name in (
            "leaderboard_cactus_single",
            "leaderboard_pumpkin_single",
            "leaderboard_power_single",
        ):
            farm, module = Farm(8), load(name)
            with self.subTest(name=name), farm.api(module):
                module._go_to(7, 7, 8)
                self.assertEqual(farm.pos(), (7, 7))
                self.assertEqual(farm.moves, ["West", "South"])

    def test_wood_and_carrot_traversals_produce_their_own_resource(self):
        for name, item, allowed in (
            ("leaderboard_wood_single", "Wood", {"Tree", "Bush"}),
            ("leaderboard_carrot_single", "Carrot", {"Carrot"}),
        ):
            farm, module = Farm(), load(name)
            with self.subTest(name=name), farm.api(module):
                self.assertTrue(module.run(1))
                self.assertGreaterEqual(farm.stock[item], 1)
                self.assertEqual({entity for _, entity in farm.plants}, allowed)
                for (x, y), entity in farm.plants:
                    if name == "leaderboard_wood_single":
                        self.assertEqual(entity, "Tree" if (x + y) % 2 == 0 else "Bush")
                    else:
                        self.assertEqual(farm.grounds[(x, y)], "Soil")

    def test_cactus_sort_is_monotone_in_both_axes_before_harvest(self):
        for seed in range(5):
            farm, module = Farm(4), load("leaderboard_cactus_single")
            rng = random.Random(seed)

            def measure():
                value = rng.randrange(10)
                farm.values[farm.pos()] = value
                return value

            def swap(direction):
                x, y = farm.pos()
                neighbor = (x, y - 1) if direction == "South" else (x - 1, y)
                a, b = farm.pos(), neighbor
                farm.values[a], farm.values[b] = farm.values[b], farm.values[a]
                return True

            def harvest():
                for y in range(farm.ws):
                    for x in range(farm.ws):
                        value = farm.values[(x, y)]
                        if x:
                            self.assertGreaterEqual(value, farm.values[(x - 1, y)])
                        if y:
                            self.assertGreaterEqual(value, farm.values[(x, y - 1)])
                farm.stock["Cactus"] = 256
                return True

            with (
                self.subTest(seed=seed),
                farm.api(
                    module,
                    measure=measure,
                    swap=swap,
                    harvest=harvest,
                    # Do not harvest partially planted fields; growth is not modeled.
                    can_harvest=lambda: len(farm.values) == 16,
                ),
            ):
                self.assertTrue(module.run(256))

    def test_pumpkin_replants_dead_tile_before_full_field_harvest(self):
        farm, module = Farm(), load("leaderboard_pumpkin_single")
        failed_once = set()

        def plant(entity):
            farm.plant(entity)
            if farm.pos() not in failed_once:
                failed_once.add(farm.pos())
                farm.entities[farm.pos()] = ENTITIES.Dead_Pumpkin
            return True

        def harvest():
            if farm.entity() == ENTITIES.Pumpkin:
                self.assertEqual(len(farm.entities), farm.ws**2)
                self.assertEqual(set(farm.entities.values()), {ENTITIES.Pumpkin})
                farm.stock["Pumpkin"] = 100
            return True

        with farm.api(
            module,
            plant=plant,
            harvest=harvest,
            can_harvest=lambda: farm.entity() == ENTITIES.Pumpkin,
        ):
            self.assertTrue(module.run(100))
        self.assertEqual(len(farm.plants), 2 * farm.ws**2)

    def test_sunflowers_do_not_skip_same_petal_bucket_or_lower_priority(self):
        farm, module = Farm(4), load("leaderboard_power_single")
        harvested = []

        def measure():
            value = 7 + (farm.x + farm.y) % 3
            farm.values[farm.pos()] = value
            return value

        def harvest():
            harvested.append(farm.values[farm.pos()])
            farm.entities.pop(farm.pos())
            farm.stock["Power"] = farm.stock.get("Power", 0) + 1
            return True

        with farm.api(
            module,
            measure=measure,
            harvest=harvest,
            can_harvest=lambda: farm.entity() == ENTITIES.Sunflower,
        ):
            self.assertFalse(module._grow_and_harvest(farm.ws, 100))
        self.assertEqual(len(harvested), 16)
        self.assertEqual(harvested, sorted(harvested, reverse=True))

    def test_sunflower_stops_at_target_with_power_margin(self):
        module = load("leaderboard_power_single")
        with (
            patch.multiple(
                module,
                Items=ITEMS,
                num_items=lambda item: 0,
                get_world_size=lambda: 8,
                create=True,
            ),
            patch.object(module, "_grow_and_harvest", return_value=True) as grow,
        ):
            self.assertTrue(module.run(10))
        grow.assert_called_once_with(8, 11)

    def test_maze_creates_max_size_and_stops_on_blocked_path(self):
        for blocked in (False, True):
            module = load("leaderboard_gold_single")
            stock, arrived = [0], [False]
            use_item, clear = Mock(return_value=True), Mock()

            def move(direction):
                arrived[0] = not blocked
                return not blocked

            def harvest():
                stock[0] = 100

            with (
                self.subTest(blocked=blocked),
                patch.multiple(
                    module,
                    Items=ITEMS,
                    Entities=ENTITIES,
                    Unlocks=symbols("Mazes"),
                    num_items=lambda item: stock[0],
                    num_unlocked=lambda unlock: 3,
                    get_world_size=lambda: 8,
                    clear=clear,
                    plant=lambda entity: True,
                    use_item=use_item,
                    move=move,
                    get_entity_type=lambda: ENTITIES.Treasure
                    if arrived[0]
                    else ENTITIES.Bush,
                    harvest=harvest,
                    quick_print=Mock(),
                    **DIRECTIONS,
                    create=True,
                ),
            ):
                self.assertEqual(module.run(100), not blocked)
                use_item.assert_called_once_with(ITEMS.Weird_Substance, 32)
                clear.assert_called_once()


class BushFarm(Farm):
    """Native overplant/respawn contracts plus an artificial delayed-readiness gate."""

    def __init__(self):
        super().__init__(8)
        self.resizes = []
        self.grass_planted_at = {}
        self.selected = set()
        self.companion_queries = []

    def resize(self, size):
        self.resizes.append(size)
        self.ws, self.x, self.y = size, 0, 0
        self.entities.clear()
        self.grounds.clear()

    def plant(self, entity):
        if self.entity() != ENTITIES.Grass:
            return False
        if entity == ENTITIES.Grass:
            self.selected.add(self.pos())
            self.grass_planted_at[self.pos()] = self.calls
        return super().plant(entity)

    def companion(self):
        self.companion_queries.append(self.pos())
        if self.pos() not in self.selected:
            return ENTITIES.Tree, (1, self.y)
        return ENTITIES.Bush, (1, self.y)

    def ready(self):
        return (
            self.entity() == ENTITIES.Grass
            and self.pos() in self.grass_planted_at
            and self.calls - self.grass_planted_at[self.pos()] > self.ws
        )

    def harvest(self):
        if not self.ready() or self.pos() not in self.selected:
            raise AssertionError("harvested immature grass or an unselected request")
        if self.entities.get((1, self.y)) != ENTITIES.Bush:
            raise AssertionError("missing bush companion")
        self.harvests.append((self.pos(), self.entity()))
        self.stock[ITEMS.Hay] = self.stock.get(ITEMS.Hay, 0) + 1
        # Grassland immediately respawns Grass; its companion request changes.
        self.entities[self.pos()] = ENTITIES.Grass
        self.selected.remove(self.pos())
        return True

    def api(self, module, **overrides):
        defaults = dict(
            set_world_size=self.resize,
            get_companion=self.companion,
            can_harvest=self.ready,
            quick_print=Mock(),
        )
        defaults.update(overrides)
        return super().api(module, **defaults)


class HayLeaderboardTests(unittest.TestCase):
    def test_snake_setup_fills_two_columns_in_six_moves_without_observations(self):
        farm, module = BushFarm(), load(HAY_MODULE)
        farm.resize(3)
        observe = Mock(side_effect=AssertionError("setup should not read its position"))
        with farm.api(module, get_pos_x=observe, get_pos_y=observe):
            self.assertTrue(module.prepare_field())
        self.assertEqual(farm.pos(), (2, 0))
        self.assertEqual(len(farm.moves), 6)
        self.assertEqual(
            {pos for pos, entity in farm.plants if entity == ENTITIES.Bush},
            {(x, y) for x in (0, 1) for y in range(3)},
        )
        self.assertEqual(len(farm.plants), 6)
        self.assertFalse(any(x == 2 for x, _ in farm.entities))
        observe.assert_not_called()

    def test_selection_rejects_other_species_and_grass_column_without_moving(self):
        module = load(HAY_MODULE)
        requests = Mock(
            side_effect=[
                None,
                ("Tree", (1, 0)),
                ("Carrot", (1, 0)),
                ("Bush", (2, 1)),
                ("Bush", (1, 0)),
            ]
        )
        plant, move = Mock(return_value=True), Mock()
        with patch.multiple(
            module,
            Entities=ENTITIES,
            get_companion=requests,
            plant=plant,
            move=move,
            create=True,
        ):
            self.assertTrue(module.select_companion())
        self.assertEqual(plant.call_count, 4)
        self.assertTrue(
            all(call.args == (ENTITIES.Grass,) for call in plant.call_args_list)
        )
        move.assert_not_called()

    def test_refused_replant_returns_instead_of_looping(self):
        module = load(HAY_MODULE)
        with patch.multiple(
            module,
            Entities=ENTITIES,
            get_companion=lambda: (ENTITIES.Carrot, (1, 0)),
            plant=Mock(return_value=False),
            quick_print=Mock(),
            create=True,
        ):
            self.assertFalse(module.select_companion())
            module.plant.assert_called_once_with(ENTITIES.Grass)

    def test_complete_run_keeps_bushes_and_selected_immature_grass(self):
        farm, module = BushFarm(), load(HAY_MODULE)
        with farm.api(module):
            self.assertTrue(module.run(6))
        self.assertEqual(farm.resizes, [3])
        self.assertEqual(farm.stock[ITEMS.Hay], 6)
        self.assertEqual(len(farm.harvests), 6)
        self.assertEqual({x for (x, _), _ in farm.harvests}, {2})
        self.assertEqual(sum(entity == ENTITIES.Bush for _, entity in farm.plants), 6)
        self.assertEqual(sum(entity == ENTITIES.Grass for _, entity in farm.plants), 6)
        self.assertEqual(len(farm.companion_queries), 12)
        self.assertTrue(
            all(entity in (ENTITIES.Grass, ENTITIES.Bush) for _, entity in farm.plants)
        )

    def test_water_is_only_used_below_threshold_with_available_stock(self):
        for stock, water, expected_calls in ((0, 0, 0), (1, 0.4, 1), (1, 0.9, 0)):
            module, use = load(HAY_MODULE), Mock(return_value=True)
            with (
                self.subTest(stock=stock, water=water),
                patch.multiple(
                    module,
                    Items=ITEMS,
                    num_items=lambda item: stock,
                    get_water=lambda: water,
                    use_item=use,
                    create=True,
                ),
            ):
                module.water()
            self.assertEqual(use.call_count, expected_calls)


if __name__ == "__main__":
    unittest.main()
