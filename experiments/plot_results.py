import argparse
from pathlib import Path


def plot(csv_path, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.read_csv(csv_path)
    grouped = df.groupby(['npc_count', 'brain'])[['states_processed', 'planning_ms', 'on_time_rate', 'travel_cost']].mean()
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), layout='constrained')
    specs = [('states_processed', 'States processed (mean)'), ('planning_ms', 'Total planning time (ms, mean)'),
             ('on_time_rate', 'On-time delivery rate (mean)'), ('travel_cost', 'Travel cost (mean)')]
    for ax, (metric, title) in zip(axes.flat, specs):
        grouped[metric].unstack('brain').plot(kind='bar', ax=ax)
        ax.set_title(title)
        ax.set_xlabel('NPC count')
        ax.tick_params(axis='x', rotation=0)
        ax.grid(axis='y', alpha=0.2)
        ax.legend(fontsize=7)
    fig.suptitle('Shipper Sai Gon — seeded pilot benchmark; runtime varies between runs', fontsize=14)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='?', default='results/benchmark.csv')
    parser.add_argument('--output', default='results/benchmark.png')
    args = parser.parse_args()
    plot(args.csv, args.output)
