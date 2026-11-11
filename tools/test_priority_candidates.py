"""Algorithm contracts for the priority candidates; no native growth or timing."""

import ast
import unittest
from pathlib import Path

from test_multi_leaderboards import Field, load
from test_producer_contract import Symbols

SAVE = Path(__file__).resolve().parents[1] / "Save0"
POLY = {
    "leaderboard_carrot_polyculture": ("Carrot", 2000000000),
    "leaderboard_carrot_single_polyculture": ("Carrot", 100000000),
    "leaderboard_wood_polyculture": ("Wood", 10000000000),
    "leaderboard_wood_single_polyculture": ("Wood", 500000000),
}
OTHER = {
    "leaderboard_pumpkin_single_pipeline": 10000000,
    "leaderboard_power_global": 100000,
}


class CompanionField(Field):
    def __init__(self, resource, invalid=False, **kwargs):
        super().__init__(**kwargs)
        self.resource = resource
        self.main = "Carrot" if resource == "Carrot" else "Tree"
        self.invalid = invalid
        self.selections = {}
        self.seeds = 10000
        self.boosted = 0

    def plant(self, entity):
        if entity == self.main:
            if self.seeds == 0:
                return False
            self.seeds -= 1
            self.selections[self.pos()] = self.selections.get(self.pos(), 0) + 1
        return super().plant(entity)

    def companion(self):
        x, y = self.pos()
        if self.invalid or self.selections[self.pos()] % 2:
            return "Grass", ((x + 1) % self.ws, y)
        return "Bush", ((x + 1) % self.ws, y)

    def harvest(self):
        if self.entity() != self.main:
            return super().harvest()
        kind, target = self.companion()
        gain = 0
        if kind == "Bush" and self.entities.get(target) == "Bush":
            gain = 10
            self.boosted += 1
        self.stock[self.resource] = self.stock.get(self.resource, 0) + gain
        self.harvests.append((self.pos(), self.main, gain))
        self.entities.pop(self.pos(), None)
        return True


class PowerField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bonus_harvests = 0

    def harvest(self):
        if self.entity() == "Sunflower":
            if any(f.__name__ == "_plant_column" for f, _, _ in self.pending.values()):
                raise AssertionError("harvesting before planting workers joined")
            petals = [
                self.values[p]
                for p, entity in self.entities.items()
                if entity == "Sunflower"
            ]
            if len(petals) >= 10:
                if self.values[self.pos()] != max(petals):
                    raise AssertionError(
                        "local petal maximum instead of global maximum"
                    )
                self.bonus_harvests += 1
        return super().harvest()


class PriorityCandidateTests(unittest.TestCase):
    def test_candidates_are_standalone_and_keep_official_targets(self):
        targets = {name: row[1] for name, row in POLY.items()}
        targets.update(OTHER)
        for name, target in targets.items():
            with self.subTest(name=name):
                tree = ast.parse((SAVE / (name + ".py")).read_text())
                self.assertFalse(
                    any(
                        isinstance(n, (ast.Import, ast.ImportFrom))
                        for n in ast.walk(tree)
                    )
                )
                self.assertEqual(load(name).TARGET, target)

    def test_polyculture_rejects_requests_and_keeps_companions_owned(self):
        for name, (resource, _) in POLY.items():
            for capacity in (1, 2, 4):
                with self.subTest(name=name, capacity=capacity):
                    module = load(name)
                    field = CompanionField(resource, ws=8, capacity=capacity)
                    with field.api(
                        module, Unlocks=Symbols(), get_companion=field.companion
                    ):
                        self.assertTrue(module.run(50))
                    self.assertGreaterEqual(field.stock[resource], 50)
                    self.assertGreater(field.boosted, 0)
                    self.assertEqual(field.spawned, field.joined)
                    self.assertFalse(field.pending)
                    roots = [p for p, entity in field.plants if entity == field.main]
                    if resource == "Wood":
                        self.assertTrue(all(y % 2 == 0 for x, y in roots))

    def test_polyculture_bad_requests_seed_exhaustion_and_locks_fail_finitely(self):
        for name, (resource, _) in POLY.items():
            for failure in ("requests", "seeds", "locked"):
                with self.subTest(name=name, failure=failure):
                    module = load(name)
                    field = CompanionField(
                        resource, ws=8, capacity=4, invalid=failure == "requests"
                    )
                    if failure == "seeds":
                        field.seeds = 0
                    with field.api(
                        module,
                        Unlocks=Symbols(),
                        num_unlocked=lambda _: int(failure != "locked"),
                        get_companion=field.companion,
                    ):
                        self.assertFalse(module.run(50))
                    self.assertEqual(field.spawned, field.joined)
                    self.assertFalse(field.pending)
                    self.assertLessEqual(sum(field.selections.values()), 512)

    def test_pipeline_plants_full_field_before_waiting_and_repairs_deaths(self):
        module = load("leaderboard_pumpkin_single_pipeline")
        field = Field(ws=3, capacity=1)
        field.kill_pumpkin = True
        readiness = field.can_harvest

        def ready():
            self.assertEqual(len(field.plant_counts), 9)
            return readiness()

        with field.api(module, get_time=lambda: field.calls / 100, can_harvest=ready):
            self.assertTrue(module.run(81))
        self.assertEqual(field.stock["Pumpkin"], 81)
        self.assertTrue(all(n == 2 for n in field.plant_counts.values()))
        self.assertEqual(len([h for h in field.harvests if h[1] == "Pumpkin"]), 1)

    def test_global_petals_join_before_harvest_and_keep_nine_flowers(self):
        module = load("leaderboard_power_global")
        for capacity in (1, 2, 4, 32):
            with self.subTest(capacity=capacity):
                field = PowerField(ws=4, capacity=capacity)
                with field.api(
                    module,
                    max_drones=lambda: capacity,
                    get_time=lambda: field.calls / 100,
                ):
                    self.assertTrue(module.run(20))
                self.assertGreaterEqual(field.stock["Power"], 21)
                self.assertGreater(field.bonus_harvests, 0)
                self.assertGreaterEqual(
                    sum(e == "Sunflower" for e in field.entities.values()), 9
                )
                self.assertEqual(field.spawned, field.joined)
                self.assertFalse(field.pending)

    def test_failed_power_planting_joins_children_without_harvesting(self):
        module = load("leaderboard_power_global")
        field = PowerField(ws=4, capacity=4)
        with field.api(module, plant=lambda _: False, max_drones=lambda: 4):
            self.assertFalse(module.run(20))
        self.assertEqual(field.spawned, field.joined)
        self.assertEqual(field.stock.get("Power", 0), 0)


if __name__ == "__main__":
    unittest.main()
