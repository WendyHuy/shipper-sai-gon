import argparse
from dataclasses import replace
from math import inf
from time import perf_counter

from ai.astar import astar
from ai.common import validate_path
from ai.dstar_lite import DStarLite
from config import Config
from core.world import World
from experiments.run_benchmark import write_csv


def run(seed=42, events=10, output='results/snapshots.csv'):
    world = World(Config(seed=seed, npc_count=0, order_count=1))
    start, goal = world.start, world.orders[0].dropoff
    costs = {cell: inf for cell in world.walls}
    planner = DStarLite(world.rows, world.cols, costs, start, goal)
    records = []
    previous = None
    for event_id in range(events + 1):
        changes = []
        if event_id and previous and len(previous) > 2:
            cell = previous[len(previous) // 2]
            cost = 8 if event_id % 3 == 0 else inf
            costs[cell] = cost
            changes.append((cell, cost))
        t0 = perf_counter()
        planner.on_changes(changes)
        dstar = planner.plan()
        dstar_ms = (perf_counter() - t0) * 1000
        t0 = perf_counter()
        baseline = astar(world.rows, world.cols, costs, start, goal)
        astar_ms = (perf_counter() - t0) * 1000
        if dstar.cost != baseline.cost:
            raise AssertionError(f'Chi phí lệch tại event {event_id}')
        valid = dstar.path is None or validate_path(dstar.path, costs, start, goal, world.rows, world.cols)
        if not valid:
            raise AssertionError('Đường D* Lite không hợp lệ')
        records.append({'seed': seed, 'event': event_id, 'changed': str(changes),
                        'astar_cost': baseline.cost, 'dstar_cost': dstar.cost,
                        'astar_processed': baseline.processed, 'dstar_processed': dstar.processed,
                        'astar_ms': astar_ms, 'dstar_ms': dstar_ms,
                        'gain_pct': 100 * (astar_ms - dstar_ms) / astar_ms if astar_ms else 0,
                        'valid': valid})
        previous = dstar.path
    write_csv(output, records)
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--events', type=int, default=10)
    parser.add_argument('--output', default='results/snapshots.csv')
    args = parser.parse_args()
    rows = run(args.seed, args.events, args.output)
    print(f'{len(rows)} snapshot: chi phí A* và D* Lite khớp; đã lưu {args.output}')
