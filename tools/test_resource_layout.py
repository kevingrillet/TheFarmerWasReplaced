"""Resource-module wiring checks, without running the game or modeling timing."""

import ast
import importlib
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SAVE = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE))
PAIRED = (
    "farm_hay",
    "farm_wood",
    "farm_haywood",
    "farm_carrot",
    "farm_pumpkin",
    "farm_cactus",
    "farm_power",
    "farm_gold",
    "farm_polyculture",
    "farm_rice",
    "farm_bamboo",
    "farm_mushroom",
    "mine_block",
    "mine_coal",
    "mine_iron",
    "mine_quartz",
    "mine_dynamite",
)
SINGLE_ONLY = ("farm_bone",)
UTILITIES = (
    "resource_manager",
    "utils_debug",
    "utils_farm",
    "utils_math",
    "utils_mine",
    "utils_move",
)


def isolated(code, *args):
    return subprocess.run(
        [sys.executable, "-I", "-c", textwrap.dedent(code), str(SAVE), *args],
        capture_output=True,
        text=True,
        timeout=15,
    )


class ResourceLayoutTests(unittest.TestCase):
    def test_resource_modules_expose_the_preserved_modes(self):
        for name in PAIRED + SINGLE_ONLY:
            with self.subTest(name=name):
                module = importlib.import_module(name)
                self.assertTrue(callable(module.farm_single))
                self.assertEqual(hasattr(module, "farm_multi"), name in PAIRED)

    def test_new_entry_modules_and_all_resources_are_inert_when_imported(self):
        entries = [p.stem for p in SAVE.glob("leaderboard*.py")]
        names = (
            list(PAIRED + SINGLE_ONLY + UTILITIES)
            + entries
            + [
                "main",
                "story_farm",
                "story_mining",
                "story_infinite",
                "ZZAchievementDLC",
            ]
        )
        code = """
            import builtins, importlib, sys
            class Categories:
                def __getattr__(self, name):
                    value = object()
                    setattr(self, name, value)
                    return value
            builtins.Leaderboards = Categories()
            sys.path.insert(0, sys.argv[1])
            for name in sys.argv[2:]:
                importlib.import_module(name)
        """
        result = isolated(code, *names)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manager_import_and_satisfied_or_locked_targets_load_no_producer(self):
        result = isolated(
            """
            import importlib, sys
            from types import SimpleNamespace
            sys.path.insert(0, sys.argv[1])
            manager = importlib.import_module("resource_manager")
            producers = set(sys.argv[2:])
            assert not producers.intersection(sys.modules)
            manager.num_items = lambda _: 10
            assert manager.farm("Hay", 10, True, True, True)
            class Symbols:
                def __getattr__(self, name):
                    return name
            manager.Items = Symbols()
            manager.Unlocks = SimpleNamespace(Coal="Coal")
            manager.num_items = lambda _: 0
            manager.num_unlocked = lambda _: 0
            assert not manager.farm("Coal", 10, True, True, True)
            assert not producers.intersection(sys.modules)
            """,
            *(PAIRED + SINGLE_ONLY),
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_producers_skip_manager_when_prerequisites_are_disabled(self):
        result = isolated(
            """
            import importlib, sys
            from types import SimpleNamespace
            from unittest.mock import Mock
            sys.path.insert(0, sys.argv[1])
            for name in sys.argv[2:]:
                module = importlib.import_module(name)
                assert "resource_manager" not in sys.modules, name
                module.get_world_size = lambda: 2
                module.num_items = lambda _: 10
                module.Items = SimpleNamespace(**{n: n for n in "Bone Cactus Carrot Power Pumpkin Weird_Substance".split()})
                module.Hats = SimpleNamespace(Straw_Hat="Straw_Hat")
                module.change_hat = Mock()
                module.utils_move.init = Mock()
                module.farm_single(10)
                assert "resource_manager" not in sys.modules, name
            """,
            "farm_bone",
            "farm_cactus",
            "farm_power",
            "farm_pumpkin",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_imports_and_module_members_resolve(self):
        sources = {
            p.stem: ast.parse(p.read_text(encoding="utf-8"))
            for p in SAVE.glob("*.py")
            if p.name != "__builtins__.py"
        }
        exports = {}
        for name, tree in sources.items():
            members = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
            members |= {
                a.name for n in tree.body if isinstance(n, ast.Import) for a in n.names
            }
            members |= {
                target.id
                for node in tree.body
                if isinstance(node, ast.Assign)
                for root in node.targets
                for target in ast.walk(root)
                if isinstance(target, ast.Name)
            }
            exports[name] = members
        for name, tree in sources.items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name, sources, (name, alias.name))
                elif (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in sources
                ):
                    self.assertIn(
                        node.attr, exports[node.value.id], (name, ast.unparse(node))
                    )

    def test_main_runs_both_stories_before_infinite(self):
        module = importlib.import_module("main")
        order = []
        with (
            patch.object(module, "INFINITE_MODE", "resources"),
            patch.object(module, "POWER_TARGET", 0),
            patch.object(
                module.story_farm,
                "run",
                side_effect=lambda: order.append("base") or True,
            ),
            patch.object(
                module.story_mining,
                "run",
                side_effect=lambda: order.append("dlc") or True,
            ),
            patch.object(
                module.story_infinite,
                "run",
                side_effect=lambda: order.append("infinite") or True,
            ),
        ):
            self.assertTrue(module.run())
        self.assertEqual(order, ["base", "dlc", "infinite"])

    def test_main_funds_power_after_stories_then_runs_only_the_selected_loop(self):
        module = importlib.import_module("main")
        for mode in ("resources", "mining", "explosive", "fast"):
            order = []

            def fund(*args):
                order.append(("power", args))
                return True

            with (
                self.subTest(mode=mode),
                patch.multiple(
                    module,
                    INFINITE_MODE=mode,
                    POWER_TARGET=10000000,
                    Items=SimpleNamespace(Power="Power"),
                    Unlocks=SimpleNamespace(
                        Megafarm="Megafarm", Polyculture="Polyculture", Trees="Trees"
                    ),
                    num_items=lambda _: 100,
                    num_unlocked=lambda skill: int(skill != "Polyculture"),
                    quick_print=Mock(),
                    create=True,
                ),
                patch.object(
                    module.story_farm,
                    "run",
                    side_effect=lambda: order.append("base") or True,
                ),
                patch.object(
                    module.story_mining,
                    "run",
                    side_effect=lambda: order.append("dlc") or True,
                ),
                patch.object(module.resource_manager, "farm", side_effect=fund),
                patch.object(
                    module.story_infinite,
                    "run",
                    side_effect=lambda: order.append("resources") or True,
                ) as resources,
                patch.object(
                    module.story_mining_infinite,
                    "run",
                    side_effect=lambda: order.append("mining") or True,
                ) as mining,
                patch.object(
                    module.story_mining_infinite_explosive,
                    "run",
                    side_effect=lambda: order.append("explosive") or True,
                ) as explosive,
                patch.object(
                    module.story_mining_infinite_fast,
                    "run",
                    side_effect=lambda: order.append("fast") or True,
                ) as fast,
            ):
                self.assertTrue(module.run())
            self.assertEqual(
                order,
                [
                    "base",
                    "dlc",
                    ("power", ("Power", 10000000, True, False, True)),
                    mode,
                ],
            )
            self.assertEqual(resources.call_count, int(mode == "resources"))
            self.assertEqual(mining.call_count, int(mode == "mining"))
            self.assertEqual(explosive.call_count, int(mode == "explosive"))
            self.assertEqual(fast.call_count, int(mode == "fast"))

    def test_main_does_not_enter_infinite_if_power_cannot_be_funded(self):
        module = importlib.import_module("main")
        with (
            patch.multiple(
                module,
                INFINITE_MODE="mining",
                POWER_TARGET=10000000,
                Items=SimpleNamespace(Power="Power"),
                Unlocks=SimpleNamespace(
                    Megafarm="Megafarm", Polyculture="Polyculture", Trees="Trees"
                ),
                num_items=lambda _: 0,
                num_unlocked=lambda _: 1,
                quick_print=Mock(),
                create=True,
            ),
            patch.object(module.story_farm, "run", return_value=True),
            patch.object(module.story_mining, "run", return_value=True),
            patch.object(module.resource_manager, "farm", return_value=False),
            patch.object(module.story_infinite, "run") as resources,
            patch.object(module.story_mining_infinite, "run") as mining,
        ):
            self.assertFalse(module.run())
        resources.assert_not_called()
        mining.assert_not_called()

    def test_main_skips_power_production_when_stock_already_suffices(self):
        module = importlib.import_module("main")
        with (
            patch.multiple(
                module,
                INFINITE_MODE="mining",
                POWER_TARGET=10000000,
                Items=SimpleNamespace(Power="Power"),
                num_items=lambda _: 10000000,
                create=True,
            ),
            patch.object(module.story_farm, "run", return_value=True),
            patch.object(module.story_mining, "run", return_value=True),
            patch.object(module.resource_manager, "farm") as fund,
            patch.object(module.story_mining_infinite, "run", return_value=False),
        ):
            self.assertFalse(module.run())
        fund.assert_not_called()

    def test_main_rejects_invalid_config_before_starting_a_story(self):
        module = importlib.import_module("main")
        for mode, target in (("unknown", 10000000), ("mining", -1)):
            with (
                self.subTest(mode=mode, target=target),
                patch.multiple(
                    module,
                    INFINITE_MODE=mode,
                    POWER_TARGET=target,
                    quick_print=Mock(),
                    create=True,
                ),
                patch.object(module.story_farm, "run") as story,
            ):
                self.assertFalse(module.run())
            story.assert_not_called()

    def test_failed_story_prevents_later_scenarios(self):
        module = importlib.import_module("main")
        for base_ok, dlc_ok in [(False, True), (True, False)]:
            with (
                self.subTest(base=base_ok, dlc=dlc_ok),
                patch.object(module.story_farm, "run", return_value=base_ok),
                patch.object(module.story_mining, "run", return_value=dlc_ok) as dlc,
                patch.object(module.story_infinite, "run") as infinite,
            ):
                self.assertFalse(module.run())
                self.assertEqual(dlc.call_count, int(base_ok))
                infinite.assert_not_called()

    def test_underground_reset_explicitly_runs_base_then_dlc_stop_mode(self):
        module = importlib.import_module("leaderboard_fastest_underground_reset")
        order = []
        with (
            patch.object(
                module.leaderboard_fastest_reset,
                "run",
                side_effect=lambda: order.append("base") or True,
            ),
            patch.object(
                module.story_mining,
                "run",
                side_effect=lambda stop: order.append(stop) or True,
            ),
        ):
            self.assertTrue(module.run())
        self.assertEqual(order, ["base", True])

    def test_manager_dispatches_base_modes_to_the_merged_resource(self):
        manager = importlib.import_module("resource_manager")
        items = SimpleNamespace(
            **{
                n: n
                for n in "Block Coal Rice Bamboo Iron Quartz Mushroom Dynamite Hay Wood Carrot Pumpkin Weird_Substance Cactus Bone Gold Power".split()
            }
        )
        entities = SimpleNamespace(Grass="Grass", Tree="Tree", Carrot="Carrot")
        cases = [
            ("Hay", False, False, "farm_hay", "farm_single", (10,)),
            ("Hay", True, False, "farm_hay", "farm_multi", (10,)),
            ("Wood", False, False, "farm_wood", "farm_single", (10, True)),
            ("Wood", True, False, "farm_wood", "farm_multi", (10,)),
            ("Carrot", False, False, "farm_carrot", "farm_single", (10,)),
            ("Carrot", True, False, "farm_carrot", "farm_multi", (10,)),
            ("Hay", False, True, "farm_polyculture", "produce_single", ("Grass", 10)),
            ("Wood", True, True, "farm_polyculture", "produce_multi", ("Tree", 10)),
            ("Carrot", True, True, "farm_polyculture", "produce_multi", ("Carrot", 10)),
            ("Pumpkin", False, False, "farm_pumpkin", "produce_single", (10,)),
            ("Pumpkin", True, False, "farm_pumpkin", "produce_multi", (10,)),
            (
                "Weird_Substance",
                False,
                False,
                "farm_pumpkin",
                "produce_goo_single",
                (10,),
            ),
            (
                "Weird_Substance",
                True,
                False,
                "farm_pumpkin",
                "produce_goo_multi",
                (10,),
            ),
            ("Cactus", False, False, "farm_cactus", "produce_single", (10,)),
            ("Cactus", True, False, "farm_cactus", "produce_multi", (10,)),
            ("Bone", False, False, "farm_bone", "produce_single", (10,)),
            ("Gold", False, False, "farm_gold", "produce_single", (10,)),
            ("Gold", True, False, "farm_gold", "produce_multi", (10,)),
            ("Power", False, False, "farm_power", "produce_single", (10,)),
            ("Power", True, False, "farm_power", "produce_multi", (10,)),
        ]
        for item, multi, poly, producer, function, args in cases:
            stock = [0]

            def produce(*_):
                stock[0] = 10
                return True

            with (
                self.subTest(item=item, multi=multi, poly=poly),
                patch.multiple(
                    manager,
                    Items=items,
                    Entities=entities,
                    num_items=lambda _: stock[0],
                    create=True,
                ),
                patch.object(
                    importlib.import_module(producer), function, side_effect=produce
                ) as called,
                patch.object(
                    importlib.import_module(producer),
                    "requirements",
                    return_value={},
                ),
                patch.object(
                    importlib.import_module("farm_pumpkin"),
                    "goo_requirements",
                    return_value={},
                ),
                patch("builtins.__import__", wraps=__import__) as imports,
            ):
                self.assertTrue(manager.farm(item, 10, multi, poly, True))
                called.assert_called_once_with(*args)
                self.assertEqual(
                    [
                        call.args[0]
                        for call in imports.call_args_list
                        if call.args[0] in PAIRED + SINGLE_ONLY
                    ],
                    [producer],
                )

    def test_wood_worker_receives_a_copied_target_and_is_joined(self):
        module = importlib.import_module("farm_wood")
        stock = [0]
        callback = []

        def spawn(worker, *args):
            callback.append((worker, args))
            worker(*args)
            return "owned"

        def harvest():
            stock[0] = 5
            return True

        with (
            patch.multiple(
                module,
                Items=SimpleNamespace(Wood="Wood"),
                Unlocks=SimpleNamespace(
                    Trees="Trees", Timing="Timing", Megafarm="Megafarm", Plant="Plant"
                ),
                num_unlocked=lambda _: 1,
                Entities=SimpleNamespace(Tree="Tree", Bush="Bush"),
                North="N",
                East="E",
                get_world_size=lambda: 1,
                get_pos_x=lambda: 0,
                get_pos_y=lambda: 0,
                get_entity_type=lambda: "Grass",
                num_items=lambda _: stock[0],
                can_harvest=lambda: True,
                harvest=harvest,
                plant=Mock(return_value=True),
                move=Mock(return_value=True),
                get_time=lambda: 0,
                spawn_drone=spawn,
                create=True,
            ),
            patch.object(module.utils_farm, "water"),
            patch.object(module.utils_farm, "can_start_phase", return_value=True),
            patch.object(module.utils_move, "go_to", return_value=True),
            patch.object(
                module.utils_farm, "wait_for", return_value=True, create=True
            ) as waiter,
        ):
            self.assertTrue(module.farm_multi(5))
        self.assertEqual(stock[0], 5)
        self.assertEqual(
            [(f.__name__, args) for f, args in callback], [("_worker", (1, 5, True))]
        )
        waiter.assert_called_once_with("owned")


if __name__ == "__main__":
    unittest.main()
