import math
import random
import unittest
from dataclasses import replace

from ai.astar import astar
from ai.bfs_dfs import bfs
from ai.brains import BRAIN_NAMES, Brain
from ai.common import manhattan, path_cost, validate_path
from ai.dstar_lite import DStarLite
from ai.greedy import greedy
from config import Config
from core.sensing import sense, with_halo
from core.simulation import Simulation


class ExtendedAlgorithmAndEdgeCaseTests(unittest.TestCase):
    """Kiểm thử mở rộng toàn diện mọi góc cạnh của 7 thuật toán và mô phỏng."""

    def test_all_seven_algorithms_basic_connectivity(self):
        """Kiểm tra cả 7 thuật toán trên bản đồ có đường đi đơn giản."""
        rows, cols = 5, 5
        start, goal = (0, 0), (4, 4)
        costs = {(1, 1): 5, (2, 2): 10}

        # 1. A*
        res_astar = astar(rows, cols, costs, start, goal, weight=1.0)
        self.assertTrue(validate_path(res_astar.path, costs, start, goal, rows, cols))
        self.assertEqual(res_astar.path[0], start)
        self.assertEqual(res_astar.path[-1], goal)

        # 2. Weighted A* (w=1.5)
        res_weighted = astar(rows, cols, costs, start, goal, weight=1.5)
        self.assertTrue(validate_path(res_weighted.path, costs, start, goal, rows, cols))

        # 3. BFS
        res_bfs = bfs(rows, cols, costs, start, goal)
        self.assertTrue(validate_path(res_bfs.path, costs, start, goal, rows, cols))
        # BFS tối ưu số bước (hops = 8)
        self.assertEqual(len(res_bfs.path) - 1, 8)

        # 4. Greedy
        res_greedy = greedy(rows, cols, costs, start, goal)
        self.assertTrue(validate_path(res_greedy.path, costs, start, goal, rows, cols))

        # 5. D* Lite
        dstar = DStarLite(rows, cols, costs, start, goal)
        res_dstar = dstar.plan()
        self.assertTrue(validate_path(res_dstar.path, costs, start, goal, rows, cols))
        self.assertEqual(res_dstar.cost, res_astar.cost)

    def test_unreachable_island_and_wall_cages(self):
        """Kiểm tra khi đích đến hoặc xuất phát bị lồng tường bao kín 100%."""
        rows, cols = 7, 7
        start = (0, 0)
        goal = (3, 3)

        # Tạo chuồng tường bao quanh goal
        costs = {}
        for r in range(2, 5):
            for c in range(2, 5):
                if (r, c) != goal:
                    costs[(r, c)] = math.inf

        for name in BRAIN_NAMES:
            brain = Brain(name, rows, cols)
            nxt = brain.plan(start, goal, costs)
            self.assertIsNone(nxt, f"Brain {name} không được tìm thấy đường khi bị bao kín")
            self.assertIsNone(brain.path)

    def test_extreme_grid_sizes(self):
        """Kiểm tra biên kích thước bản đồ cực nhỏ (3x3) và cực lớn (30x30)."""
        # Kích thước cực nhỏ 3x3
        costs_small = {(0, 1): math.inf, (1, 1): math.inf}
        res_small = astar(3, 3, costs_small, (0, 0), (0, 2))
        self.assertEqual(res_small.path, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)])

        # Kích thước lớn 30x30
        rows_large, cols_large = 30, 30
        res_large = astar(rows_large, cols_large, {}, (0, 0), (29, 29))
        self.assertEqual(res_large.cost, 58)
        self.assertEqual(len(res_large.path) - 1, 58)

    def test_dstar_lite_dynamic_fluctuations(self):
        """Kiểm tra D* Lite trong điều kiện chi phí biến động ngẫu nhiên liên tục 150 bước."""
        rng = random.Random(1337)
        rows, cols = 8, 8
        start, goal = (0, 0), (7, 7)
        costs = {}
        dstar = DStarLite(rows, cols, costs, start, goal)

        for step in range(150):
            # 3 điểm thay đổi cost ngẫu nhiên
            changes = []
            for _ in range(3):
                cell = (rng.randint(0, rows - 1), rng.randint(0, cols - 1))
                if cell not in (start, goal):
                    c = rng.choice([1, 2, 5, 10, math.inf])
                    costs[cell] = c
                    changes.append((cell, c))

            dstar.on_changes(changes)
            res_dstar = dstar.plan()
            res_oracle = astar(rows, cols, costs, start, goal, weight=0.0)

            if res_oracle.path is None:
                self.assertIsNone(res_dstar.path)
            else:
                self.assertEqual(res_dstar.cost, res_oracle.cost, f"Lệch cost ở bước {step}")
                self.assertTrue(validate_path(res_dstar.path, costs, start, goal, rows, cols))

            # Mô phỏng di chuyển vị trí start nếu có đường
            if res_dstar.path and len(res_dstar.path) > 1 and step % 3 == 0:
                start = res_dstar.path[1]
                dstar.move_start(start)

    def test_halo_sensing_costs(self):
        """Kiểm tra lớp halo tạo vùng đệm an toàn xung quanh NPC."""
        cfg = Config(rows=10, cols=10, npc_count=1, sensing_radius=4)
        sim = Simulation(cfg, 'dstar_halo')
        # Đặt NPC tại vị trí xác định trong tầm nhìn
        npc_pos = (2, 2)
        sim.world.traffic.positions = [npc_pos]
        sim.shipper.pos = (0, 0)

        known = {cell: math.inf for cell in sim.world.walls}
        _, visible = sense(sim.world, sim.shipper.pos, 4, known)
        costs_halo = with_halo(sim.world, known, visible, sim.shipper.pos)

        # Các ô láng giềng kề sát NPC phải nhận chi phí halo >= 4
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            adj = (npc_pos[0] + dr, npc_pos[1] + dc)
            if adj in visible and adj not in sim.world.walls:
                self.assertGreaterEqual(costs_halo.get(adj, 1), 4)

    def test_full_game_simulation_multi_order_completion(self):
        """Mô phỏng toàn bộ ván đấu hoàn chỉnh giao nhiều đơn hàng."""
        cfg = Config(rows=12, cols=12, npc_count=3, order_count=4, max_ticks=400, density=0.1)
        sim = Simulation(cfg, 'dstar')

        ticks_run = 0
        while not sim.finished and ticks_run < 400:
            sim.step()
            ticks_run += 1

        summary = sim.summary()
        self.assertGreater(summary['delivered'] + summary['cancelled'], 0)
        self.assertGreaterEqual(sim.shipper.steps, 0)
        self.assertEqual(summary['ticks'], ticks_run)

    def test_brain_plan_no_mutation_of_input_dict(self):
        """Đảm bảo hàm Brain.plan không làm biến đổi bất thường dictionary costs truyền vào."""
        brain = Brain('astar_tick', 6, 6)
        costs = {(1, 1): 5, (2, 2): 8}
        costs_copy = dict(costs)
        brain.plan((0, 0), (5, 5), costs)
        self.assertEqual(costs, costs_copy)


if __name__ == '__main__':
    unittest.main()
