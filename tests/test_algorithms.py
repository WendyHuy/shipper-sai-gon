import random
import unittest
from math import inf

from ai.astar import astar
from ai.bfs_dfs import bfs
from ai.common import path_cost, validate_path
from ai.dstar_lite import DStarLite
from ai.greedy import greedy


class AlgorithmTests(unittest.TestCase):
    def test_weighted_detour_and_validation(self):
        costs = {(1, 1): 8, (1, 2): 8}
        result = astar(3, 4, costs, (1, 0), (1, 3))
        self.assertEqual(result.cost, 5)
        self.assertTrue(validate_path(result.path, costs, (1, 0), (1, 3), 3, 4))
        self.assertGreater(bfs(3, 4, costs, (1, 0), (1, 3)).cost, result.cost)
        self.assertFalse(validate_path([(1, 0), (1, 3)], costs, (1, 0), (1, 3), 3, 4))

    def test_unreachable_and_blocked_endpoints(self):
        costs = {(1, c): inf for c in range(3)}
        for fn in (astar, bfs, greedy):
            self.assertIsNone(fn(3, 3, costs, (0, 0), (2, 2)).path)
        for blocked in ((0, 0), (2, 2)):
            planner = DStarLite(3, 3, {blocked: inf}, (0, 0), (2, 2))
            self.assertIsNone(planner.plan().path)
            planner.on_changes([(blocked, 1)])
            self.assertEqual(planner.plan().cost, 4)

    def test_start_equals_goal(self):
        for fn in (astar, bfs, greedy):
            self.assertEqual(fn(3, 3, {}, (0, 0), (0, 0)).path, [(0, 0)])
        self.assertEqual(DStarLite(3, 3, {}, (0, 0), (0, 0)).plan().cost, 0)

    def test_dstar_random_updates_moving_start_vs_dijkstra(self):
        for seed in range(20):
            rng = random.Random(seed)
            rows, cols = 9, 9
            start, goal = (0, 0), (8, 8)
            costs = {}
            planner = DStarLite(rows, cols, costs, start, goal)
            for tick in range(50):
                changes = []
                for _ in range(5):
                    cell = rng.randrange(rows), rng.randrange(cols)
                    if cell not in (start, goal):
                        cost = rng.choice((1, 1, 3, 8, inf))
                        costs[cell] = cost
                        changes.append((cell, cost))
                planner.on_changes(changes)
                incremental = planner.plan()
                oracle = astar(rows, cols, costs, start, goal, weight=0)
                self.assertEqual(incremental.cost, oracle.cost, (seed, tick, start))
                if incremental.path:
                    self.assertTrue(validate_path(incremental.path, costs, start, goal, rows, cols))
                    self.assertEqual(path_cost(incremental.path, costs), oracle.cost)
                    if len(incremental.path) > 1 and tick % 2 == 0:
                        start = incremental.path[1]
                        planner.move_start(start)
                self.assertLess(len(planner.heap), 4 * len(planner.active) + 129)


if __name__ == '__main__':
    unittest.main()
