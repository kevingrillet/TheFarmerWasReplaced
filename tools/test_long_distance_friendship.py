"""Transport/stratum fixtures, not a native cave-in or achievement validation."""

import importlib
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from test_producer_contract import Symbols

achievements = importlib.import_module("ZZAchievementDLC")


class MushroomWells:
    """Two distant columns joined by wrapping pushes, with native landing rules."""

    def __init__(self, second=40):
        self.x = self.y = 0
        self.depths = {0: 2, 7: 0}
        self.carried = {(0, 2): (2, "first")}
        self.second = second
        self.stock = self.digs = 0
        self.transfers, self.matches, self.lost = [], [], []
        self.refuse_push = False
        self.stall = False

    def mushroom(self, x, depth):
        if (x, depth) in self.carried:
            return self.carried[x, depth]
        if 2 <= depth <= 5:
            return (x + depth) % 6, "first"
        if self.second is not None and self.second <= depth < self.second + 4:
            return (x + depth) % 6, "second"
        return None

    def go_to(self, x, y):
        self.x, self.y = x, y
        return True

    def z(self):
        return -self.depths[self.x]

    def ground(self):
        return "Mushroom" if self.mushroom(self.x, self.depths[self.x]) else "Rock"

    def measure(self):
        return self.mushroom(self.x, self.depths[self.x])[0]

    def dig(self):
        self.digs += 1
        if self.stall:
            return
        self.carried.pop((self.x, self.depths[self.x]), None)
        self.depths[self.x] += 1
        # Simplified non-wrapping slope: demonstrates why a fixed shallow source
        # can be lost. This is deliberately not a full engine physics model.
        for pos in list(self.carried):
            if self.depths[self.x] - pos[1] > abs(self.x - pos[0]) + 1:
                self.lost.append(pos)
                self.carried.pop(pos)
                self.depths[pos[0]] = self.depths[self.x]

    def can_push(self, direction):
        target = 7 if direction == "West" else 0
        return (
            not self.refuse_push
            and self.ground() == "Mushroom"
            and self.depths[target] > self.depths[self.x]
        )

    def push(self, direction):
        if not self.can_push(direction):
            return False
        source, source_depth = self.x, self.depths[self.x]
        target = 7 if direction == "West" else 0
        target_depth = self.depths[target]
        block = self.mushroom(source, source_depth)
        under = self.mushroom(target, target_depth)
        self.transfers.append((source_depth, target_depth))
        self.carried.pop((source, source_depth), None)
        self.depths[source] += 1
        if under and under[0] == block[0]:
            self.matches.append((block[1], under[1]))
            self.stock += 1
            self.depths[target] += 1
        else:
            self.depths[target] -= 1
            self.carried[target, target_depth - 1] = block
        return True

    @contextmanager
    def api(self):
        with (
            patch.multiple(
                achievements,
                Grounds=Symbols(),
                Unlocks=Symbols(),
                Items=Symbols(),
                West="West",
                East="East",
                get_world_size=lambda: 8,
                get_pos_z=self.z,
                get_ground_type=self.ground,
                measure=self.measure,
                dig=self.dig,
                can_push=self.can_push,
                push=self.push,
                num_items=lambda _: self.stock,
                quick_print=lambda *args: None,
                create=True,
            ),
            patch.object(achievements, "_prepare", return_value=True),
            patch.object(achievements, "_seek", return_value=True),
            patch.object(achievements.utils_mine, "go_to", side_effect=self.go_to),
        ):
            yield


class LongDistanceFriendshipTests(unittest.TestCase):
    def test_carries_the_original_block_through_a_long_gap_to_another_colony(self):
        field = MushroomWells()
        with field.api():
            self.assertTrue(achievements.long_distance_friendship(200))
        self.assertEqual(field.matches, [("first", "second")])
        self.assertGreater(len(field.transfers), 10)
        self.assertEqual(field.lost, [])
        self.assertTrue(
            all(1 <= target - source <= 3 for source, target in field.transfers)
        )

    def test_fixed_source_can_be_lost_before_the_next_colony(self):
        field = MushroomWells()
        field.go_to(7, 0)
        for _ in range(40):
            field.dig()
        self.assertEqual(field.lost, [(0, 2)])

    def test_matching_within_first_colony_does_not_consume_the_source(self):
        field = MushroomWells()
        field.carried[7, 4] = (2, "first")
        with field.api():
            self.assertTrue(achievements.long_distance_friendship(200))
        self.assertEqual(field.matches, [("first", "second")])
        self.assertIn((2, 5), field.transfers)

    def test_no_lower_colony_is_a_bounded_failure(self):
        field = MushroomWells(second=None)
        with field.api():
            self.assertFalse(achievements.long_distance_friendship(50))
        self.assertLessEqual(field.digs, 50)
        self.assertEqual(field.stock, 0)

    def test_failed_dig_or_push_stops_without_looping(self):
        for option in ("stall", "refuse_push"):
            field = MushroomWells()
            setattr(field, option, True)
            with self.subTest(option=option), field.api():
                self.assertFalse(achievements.long_distance_friendship())
            self.assertLessEqual(field.digs, 4)

    def test_small_world_or_empty_budget_fails_before_preparation(self):
        field = MushroomWells()
        with field.api(), patch.object(achievements, "_prepare") as prepare:
            self.assertFalse(achievements.long_distance_friendship(0))
            with patch.object(achievements, "get_world_size", return_value=3):
                self.assertFalse(achievements.long_distance_friendship())
            prepare.assert_not_called()


if __name__ == "__main__":
    unittest.main()
