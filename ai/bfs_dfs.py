from collections import deque
from math import inf

from ai.common import SearchResult, neighbors4, path_cost, reconstruct


def bfs(rows, cols, costs, start, goal):
    if costs.get(start, 1) == inf or costs.get(goal, 1) == inf:
        return SearchResult(None)
    queue = deque([start])
    parent = {start: None}
    expanded = []
    peak = 1
    while queue:
        u = queue.popleft()
        expanded.append(u)
        if u == goal:
            path = reconstruct(parent, goal)
            return SearchResult(path, path_cost(path, costs), len(expanded), peak, expanded)
        for v in neighbors4(u, rows, cols):
            if v not in parent and costs.get(v, 1) < inf:
                parent[v] = u
                queue.append(v)
        peak = max(peak, len(queue))
    return SearchResult(None, inf, len(expanded), peak, expanded)
