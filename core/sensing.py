from math import inf

from ai.common import manhattan, neighbors4


def sense(world, pos, radius, known):
    changes = []
    visible = set()
    for r in range(max(0, pos[0] - radius), min(world.rows, pos[0] + radius + 1)):
        for c in range(max(0, pos[1] - radius), min(world.cols, pos[1] + radius + 1)):
            cell = r, c
            if manhattan(pos, cell) > radius:
                continue
            visible.add(cell)
            new_cost = world.cost_at(cell)
            if cell == pos:
                new_cost = world.terrain_cost(cell)
                if new_cost == inf:
                    new_cost = 1
            if known.get(cell, 1) != new_cost:
                known[cell] = new_cost
                changes.append((cell, new_cost))
    return changes, visible


def with_halo(world, known, visible, pos):
    costs = dict(known)
    for npc in sorted(world.traffic.positions):
        if npc not in visible:
            continue
        for cell in neighbors4(npc, world.rows, world.cols):
            if cell in visible and cell != pos and costs.get(cell, 1) < inf:
                costs[cell] = max(4, costs.get(cell, 1))
    return costs
