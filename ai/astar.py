from heapq import heappop, heappush
from itertools import count
from math import inf

from ai.common import SearchResult, edge_cost, manhattan, neighbors4, reconstruct


def astar(rows, cols, costs, start, goal, weight=1.0):
    if costs.get(start, 1) == inf or costs.get(goal, 1) == inf:
        return SearchResult(None)
    serial = count()
    queue = [(weight * manhattan(start, goal), 0, next(serial), start)]
    best_g = {start: 0}
    parent = {start: None}
    expanded = []
    max_frontier = 1
    while queue:
        _, g, _, u = heappop(queue)
        if g != best_g.get(u, inf):
            continue
        expanded.append(u)
        if u == goal:
            return SearchResult(reconstruct(parent, goal), g, len(expanded), max_frontier, expanded)
        for v in neighbors4(u, rows, cols):
            new_g = g + edge_cost(costs, u, v)
            if new_g < best_g.get(v, inf):
                best_g[v] = new_g
                parent[v] = u
                heappush(queue, (new_g + weight * manhattan(v, goal), new_g, next(serial), v))
        max_frontier = max(max_frontier, len(queue))
    return SearchResult(None, inf, len(expanded), max_frontier, expanded)
