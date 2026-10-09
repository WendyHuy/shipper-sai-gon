from dataclasses import dataclass, field
from math import inf


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors4(cell, rows, cols):
    r, c = cell
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def edge_cost(costs, u, v):
    if costs.get(u, 1) == inf or costs.get(v, 1) == inf:
        return inf
    return costs.get(v, 1)


def reconstruct(parent, goal):
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]


def path_cost(path, costs):
    if path is None:
        return inf
    return sum(edge_cost(costs, u, v) for u, v in zip(path, path[1:]))


def validate_path(path, costs, start, goal, rows, cols):
    if not path or path[0] != start or path[-1] != goal:
        return False
    if any(not (0 <= r < rows and 0 <= c < cols) or costs.get((r, c), 1) == inf
           for r, c in path):
        return False
    return all(manhattan(u, v) == 1 for u, v in zip(path, path[1:]))


@dataclass
class SearchResult:
    path: list | None
    cost: float = inf
    processed: int = 0
    max_frontier: int = 0
    expanded_cells: list = field(default_factory=list)
