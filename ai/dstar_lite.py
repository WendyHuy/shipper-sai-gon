from collections import defaultdict
from heapq import heappop, heappush
from itertools import count
from math import inf

from ai.common import SearchResult, edge_cost, manhattan, neighbors4, path_cost


class DStarLite:
    def __init__(self, rows, cols, costs, start, goal):
        self.rows, self.cols = rows, cols
        self.costs = dict(costs)
        self.start, self.last, self.goal = start, start, goal
        self.km = 0
        self.g = defaultdict(lambda: inf)
        self.rhs = defaultdict(lambda: inf)
        self.rhs[goal] = 0
        self.heap = []
        self.active = {}
        self.serial = count()
        self.processed_cells = []
        self.max_frontier = 0
        self._push(goal)

    def neighbors(self, u):
        return neighbors4(u, self.rows, self.cols)

    def key(self, u):
        m = min(self.g[u], self.rhs[u])
        return m + manhattan(self.start, u) + self.km, m

    def _push(self, u):
        key = self.key(u)
        token = next(self.serial)
        self.active[u] = (key, token)
        heappush(self.heap, (*key, token, u))
        self.max_frontier = max(self.max_frontier, len(self.active))

    def _clean(self):
        while self.heap:
            k1, k2, token, u = self.heap[0]
            if self.active.get(u) == ((k1, k2), token):
                break
            heappop(self.heap)

    def _top_key(self):
        self._clean()
        return self.heap[0][:2] if self.heap else (inf, inf)

    def update_vertex(self, u):
        if u != self.goal:
            self.rhs[u] = min((edge_cost(self.costs, u, v) + self.g[v]
                               for v in self.neighbors(u)), default=inf)
        self.active.pop(u, None)
        if self.g[u] != self.rhs[u]:
            self._push(u)

    def on_changes(self, changes):
        affected = set()
        for u, cost in changes:
            if cost < 1:
                raise ValueError('Chi phí phải >= 1.')
            if self.costs.get(u, 1) == cost:
                continue
            self.costs[u] = cost
            affected.add(u)
            affected.update(self.neighbors(u))
        for u in sorted(affected):
            self.update_vertex(u)

    def move_start(self, pos):
        self.km += manhattan(self.last, pos)
        self.start = self.last = pos

    def compute_shortest_path(self):
        self.processed_cells = []
        self.max_frontier = len(self.active)
        while self._top_key() < self.key(self.start) or self.rhs[self.start] != self.g[self.start]:
            if not self.heap:
                break
            k1, k2, token, u = heappop(self.heap)
            if self.active.get(u) != ((k1, k2), token):
                continue
            self.active.pop(u, None)
            old_key = k1, k2
            if old_key < self.key(u):
                self._push(u)
            elif self.g[u] > self.rhs[u]:
                self.processed_cells.append(u)
                self.g[u] = self.rhs[u]
                for p in self.neighbors(u):
                    self.update_vertex(p)
            else:
                self.processed_cells.append(u)
                self.g[u] = inf
                self.update_vertex(u)
                for p in self.neighbors(u):
                    self.update_vertex(p)
        if len(self.heap) > 4 * len(self.active) + 128:
            self.heap = [(*key, token, u) for u, (key, token) in sorted(self.active.items())]
            from heapq import heapify
            heapify(self.heap)
        return len(self.processed_cells)

    def get_path(self):
        if self.costs.get(self.start, 1) == inf or self.costs.get(self.goal, 1) == inf:
            return None
        if self.g[self.start] == inf:
            return None
        cur = self.start
        path, seen = [cur], {cur}
        while cur != self.goal:
            score, _, nxt = min((edge_cost(self.costs, cur, v) + self.g[v],
                                 manhattan(v, self.goal), v) for v in self.neighbors(cur))
            if score == inf or nxt in seen:
                return None
            cur = nxt
            path.append(cur)
            seen.add(cur)
        return path

    def plan(self):
        processed = self.compute_shortest_path()
        path = self.get_path()
        return SearchResult(path, path_cost(path, self.costs), processed,
                            self.max_frontier, list(self.processed_cells))
