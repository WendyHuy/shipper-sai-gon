from random import Random

from ai.common import neighbors4


class RandomTraffic:
    def __init__(self, rows, cols, walls, positions, seed):
        self.rows, self.cols, self.walls = rows, cols, walls
        self.positions = list(positions)
        self.rng = Random(seed + 2003)

    def step(self):
        occupied = set(self.positions)
        for i, pos in enumerate(self.positions):
            candidates = [pos] + [v for v in neighbors4(pos, self.rows, self.cols)
                                  if v not in self.walls and v not in occupied]
            nxt = self.rng.choice(candidates)
            occupied.remove(pos)
            occupied.add(nxt)
            self.positions[i] = nxt
