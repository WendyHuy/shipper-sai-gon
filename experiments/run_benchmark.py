import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path

from ai.brains import BRAIN_NAMES
from config import Config
from core.simulation import Simulation


def write_csv(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def benchmark(config, seeds, npc_counts, brains=BRAIN_NAMES, repeats=1,
              output='results/benchmark.csv', progress=None):
    records = []
    total = len(seeds) * len(npc_counts) * len(brains) * repeats
    for npc_count in npc_counts:
        for seed in seeds:
            for brain in brains:
                for repeat in range(repeats):
                    cfg = replace(config, seed=seed, npc_count=npc_count)
                    sim = Simulation(cfg, brain)
                    while not sim.finished:
                        sim.step()
                    record = sim.summary()
                    record['repeat'] = repeat + 1
                    records.append(record)
                    if progress:
                        progress(len(records), total, record)
    baseline = {(r['seed'], r['npc_count'], r['repeat']): r['planning_ms']
                for r in records if r['brain'] == 'astar_tick'}
    for r in records:
        reference = baseline.get((r['seed'], r['npc_count'], r['repeat']), 0)
        r['planning_gain_vs_s1_pct'] = 100 * (reference - r['planning_ms']) / reference if reference > 0 else ''
    write_csv(output, records)
    metadata = {'config': asdict(config), 'seeds': seeds, 'npc_counts': npc_counts,
                'brains': list(brains), 'repeats': repeats,
                'environment': 'RandomWalker with separate RNG; independent of agent/brain',
                'timing': 'Brain.plan wall time; includes change application, search and path reconstruction; excludes rendering and sensing',
                'gain': 'Cumulative episode planning time vs S1; trajectories differ. Not same-snapshot incremental gain.',
                'stop': 'max_ticks OR all orders delivered/cancelled; use ticks field when comparing'}
    Path(output).with_suffix('.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description='Benchmark game giao hàng không giao diện.')
    parser.add_argument('--seeds', nargs='+', type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument('--npcs', nargs='+', type=int, default=[5, 10, 20, 40])
    parser.add_argument('--brains', nargs='+', choices=BRAIN_NAMES, default=list(BRAIN_NAMES))
    parser.add_argument('--ticks', type=int, default=300)
    parser.add_argument('--orders', type=int, default=5)
    parser.add_argument('--radius', type=int, default=5)
    parser.add_argument('--density', type=float, default=0.15)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--output', default='results/benchmark.csv')
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error('--repeats phải >= 1')
    config = Config(max_ticks=args.ticks, order_count=args.orders,
                    sensing_radius=args.radius, density=args.density)
    records = benchmark(config, args.seeds, args.npcs, args.brains, args.repeats, args.output,
                        lambda i, n, r: print(f"[{i}/{n}] {r['brain']}: seed={r['seed']}, NPC={r['npc_count']}, giao={r['delivered']}/{r['orders']}"))
    print(f'Đã ghi {len(records)} lượt vào {args.output}')


if __name__ == '__main__':
    main()
