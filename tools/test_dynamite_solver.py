"""Incremental inference equivalence and ownership, not native tick measurements."""

import importlib
import random
import unittest
from unittest.mock import patch

from test_mining_multi import DynamiteField

solver = importlib.import_module("mine_dynamite")


class DynamiteSolverTests(unittest.TestCase):
    def test_topology_is_bounded_and_matches_the_reference(self):
        for ws in (3, 8, 32):
            with self.subTest(ws=ws):
                table = solver._new_solver(ws)[0]
                self.assertEqual(table, {"size": ws})
                for pos in range(ws * ws):
                    x, y = pos % ws, pos // ws
                    expected = [
                        x + dx + (y + dy) * ws
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        if (dx or dy) and 0 <= x + dx < ws and 0 <= y + dy < ws
                    ]
                    self.assertEqual(solver._cached_neighbors(table, pos), expected)
                    self.assertNotIn(pos, table[pos])

    def test_topology_has_no_warmup_and_each_cell_is_computed_once(self):
        with patch.object(
            solver, "_neighbors_single", wraps=solver._neighbors_single
        ) as build:
            cache = solver._new_solver(32)[0]
            build.assert_not_called()
            self.assertIs(
                solver._cached_neighbors(cache, 0), solver._cached_neighbors(cache, 0)
            )
            build.assert_called_once_with(0, 32)

    def test_incremental_matches_reference_on_complete_solver_traces(self):
        counts = dict(rounds=0, subsets=0, guesses=0)
        for seed in range(100):
            rng = random.Random(seed)
            ws = 6 if seed % 2 else 8
            mines = {p for p in range(1, ws * ws) if rng.random() < 0.18}
            table = [solver._neighbors_single(p, ws) for p in range(ws * ws)]
            state = solver._new_solver(ws)
            clues = {0: sum(p in mines for p in table[0])}
            flags = set()
            changed = [0]
            for _ in range(ws * ws * 4):
                old = solver._deduce_single(clues, flags, ws)
                new = solver._deduce_incremental(clues, flags, state, changed)
                self.assertIsNotNone(old)
                self.assertIsNotNone(new)
                safe, marked, constraints = old
                self.assertEqual(set(new[0]), safe, (seed, len(clues), "safe"))
                self.assertEqual(set(new[1]), marked, (seed, len(clues), "mines"))
                self.assertFalse(safe & mines)
                self.assertTrue(marked <= mines)
                counts["rounds"] += 1
                if not safe and any(
                    len(c) < len(d) and c <= d
                    for c, _ in constraints
                    for d, _ in constraints
                ):
                    counts["subsets"] += 1
                changed = []
                for pos in marked:
                    if pos not in flags:
                        flags.add(pos)
                        changed.append(pos)
                if not safe and changed:
                    continue
                cells = set(safe)
                if not cells:
                    # Constraint cache must supply the same risks when a guess is needed.
                    def normalized(cs):
                        return {(frozenset(c), n) for c, n in cs}

                    self.assertEqual(normalized(new[2]), normalized(constraints))
                    choice = solver._guess_single(clues, flags, constraints, ws)
                    counts["guesses"] += 1
                    if choice is None or choice in mines:
                        break
                    cells.add(choice)
                for pos in cells:
                    clues[pos] = sum(p in mines for p in table[pos])
                    changed.append(pos)
                if len(clues) + len(mines) == ws * ws:
                    break
            else:
                self.fail("Inference did not terminate")
        self.assertGreater(counts["rounds"], 500)
        self.assertGreater(counts["subsets"], 0)
        self.assertGreater(counts["guesses"], 0)

    def test_unchanged_snapshot_reuses_facts_without_rebuilding_constraints(self):
        state = solver._new_solver(3)
        with patch.object(
            solver, "_update_constraint", wraps=solver._update_constraint
        ) as update:
            first = solver._deduce_incremental({0: 1, 1: 1}, set(), state, [0, 1])
            self.assertEqual(first[0], {2, 5})
            calls = update.call_count
            again = solver._deduce_incremental({0: 1, 1: 1}, set(), state, [])
            self.assertEqual(again[0], {2, 5})
            self.assertEqual(update.call_count, calls)

    def test_revealing_one_cell_updates_at_most_nine_constraints(self):
        ws = 16
        state = solver._new_solver(ws)
        table = [solver._neighbors_single(p, ws) for p in range(ws * ws)]
        # Valid one-mine clues, with no forced zero expansion in this setup.
        mines = {p for p in range(ws * ws) if p % 7 == 0}
        opened = [p for p in range(150) if p not in mines]
        clues = {p: sum(n in mines for n in table[p]) for p in opened}
        solver._deduce_incremental(clues, set(), state, opened)
        pos = next(p for p in range(150, ws * ws) if p not in mines)
        clues[pos] = sum(n in mines for n in table[pos])
        with patch.object(
            solver, "_update_constraint", wraps=solver._update_constraint
        ) as update:
            self.assertIsNotNone(solver._deduce_incremental(clues, set(), state, [pos]))
        self.assertLessEqual(update.call_count, 9)
        self.assertLess(update.call_count, len(clues) // 10)

    def test_contradictions_are_rejected(self):
        for clues, flags in (({0: 4}, set()), ({0: 0}, {1}), ({0: 1, 1: 4}, set())):
            with self.subTest(clues=clues, flags=flags):
                old = solver._deduce_single(clues, flags, 3)
                state = solver._new_solver(3)
                result = solver._deduce_incremental(
                    clues, flags, state, list(clues) + list(flags)
                )
                self.assertEqual(result is None, old is None)

    def test_subset_comparisons_use_local_overlaps_instead_of_all_pairs(self):
        ws = 32
        state = solver._new_solver(ws)
        table = [solver._neighbors_single(p, ws) for p in range(ws * ws)]
        mines = {x + y * ws for x in range(ws) for y in range(ws) if (x + y) % 2}
        clues = {
            x + y * ws: sum(n in mines for n in table[x + y * ws])
            for x in range(0, ws, 2)
            for y in range(0, ws, 2)
        }
        reference = solver._deduce_single(clues, set(), ws)
        with patch.object(
            solver, "_subset_facts", wraps=solver._subset_facts
        ) as compare:
            result = solver._deduce_incremental(clues, set(), state, list(clues))
        self.assertEqual(result[0], reference[0])
        self.assertEqual(result[1], reference[1])
        self.assertFalse(result[0])
        self.assertLess(compare.call_count, len(reference[2]) ** 2 // 4)

    def test_parent_inference_and_isolated_guesses_are_used_in_both_modes(self):
        for parallel in (False, True):
            field = DynamiteField(ws=4, capacity=4, mines=((1, 1),))
            infer = solver._deduce_incremental
            guess = solver._guess_single

            def parent_only(*args):
                self.assertFalse(field.in_worker)
                self.assertFalse(field.pending)
                return infer(*args)

            def alone(*args):
                self.assertFalse(field.in_worker)
                self.assertFalse(field.pending)
                return guess(*args)

            with (
                field.api(solver, measure=field.measure),
                patch.object(
                    solver, "_deduce_incremental", side_effect=parent_only
                ) as deductions,
                patch.object(solver, "_guess_single", side_effect=alone),
            ):
                result = (
                    solver.produce_multi(1000)
                    if parallel
                    else solver.produce_single(1000)
                )
            self.assertTrue(result)
            self.assertTrue(field.solved)
            self.assertGreater(deductions.call_count, 0)
            self.assertEqual(field.spawned, field.joined)


if __name__ == "__main__":
    unittest.main()
