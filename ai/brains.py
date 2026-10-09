from ai.astar import astar
from ai.bfs_dfs import bfs
from ai.common import SearchResult, path_cost
from ai.dstar_lite import DStarLite
from ai.greedy import greedy


BRAIN_NAMES = ('astar_tick', 'astar_needed', 'dstar', 'dstar_halo', 'bfs', 'greedy', 'weighted')
LABELS = {'astar_tick': 'A* mỗi tick (S1)', 'astar_needed': 'A* khi cần (S2)',
          'dstar': 'D* Lite (S3)', 'dstar_halo': 'D* Lite + halo (S4)',
          'bfs': 'BFS', 'greedy': 'Greedy Manhattan', 'weighted': 'Weighted A* (w=1.5)'}


class Brain:
    def __init__(self, name, rows, cols):
        if name not in BRAIN_NAMES:
            raise ValueError(f'Brain không hợp lệ: {name}')
        self.name, self.rows, self.cols = name, rows, cols
        self.goal = None
        self.path = None
        self.planner = None
        self.costs = {}
        self.last_result = SearchResult(None)
        self.replanned = False

    def plan(self, pos, goal, costs):
        reset = goal != self.goal
        changes = [(cell, costs.get(cell, 1)) for cell in sorted(set(costs) | set(self.costs))
                   if costs.get(cell, 1) != self.costs.get(cell, 1)]
        old_path = self.path
        if reset:
            self.goal = goal
            self.path = None
        self.replanned = False
        if self.name.startswith('dstar'):
            if reset or self.planner is None:
                self.planner = DStarLite(self.rows, self.cols, costs, pos, goal)
            else:
                self.planner.move_start(pos)
                self.planner.on_changes(changes)
            self.last_result = self.planner.plan()
            self.replanned = reset or bool(changes) or self.last_result.processed > 0
        else:
            changed_path = bool(changes and self.path and
                                set(cell for cell, _ in changes).intersection(self.path))
            should_plan = self.name != 'astar_needed' or reset or not self.path or changed_path
            if should_plan:
                if self.name == 'bfs':
                    self.last_result = bfs(self.rows, self.cols, costs, pos, goal)
                elif self.name == 'greedy':
                    self.last_result = greedy(self.rows, self.cols, costs, pos, goal)
                else:
                    self.last_result = astar(self.rows, self.cols, costs, pos, goal,
                                             1.5 if self.name == 'weighted' else 1.0)
                self.replanned = True
            else:
                self.last_result = SearchResult(self.path, path_cost(self.path, costs))
        self.costs = dict(costs)
        self.path = self.last_result.path
        if old_path and old_path[0] != pos and pos in old_path:
            old_path = old_path[old_path.index(pos):]
        self.path_changed = bool(not reset and old_path and self.path and old_path != self.path)
        return self.path[1] if self.path and len(self.path) > 1 else None

    def on_move(self, pos):
        if self.planner:
            self.planner.move_start(pos)
        if self.path and len(self.path) > 1 and self.path[1] == pos:
            self.path = self.path[1:]
