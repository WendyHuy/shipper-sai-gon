import argparse
import json
from pathlib import Path

from ai.brains import BRAIN_NAMES
from config import Config
from core.simulation import Simulation
from experiments.run_benchmark import write_csv


def main():
    parser = argparse.ArgumentParser(description='Shipper Sài Gòn — game giao hàng và thực nghiệm AI.')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--npcs', type=int, default=20)
    parser.add_argument('--radius', type=int, default=5)
    parser.add_argument('--orders', type=int, default=5)
    parser.add_argument('--ticks', type=int, default=300)
    parser.add_argument('--density', type=float, default=0.15)
    parser.add_argument('--brain', choices=BRAIN_NAMES, default='astar_tick')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', default='results/episode.csv')
    parser.add_argument('--screenshot', help='Chụp một frame để kiểm tra giao diện; cần Pygame.')
    parser.add_argument('--screenshot-ticks', type=int, default=70)
    args = parser.parse_args()
    config = Config(seed=args.seed, npc_count=args.npcs, sensing_radius=args.radius,
                    order_count=args.orders, max_ticks=args.ticks, density=args.density)
    if args.headless:
        sim = Simulation(config, args.brain)
        while not sim.finished:
            sim.step()
        write_csv(args.output, sim.metrics.records)
        summary = sim.summary()
        Path(args.output).with_suffix('.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        try:
            from ui.app import run_app
        except ModuleNotFoundError as exc:
            if exc.name == 'pygame':
                raise SystemExit('Chưa có pygame. Chạy: python -m pip install -r requirements.txt') from exc
            raise
        run_app(config, args.brain, args.screenshot, args.screenshot_ticks)


if __name__ == '__main__':
    main()
